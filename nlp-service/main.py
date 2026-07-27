import os
import re
import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from nltk.sentiment.vader import SentimentIntensityAnalyzer
import nltk

app = FastAPI(title="Guest Pulse NLP Microservice", version="1.0.0")

# Initialize VADER Sentiment Intensity Analyzer
try:
    sia = SentimentIntensityAnalyzer()
except Exception:
    nltk.download('vader_lexicon')
    sia = SentimentIntensityAnalyzer()

# Aspect keywords configuration
ASPECT_KEYWORDS = {
    "wifi": ["wifi", "wi-fi", "internet", "connection", "router", "network", "signal", "web"],
    "food": ["food", "breakfast", "dinner", "lunch", "restaurant", "meal", "delicious", "buffet", "eat", "dining", "chef", "coffee"],
    "service": ["service", "staff", "reception", "bellboy", "employee", "waiter", "hospitality", "helpful", "friendly", "rude", "desk", "host"],
    "room": ["room", "bed", "bathroom", "shower", "aircon", "ac", "sheets", "pillow", "noise", "sleep", "suite"],
    "cleanliness": ["clean", "dirty", "dust", "spotless", "hygiene", "messy", "smell", "neat", "spotted", "filthy"],
    "price": ["price", "cost", "expensive", "value", "cheap", "worth", "affordable", "pricey", "charge", "fee"]
}

class AnalysisRequest(BaseModel):
    text: str

class AnalysisResponse(BaseModel):
    sentiment_score: float
    sentiment_label: str
    aspects: Dict[str, str]

class ResponseSuggestionRequest(BaseModel):
    text: str
    rating: int
    sentiment_score: float
    sentiment_label: str
    aspects: Dict[str, str]
    tone: Optional[str] = "professional"

class ResponseSuggestionResponse(BaseModel):
    suggestion: str

class ReviewItem(BaseModel):
    source: str
    reviewer_name: str
    rating: int
    review_text: str
    review_date: str

# Helper function to split text into sentences
def split_into_sentences(text: str) -> List[str]:
    # Simple regex sentence splitter
    sentences = re.split(r'(?<=[.!?])\s+', text)
    return [s.strip() for s in sentences if s.strip()]

def analyze_aspects(text: str) -> Dict[str, str]:
    sentences = split_into_sentences(text.lower())
    aspect_sentiments = {}
    
    for aspect, keywords in ASPECT_KEYWORDS.items():
        aspect_sentences = []
        for sentence in sentences:
            if any(keyword in sentence for keyword in keywords):
                aspect_sentences.append(sentence)
        
        if aspect_sentences:
            # Calculate average compound score for the sentences containing aspect keywords
            scores = []
            for s in aspect_sentences:
                scores.append(sia.polarity_scores(s)['compound'])
            avg_score = sum(scores) / len(scores)
            
            # Map score to label
            if avg_score >= 0.05:
                aspect_sentiments[aspect] = "positive"
            elif avg_score <= -0.05:
                aspect_sentiments[aspect] = "negative"
            else:
                aspect_sentiments[aspect] = "neutral"
                
    return aspect_sentiments

@app.post("/analyze", response_model=AnalysisResponse)
def analyze_review(payload: AnalysisRequest):
    text = payload.text
    if not text.strip():
        raise HTTPException(status_code=400, detail="Review text cannot be empty")
        
    scores = sia.polarity_scores(text)
    compound = scores['compound']
    
    # Label compound score
    if compound >= 0.05:
        label = "positive"
    elif compound <= -0.05:
        label = "negative"
    else:
        label = "neutral"
        
    aspects = analyze_aspects(text)
    
    return AnalysisResponse(
        sentiment_score=compound,
        sentiment_label=label,
        aspects=aspects
    )

@app.post("/suggest-response", response_model=ResponseSuggestionResponse)
def suggest_response(payload: ResponseSuggestionRequest):
    name_placeholder = "Valued Guest"
    tone = payload.tone.lower() if payload.tone else "professional"
    
    # Structure responses based on rules
    negatives = [k for k, v in payload.aspects.items() if v == "negative"]
    positives = [k for k, v in payload.aspects.items() if v == "positive"]
    
    formatted_positives = ", ".join(positives) if positives else ""
    formatted_negatives = " and ".join(negatives) if negatives else ""
    
    if tone == "casual":
        if payload.sentiment_label == "positive":
            greeting = f"Hey {name_placeholder}!"
            body = f"Thanks a million for sharing your thoughts! We're super happy you had a great time with us."
            if positives:
                body += f" It's so awesome that you loved our {formatted_positives}. Our crew works hard to keep things fun and comfortable."
            closing = "Can't wait to see you again soon! \n\nCheers,\nThe Guest Team"
        elif payload.sentiment_label == "negative":
            greeting = f"Hi {name_placeholder},"
            body = "Thanks for let us know about this. We're really sorry that your stay wasn't great."
            if negatives:
                body += f" We're checking on the issues with the {formatted_negatives} right away to make sure they get sorted."
            else:
                body += " We always want our guests to have a good time, and we clearly missed the mark for you."
            closing = "Hope you'll give us another shot in the future. \n\nBest,\nThe Management Team"
        else: # Neutral
            greeting = f"Hey {name_placeholder},"
            body = "Thanks for the feedback! We're glad you liked some parts of your stay"
            if positives:
                body += f", especially our {formatted_positives}"
            if negatives:
                body += f". We also hear you on the issues with the {formatted_negatives} and we'll get right on making those better"
            body += "."
            closing = "Hope to catch you again sometime! \n\nWarmly,\nFront Desk Crew"

    elif tone == "apologetic":
        if payload.sentiment_label == "positive":
            greeting = f"Dear {name_placeholder},"
            body = f"Thank you very much for your wonderful review. While we are delighted that you enjoyed your stay"
            if positives:
                body += f" and appreciated our {formatted_positives}"
            body += ", please accept our apologies for any minor issues you may have encountered. We constantly strive to offer a flawless experience."
            closing = "We hope to exceed your expectations on your next visit.\n\nWarm regards,\nHotel Management"
        elif payload.sentiment_label == "negative":
            greeting = f"Dear {name_placeholder},"
            body = "Please accept our deepest and most sincere apologies for your experience. We are truly sorry that we fell short of your expectations during your stay."
            if negatives:
                body += f" We take the problems you experienced with the {formatted_negatives} very seriously, and we have launched an immediate operational review to rectify these issues."
            else:
                body += " We pride ourselves on our quality of hospitality, and it is clear we failed to deliver that to you."
            closing = "We would welcome the opportunity to host you again and demonstrate our commitment to your comfort.\n\nWith our sincere apologies,\nGuest Relations Director"
        else: # Neutral
            greeting = f"Dear {name_placeholder},"
            body = "Thank you for sharing your feedback. We apologize that your visit was merely average and fell short of being fully satisfactory."
            if negatives:
                body += f" We have noted your concerns regarding the {formatted_negatives} and have scheduled maintenance updates to address them."
            closing = "We hope you will allow us to prove our hospitality standards to you in the future.\n\nSincerely,\nFront Office Manager"

    elif tone == "thankful":
        if payload.sentiment_label == "positive":
            greeting = f"Dear {name_placeholder},"
            body = "We cannot thank you enough for this absolutely amazing review! You have truly brightened our day."
            if positives:
                body += f" We are incredibly grateful that you enjoyed our {formatted_positives}, and we'll be sure to pass your praise along to the whole team!"
            closing = "We are so looking forward to welcoming you back for another perfect stay!\n\nWith our sincerest thanks,\nThe Entire Hotel Team"
        elif payload.sentiment_label == "negative":
            greeting = f"Dear {name_placeholder},"
            body = "Thank you very much for taking the time to share this critical feedback. We are highly grateful for your honesty, as it is the only way we can learn and grow."
            if negatives:
                body += f" We are especially thankful for you bringing the issues with the {formatted_negatives} to our attention so we can address them immediately."
            closing = "We appreciate your valuable feedback and hope to welcome you again.\n\nWith gratitude,\nQuality Assurance Team"
        else: # Neutral
            greeting = f"Dear {name_placeholder},"
            body = "Thank you so much for your balanced and thoughtful review. We are truly grateful for both your kind words and your constructive criticisms."
            parts = []
            if positives:
                parts.append(f"our {formatted_positives} (which we are glad you enjoyed)")
            if negatives:
                parts.append(f"the {formatted_negatives} (which we will work hard to improve)")
            if parts:
                body += " Your notes regarding " + " and ".join(parts) + " are extremely helpful."
            closing = "Thank you for helping us improve our guest experiences.\n\nWarmest thanks,\nGuest Experience Team"

    else: # Professional (Default)
        if payload.sentiment_label == "positive":
            greeting = f"Dear {name_placeholder},"
            body = "Thank you so much for taking the time to share your feedback! We are thrilled to hear you had a wonderful stay with us."
            if positives:
                body += f" It is especially rewarding to know that you enjoyed our {formatted_positives}. Our team strives to deliver the best experience, and your kind words mean a lot to us."
            else:
                body += " We are dedicated to providing excellent hospitality, and we are glad that we succeeded during your visit."
            closing = "We look forward to welcoming you back in the near future!\n\nWarm regards,\nHotel Management"
        elif payload.sentiment_label == "negative":
            greeting = f"Dear {name_placeholder},"
            body = "Thank you for sharing your review. We sincerely apologize that your recent stay did not meet your expectations."
            if negatives:
                body += f" We take your concerns regarding the {formatted_negatives} very seriously. We have shared this feedback with our departments to address these shortcomings immediately."
            else:
                body += " We are deeply sorry for any inconvenience caused during your stay. Your comfort and satisfaction are our top priorities, and we will review our services to make the necessary improvements."
            closing = "We hope you will give us another opportunity to provide you with the high-quality experience you deserve.\n\nSincerely,\nGuest Relations Team"
        else: # Neutral
            greeting = f"Dear {name_placeholder},"
            body = "Thank you for posting your feedback. We appreciate your comments as they help us improve."
            body_parts = []
            if positives:
                body_parts.append(f"We're glad to hear you appreciated our {formatted_positives}")
            if negatives:
                body_parts.append(f"but we have also noted your concern regarding the {formatted_negatives} and will work to improve it")
            if body_parts:
                body += " " + ", ".join(body_parts) + "."
            else:
                body += " We have shared your observations with our staff to ensure we maintain our high standards of hospitality."
            closing = "We hope to welcome you again to show you our progress.\n\nBest regards,\nFront Office Team"
        
    response_draft = f"{greeting}\n\n{body}\n\n{closing}"
    return ResponseSuggestionResponse(suggestion=response_draft)

# Comprehensive review database for scraping simulation
POOL_REVIEWS = [
    {
        "source": "google",
        "reviewer_name": "Sarah Miller",
        "rating": 5,
        "review_text": "Had an incredible weekend stay. The breakfast buffet was absolutely delicious with so many fresh options! The service from the front desk staff was top-notch. Clean, comfy rooms.",
        "days_ago": 1
    },
    {
        "source": "booking",
        "reviewer_name": "Michael Chen",
        "rating": 3,
        "review_text": "The location is fantastic, very central. However, the wifi connection in our room was extremely slow and dropped constantly, making it hard to work. The bed was comfortable though.",
        "days_ago": 2
    },
    {
        "source": "tripadvisor",
        "reviewer_name": "Emma Watson",
        "rating": 2,
        "review_text": "Very disappointed with our stay. The room was not properly cleaned; there was thick dust on the nightstands and the bathroom smelled damp. Also, the service at the restaurant was very slow.",
        "days_ago": 3
    },
    {
        "source": "google",
        "reviewer_name": "David Rossi",
        "rating": 5,
        "review_text": "Best boutique hotel in the city! Cleanliness was flawless. The staff went above and beyond to suggest local sights. Wi-Fi was fast and perfect for video calls.",
        "days_ago": 4
    },
    {
        "source": "booking",
        "reviewer_name": "Jessica Taylor",
        "rating": 4,
        "review_text": "Very nice room with a beautiful city view. Good price for the location. Breakfast was decent but the dining area was a bit messy. Would stay here again.",
        "days_ago": 5
    },
    {
        "source": "tripadvisor",
        "reviewer_name": "Liam Davies",
        "rating": 1,
        "review_text": "Avoid this place! The rooms are so noisy, you can hear traffic and neighbors all night. AC unit was broken and blew hot air. Staff did not care when we complained. Too expensive for what you get.",
        "days_ago": 6
    },
    {
        "source": "google",
        "reviewer_name": "Sofia Hansen",
        "rating": 4,
        "review_text": "Excellent service from start to finish. The room was clean, spacious, and modern. My only complaint is that the price of parking is too expensive.",
        "days_ago": 8
    },
    {
        "source": "booking",
        "reviewer_name": "Robert Kowalski",
        "rating": 5,
        "review_text": "Exceptional hospitality! The staff treated us like royalty. Delicious dinner at the restaurant. Rooms are spotless and quiet. Highly recommended!",
        "days_ago": 10
    },
    {
        "source": "tripadvisor",
        "reviewer_name": "Charlotte Dubois",
        "rating": 3,
        "review_text": "Average stay. The rooms are okay but look a bit outdated. WiFi was decent in the lobby but weak in the room. The price is reasonable for the location.",
        "days_ago": 12
    },
    {
        "source": "google",
        "reviewer_name": "Niels Berg",
        "rating": 2,
        "review_text": "The reception staff was quite rude when we checked in. The bed sheets had stains on them. Food was alright but way overpriced.",
        "days_ago": 15
    },
    {
        "source": "booking",
        "reviewer_name": "Elena Popova",
        "rating": 5,
        "review_text": "Absolutely spotless! The housekeeping staff does an amazing job. Fast internet connection, comfortable bed, and very quiet. Will definitely return.",
        "days_ago": 18
    },
    {
        "source": "tripadvisor",
        "reviewer_name": "Marcus Aurelius",
        "rating": 4,
        "review_text": "Nice boutique vibe. The pool and lobby are beautiful. Breakfast was delicious. Service was helpful, but check-in was a bit slow.",
        "days_ago": 22
    }
]

@app.get("/scrape", response_model=List[ReviewItem])
def scrape_reviews(count: int = 5, sources: Optional[str] = None):
    # Simulates review scraping by pulling a randomized subset of reviews
    # with dates adjusted dynamically based on the current system time.
    pool = POOL_REVIEWS
    if sources:
        allowed_sources = [s.strip().lower() for s in sources.split(",") if s.strip()]
        if allowed_sources:
            pool = [r for r in POOL_REVIEWS if r["source"].lower() in allowed_sources]
            
    if not pool:
        return []

    selected_reviews = random.sample(pool, min(count, len(pool)))
    
    results = []
    base_date = datetime.now()
    
    for review in selected_reviews:
        # Subtract randomized days to make review dates look natural
        review_date = (base_date - timedelta(days=review["days_ago"] + random.randint(0, 3))).strftime("%Y-%m-%d")
        results.append(ReviewItem(
            source=review["source"],
            reviewer_name=review["reviewer_name"],
            rating=review["rating"],
            review_text=review["review_text"],
            review_date=review_date
        ))
        
    return results

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8001)
