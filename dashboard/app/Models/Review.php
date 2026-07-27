<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Factories\HasFactory;
use Illuminate\Database\Eloquent\Model;

class Review extends Model
{
    use HasFactory;

    protected $fillable = [
        'source',
        'reviewer_name',
        'rating',
        'review_text',
        'sentiment_score',
        'sentiment_label',
        'aspect_sentiments',
        'review_date',
        'response_suggested',
        'response_tone',
        'reply_text',
        'response_status',
    ];

    protected $casts = [
        'aspect_sentiments' => 'array',
        'sentiment_score' => 'float',
        'rating' => 'integer',
        'review_date' => 'date:Y-m-d',
    ];
}
