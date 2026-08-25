import os
import re
from typing import List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from groq import Groq
from geopy.geocoders import Nominatim

app = FastAPI(title="AI Travel Planner API")

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
    interests: List[str] = []
    must_visit: Optional[str] = ""

def get_coordinates(location_name: str):
    try:
        geolocator = Nominatim(user_agent="travel_planner_vercel_student_project_v10")
        location = geolocator.geocode(location_name, timeout=10)
        if location:
            return [location.latitude, location.longitude]
    except Exception:
        pass
    return None

@app.get("/api/health")
def health_check():
    return {"status": "ok", "service": "AI Travel Planner API"}

@app.post("/api/generate")
def generate_itinerary(req: TripRequest):
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise HTTPException(
            status_code=500,
            detail="GROQ_API_KEY environment variable is not configured on Vercel."
        )

    client = Groq(api_key=api_key)

    budget_text = f"{req.budget_level} Tier"
    if req.budget_amount:
        budget_text += f" with a strict cap of {req.budget_amount}"

    must_visit_instruction = ""
    if req.must_visit:
        must_visit_instruction = f"CRITICAL: You MUST include a visit to '{req.must_visit}' in the itinerary."

    interests_string = ", ".join(req.interests) if req.interests else "General sightseeing, culture, local food"

    prompt = f"""
    Act as an expert local travel guide. Create a {req.days}-day trip to {req.destination} for a student. 
    Budget Constraints: {budget_text}.
    Specific Interests: {interests_string}. 
    {must_visit_instruction}
    
    Structure the response strictly as follows (Use Markdown):
    1. A Catchy Title (H2)
    2. Budget Breakdown (Bulleted list)
    3. Day-by-Day Itinerary (Morning, Afternoon, Evening sections)
    4. At the very end, list 3 exact landmarks to pin on a map, labeled EXACTLY like this:
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
        raw_landmarks = [l.strip() for l in parts[1].strip().split(",") if l.strip()]
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
        "markers": markers
    }
