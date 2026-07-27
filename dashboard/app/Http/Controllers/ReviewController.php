<?php

namespace App\Http\Controllers;

use App\Models\Review;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Http;
use Illuminate\Support\Facades\Log;

class ReviewController extends Controller
{
    private string $nlpServiceUrl = 'http://127.0.0.1:8001';

    /**
     * Display the dashboard page.
     */
    public function index()
    {
        return view('dashboard');
    }

    /**
     * Get reviews list with optional filters.
     */
    public function getReviews(Request $request)
    {
        $query = Review::query();

        // Filter by source
        if ($request->has('source') && !empty($request->source)) {
            $query->where('source', $request->source);
        }

        // Filter by sentiment label
        if ($request->has('sentiment') && !empty($request->sentiment)) {
            $query->where('sentiment_label', $request->sentiment);
        }

        // Filter by rating
        if ($request->has('rating') && !empty($request->rating)) {
            $query->where('rating', $request->rating);
        }

        // Search in text or reviewer name
        if ($request->has('search') && !empty($request->search)) {
            $search = $request->search;
            $query->where(function ($q) use ($search) {
                $q->where('review_text', 'like', "%{$search}%")
                  ->orWhere('reviewer_name', 'like', "%{$search}%");
            });
        }

        $reviews = $query->orderBy('review_date', 'desc')->get();

        return response()->json($reviews);
    }

    /**
     * Get aggregate statistics for KPIs and charts.
     */
    public function getStats()
    {
        $totalReviews = Review::count();
        if ($totalReviews === 0) {
            return response()->json([
                'kpis' => [
                    'avg_rating' => 0,
                    'avg_sentiment' => 0,
                    'total_reviews' => 0,
                    'response_rate' => 0
                ],
                'charts' => [
                    'sources' => [],
                    'sentiment_history' => [],
                    'aspects' => []
                ]
            ]);
        }

        $avgRating = round(Review::avg('rating'), 1);
        $avgSentiment = round(Review::avg('sentiment_score'), 2);
        
        $repliedCount = Review::where('response_status', 'replied')->count();
        $responseRate = round(($repliedCount / $totalReviews) * 100, 1);

        // Sources count
        $sources = Review::select('source', \DB::raw('count(*) as count'))
            ->groupBy('source')
            ->get()
            ->pluck('count', 'source')
            ->toArray();

        // Sentiment over time (grouped by date)
        $sentimentHistory = Review::select('review_date', \DB::raw('AVG(sentiment_score) as avg_score'), \DB::raw('count(*) as count'))
            ->groupBy('review_date')
            ->orderBy('review_date', 'asc')
            ->get()
            ->map(function ($item) {
                return [
                    'date' => $item->review_date->format('Y-m-d'),
                    'score' => round($item->avg_score, 2),
                    'count' => $item->count
                ];
            })
            ->toArray();

        // Aspect breakdown
        $aspectCounts = [
            'wifi' => ['positive' => 0, 'negative' => 0, 'neutral' => 0],
            'food' => ['positive' => 0, 'negative' => 0, 'neutral' => 0],
            'service' => ['positive' => 0, 'negative' => 0, 'neutral' => 0],
            'room' => ['positive' => 0, 'negative' => 0, 'neutral' => 0],
            'cleanliness' => ['positive' => 0, 'negative' => 0, 'neutral' => 0],
            'price' => ['positive' => 0, 'negative' => 0, 'neutral' => 0],
        ];

        $reviewsWithAspects = Review::whereNotNull('aspect_sentiments')->get();
        foreach ($reviewsWithAspects as $review) {
            $aspects = $review->aspect_sentiments;
            if (is_array($aspects)) {
                foreach ($aspects as $aspect => $sentiment) {
                    if (isset($aspectCounts[$aspect]) && isset($aspectCounts[$aspect][$sentiment])) {
                        $aspectCounts[$aspect][$sentiment]++;
                    }
                }
            }
        }

        return response()->json([
            'kpis' => [
                'avg_rating' => $avgRating,
                'avg_sentiment' => $avgSentiment,
                'total_reviews' => $totalReviews,
                'response_rate' => $responseRate
            ],
            'charts' => [
                'sources' => $sources,
                'sentiment_history' => $sentimentHistory,
                'aspects' => $aspectCounts
            ]
        ]);
    }

    public function fetchNewReviews(Request $request)
    {
        try {
            $sources = $request->input('sources');
            
            // Call the python scraping microservice
            $response = Http::timeout(10)->get("{$this->nlpServiceUrl}/scrape", [
                'count' => 6,
                'sources' => $sources
            ]);

            if ($response->failed()) {
                return response()->json(['error' => 'Failed to reach scraping microservice'], 502);
            }

            $scrapedReviews = $response->json();
            $newCount = 0;

            foreach ($scrapedReviews as $rawReview) {
                // Check if duplicate review exists
                $exists = Review::where('reviewer_name', $rawReview['reviewer_name'])
                    ->where('review_date', $rawReview['review_date'])
                    ->where('source', $rawReview['source'])
                    ->exists();

                if ($exists) {
                    continue;
                }

                // Call NLP sentiment analysis API
                $analysisResponse = Http::post("{$this->nlpServiceUrl}/analyze", [
                    'text' => $rawReview['review_text']
                ]);

                if ($analysisResponse->successful()) {
                    $analysis = $analysisResponse->json();
                    $sentimentScore = $analysis['sentiment_score'];
                    $sentimentLabel = $analysis['sentiment_label'];
                    $aspects = $analysis['aspects'];
                } else {
                    // Fallback local analyzer if FastAPI fails or returns error
                    $sentimentScore = $rawReview['rating'] >= 4 ? 0.6 : ($rawReview['rating'] <= 2 ? -0.6 : 0.0);
                    $sentimentLabel = $rawReview['rating'] >= 4 ? 'positive' : ($rawReview['rating'] <= 2 ? 'negative' : 'neutral');
                    $aspects = [];
                }

                // Create the review record
                Review::create([
                    'source' => $rawReview['source'],
                    'reviewer_name' => $rawReview['reviewer_name'],
                    'rating' => $rawReview['rating'],
                    'review_text' => $rawReview['review_text'],
                    'sentiment_score' => $sentimentScore,
                    'sentiment_label' => $sentimentLabel,
                    'aspect_sentiments' => $aspects,
                    'review_date' => $rawReview['review_date'],
                    'response_status' => 'pending'
                ]);

                $newCount++;
            }

            return response()->json([
                'success' => true,
                'message' => "Successfully processed reviews. {$newCount} new reviews imported.",
                'new_count' => $newCount
            ]);

        } catch (\Exception $e) {
            Log::error('Scrape error: ' . $e->getMessage());
            return response()->json([
                'error' => 'An error occurred during review ingestion: ' . $e->getMessage()
            ], 500);
        }
    }

    /**
     * Get suggested AI response for a review.
     */
    public function generateSuggestedResponse(Request $request, $id)
    {
        $review = Review::findOrFail($id);
        $tone = $request->input('tone', 'professional');

        try {
            $response = Http::post("{$this->nlpServiceUrl}/suggest-response", [
                'text' => $review->review_text,
                'rating' => $review->rating,
                'sentiment_score' => $review->sentiment_score,
                'sentiment_label' => $review->sentiment_label,
                'aspects' => $review->aspect_sentiments ?? (object)[],
                'tone' => $tone
            ]);

            if ($response->successful()) {
                $suggestion = $response->json()['suggestion'];
                
                // Replace general name placeholder with real name
                $suggestion = str_replace("Valued Guest", $review->reviewer_name, $suggestion);

                $review->update([
                    'response_suggested' => $suggestion
                ]);

                return response()->json([
                    'success' => true,
                    'suggestion' => $suggestion
                ]);
            }

            return response()->json(['error' => 'Failed to generate response suggestion'], 502);

        } catch (\Exception $e) {
            Log::error('Response generation error: ' . $e->getMessage());
            return response()->json(['error' => 'NLP service offline or error occurred'], 500);
        }
    }

    /**
     * Save the replies.
     */
    public function saveReply(Request $request, $id)
    {
        $request->validate([
            'reply_text' => 'required|string'
        ]);

        $review = Review::findOrFail($id);
        $review->update([
            'reply_text' => $request->reply_text,
            'response_status' => 'replied'
        ]);

        return response()->json(['success' => true]);
    }

    /**
     * Ignore a review.
     */
    public function ignoreReview($id)
    {
        $review = Review::findOrFail($id);
        $review->update([
            'response_status' => 'ignored'
        ]);

        return response()->json(['success' => true]);
    }
}
