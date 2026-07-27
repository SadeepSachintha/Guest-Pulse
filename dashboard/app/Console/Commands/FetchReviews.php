<?php

namespace App\Console\Commands;

use Illuminate\Console\Command;
use App\Models\Review;
use Illuminate\Support\Facades\Http;
use Illuminate\Support\Facades\Log;

class FetchReviews extends Command
{
    /**
     * The name and signature of the console command.
     *
     * @var string
     */
    protected $signature = 'reviews:fetch {--sources= : Comma-separated list of active sources}';

    /**
     * The console command description.
     *
     * @var string
     */
    protected $description = 'Ingest and analyze new guest reviews from Google, Booking.com, and TripAdvisor';

    /**
     * Execute the console command.
     */
    public function handle()
    {
        $this->info('Starting scheduled review scraping...');
        $nlpServiceUrl = 'http://127.0.0.1:8001';
        $sources = $this->option('sources') ?? 'google,booking,tripadvisor';

        try {
            $response = Http::timeout(15)->get("{$nlpServiceUrl}/scrape", [
                'count' => 5,
                'sources' => $sources
            ]);

            if ($response->failed()) {
                $this->error('Failed to reach scraping microservice');
                return 1;
            }

            $scrapedReviews = $response->json();
            $newCount = 0;

            foreach ($scrapedReviews as $rawReview) {
                $exists = Review::where('reviewer_name', $rawReview['reviewer_name'])
                    ->where('review_date', $rawReview['review_date'])
                    ->where('source', $rawReview['source'])
                    ->exists();

                if ($exists) {
                    continue;
                }

                $analysisResponse = Http::post("{$nlpServiceUrl}/analyze", [
                    'text' => $rawReview['review_text']
                ]);

                if ($analysisResponse->successful()) {
                    $analysis = $analysisResponse->json();
                    $sentimentScore = $analysis['sentiment_score'];
                    $sentimentLabel = $analysis['sentiment_label'];
                    $aspects = $analysis['aspects'];
                } else {
                    $sentimentScore = $rawReview['rating'] >= 4 ? 0.6 : ($rawReview['rating'] <= 2 ? -0.6 : 0.0);
                    $sentimentLabel = $rawReview['rating'] >= 4 ? 'positive' : ($rawReview['rating'] <= 2 ? 'negative' : 'neutral');
                    $aspects = [];
                }

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

                if ($sentimentScore <= -0.5) {
                    Log::warning("CRITICAL REPUTATION ESCALATION: Highly negative review received from {$rawReview['reviewer_name']} on {$rawReview['source']}. Rating: {$rawReview['rating']}. Sentiment Score: {$sentimentScore}. Review: \"{$rawReview['review_text']}\"");
                }

                $newCount++;
            }

            $this->info("Completed! Processed reviews: {$newCount} new items imported.");
            return 0;

        } catch (\Exception $e) {
            $this->error('Error during scraping command: ' . $e->getMessage());
            Log::error('Command Scraping error: ' . $e->getMessage());
            return 1;
        }
    }
}
