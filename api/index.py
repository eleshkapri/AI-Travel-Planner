import os
import re
from typing import List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from groq import Groq
from geopy.geocoders import Nominatim

app = FastAPI(title="AI Travel Planner API", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class TripRequest(BaseModel):
    destination: str
    days: int = 3
    budget_level: str = "Student (Low)"
    budget_amount: Optional[str] = ""
    currency: Optional[str] = "USD"
    interests: List[str] = []
    must_visit: Optional[str] = ""
    travel_pace: Optional[str] = "Balanced"
    accommodation_style: Optional[str] = "Hostel / Backpacker"

def get_coordinates(location_name: str):
    try:
        geolocator = Nominatim(user_agent="travel_planner_v2_modern_web_app")
        location = geolocator.geocode(location_name, timeout=10)
        if location:
            return [location.latitude, location.longitude]
    except Exception:
        pass
    return None

@app.get("/api/health")
def health_check():
    return {
        "status": "ok",
        "service": "AI Travel Planner API",
        "version": "2.0.0",
        "supported_models": ["openai/gpt-oss-120b", "openai/gpt-oss-20b", "llama-3.1-8b-instant", "qwen/qwen3.6-27b"]
    }

@app.post("/api/generate")
def generate_itinerary(req: TripRequest):
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise HTTPException(
            status_code=500,
            detail="GROQ_API_KEY environment variable is not configured on Vercel."
        )

    client = Groq(api_key=api_key)

    curr = req.currency or "USD"
    budget_text = f"{req.budget_level} Tier (in {curr})"
    if req.budget_amount:
        budget_text += f" with a strict cap of {req.budget_amount} {curr}"

    must_visit_instruction = ""
    if req.must_visit:
        must_visit_instruction = f"CRITICAL REQUIREMENT: You MUST feature a dedicated visit to '{req.must_visit}' in the itinerary."

    interests_string = ", ".join(req.interests) if req.interests else "Local culture, budget hidden gems, street food, sightseeing"
    pace_text = f"Pace: {req.travel_pace or 'Balanced'}. Accommodation: {req.accommodation_style or 'Hostel'}."

    prompt = f"""
    You are an award-winning local travel guide specializing in epic, student-friendly, budget adventures.
    Create a detailed, high-energy {req.days}-day trip itinerary to {req.destination}.

    Travel Parameters:
    - Destination: {req.destination}
    - Duration: {req.days} Days
    - Budget Level: {budget_text}
    - Specific Interests: {interests_string}
    - {pace_text}
    - {must_visit_instruction}

    Structure your response strictly in clean Markdown as follows:
    # 🌍 [Catchy Trip Title & Emoji]
    
    ## 💰 Estimated Student Budget Breakdown ({curr})
    - 🏨 **Accommodation ({req.accommodation_style or 'Hostel'}):** [Estimated cost per night & total]
    - 🍜 **Food & Street Eats:** [Daily & total food estimate]
    - 🚇 **Local Transport:** [Passes/Subway/Bus estimates]
    - 🎟️ **Activities & Entry Fees:** [Cost estimates for attractions]
    - 💡 **Student Savings Tip:** [1 high-impact money-saving hack]

    ## 🗓️ Day-by-Day Itinerary

    ### Day 1: [Day 1 Theme/Title]
    - ☀️ **Morning:** [Actionable morning activity + budget tip]
    - 🌤️ **Afternoon:** [Actionable afternoon activity + food spot recommendation]
    - 🌙 **Evening:** [Evening vibes, sunset spot, or student nightlife]

    (Repeat detailed ### Day X format for all {req.days} days)

    ## 🎒 Essential Student Tips
    - 3 practical tips for safety, SIM cards, or student discounts in {req.destination}.

    LANDMARKS: Place 1, Place 2, Place 3
    """

    models_to_try = [
        "openai/gpt-oss-120b",
        "openai/gpt-oss-20b",
        "llama-3.1-8b-instant",
        "qwen/qwen3.6-27b",
    ]

    response_text = None
    last_error = None

    for model_name in models_to_try:
        try:
            completion = client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model=model_name,
            )
            response_text = completion.choices[0].message.content
            if response_text:
                break
        except Exception as e:
            last_error = str(e)
            continue

    if not response_text:
        raise HTTPException(status_code=500, detail=f"AI Generation failed: {last_error}")

    # Parse landmarks and itinerary
    raw_landmarks = []
    if "LANDMARKS:" in response_text:
        parts = response_text.split("LANDMARKS:")
        itinerary = parts[0].strip()
        raw_landmarks = [l.strip().rstrip('.') for l in parts[1].strip().split(",") if l.strip()]
    else:
        itinerary = response_text.strip()
        raw_landmarks = [req.destination]

    # Geocode destination & landmarks
    dest_coords = get_coordinates(req.destination)
    markers = []

    if dest_coords:
        markers.append({
            "name": f"Destination: {req.destination}",
            "type": "destination",
            "coords": dest_coords
        })

    if req.must_visit:
        mv_coords = get_coordinates(f"{req.must_visit}, {req.destination}")
        if mv_coords:
            markers.append({
                "name": f"Must Visit: {req.must_visit}",
                "type": "must_visit",
                "coords": mv_coords
            })

    for landmark in raw_landmarks:
        l_coords = get_coordinates(f"{landmark}, {req.destination}")
        if l_coords:
            markers.append({
                "name": landmark,
                "type": "landmark",
                "coords": l_coords
            })

    return {
        "itinerary": itinerary,
        "landmarks": raw_landmarks,
        "destination_coords": dest_coords,
        "markers": markers,
        "trip_summary": {
            "destination": req.destination,
            "days": req.days,
            "budget_level": req.budget_level,
            "currency": curr,
            "interests": req.interests
        }
    }
