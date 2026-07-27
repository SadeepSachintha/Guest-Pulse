<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    /**
     * Run the migrations.
     */
    public function up(): void
    {
        Schema::create('reviews', function (Blueprint $table) {
            $table->id();
            $table->string('source'); // google, booking, tripadvisor
            $table->string('reviewer_name');
            $table->integer('rating');
            $table->text('review_text');
            $table->float('sentiment_score'); // compound score between -1.0 and 1.0
            $table->string('sentiment_label'); // positive, neutral, negative
            $table->json('aspect_sentiments')->nullable(); // JSON of parsed aspects
            $table->date('review_date');
            $table->text('response_suggested')->nullable();
            $table->text('reply_text')->nullable();
            $table->string('response_status')->default('pending'); // pending, replied, ignored
            $table->timestamps();
        });
    }

    /**
     * Reverse the migrations.
     */
    public function down(): void
    {
        Schema::dropIfExists('reviews');
    }
};
