<?php

use Illuminate\Support\Facades\Route;
use App\Http\Controllers\ReviewController;

Route::get('/', [ReviewController::class, 'index']);

Route::prefix('api')->group(function () {
    Route::get('/reviews', [ReviewController::class, 'getReviews']);
    Route::get('/stats', [ReviewController::class, 'getStats']);
    Route::post('/reviews/fetch', [ReviewController::class, 'fetchNewReviews']);
    Route::post('/reviews/{id}/suggest-response', [ReviewController::class, 'generateSuggestedResponse']);
    Route::post('/reviews/{id}/reply', [ReviewController::class, 'saveReply']);
    Route::post('/reviews/{id}/ignore', [ReviewController::class, 'ignoreReview']);
});
