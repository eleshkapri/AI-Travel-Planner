import os
from typing import List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from groq import Groq
from geopy.geocoders import Nominatim

# Top-level FastAPI application instance required by Vercel
app = FastAPI(
    title="RoamAI • AI Student Travel Planner",
    description="Next-Gen 3D Modern Student Travel Planner powered by Groq AI",
    version="2.0.0"
)

# Enable CORS for seamless client-server interaction
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
        geolocator = Nominatim(user_agent="roamai_travel_architect_v2")
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
        "service": "RoamAI FastAPI Backend",
        "version": "2.0.0",
        "models": ["openai/gpt-oss-120b", "openai/gpt-oss-20b", "llama-3.1-8b-instant", "qwen/qwen3.6-27b"]
    }

@app.post("/api/generate")
def generate_itinerary(req: TripRequest):
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise HTTPException(
            status_code=500,
            detail="GROQ_API_KEY environment variable is not configured in Vercel settings."
        )

    client = Groq(api_key=api_key)

    curr = req.currency or "USD"
    budget_text = f"{req.budget_level} Tier ({curr})"
    if req.budget_amount:
        budget_text += f" with strict limit of {req.budget_amount} {curr}"

    must_visit_instruction = ""
    if req.must_visit:
        must_visit_instruction = f"CRITICAL: You MUST feature a dedicated visit to '{req.must_visit}' in the itinerary."

    interests_string = ", ".join(req.interests) if req.interests else "Local street food, culture, secret budget spots"
    pace_text = f"Pace: {req.travel_pace or 'Balanced'}. Accommodation: {req.accommodation_style or 'Hostel'}."

    prompt = f"""
    You are an award-winning local travel architect specializing in epic, student-friendly, budget adventures.
    Create a detailed, high-energy {req.days}-day trip itinerary to {req.destination}.

    Travel Parameters:
    - Destination: {req.destination}
    - Duration: {req.days} Days
    - Budget: {budget_text}
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

    ### Day 1: [Day 1 Theme]
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

    raw_landmarks = []
    if "LANDMARKS:" in response_text:
        parts = response_text.split("LANDMARKS:")
        itinerary = parts[0].strip()
        raw_landmarks = [l.strip().rstrip('.') for l in parts[1].strip().split(",") if l.strip()]
    else:
        itinerary = response_text.strip()
        raw_landmarks = [req.destination]

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

# ========================================================
# 3D MODERN MULTI-PAGE FRONTEND EMBEDDED IN PYTHON
# ========================================================
HTML_CONTENT = """<!DOCTYPE html>
<html lang="en" class="scroll-smooth">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>RoamAI • Next-Gen AI Student Travel Planner</title>
  <link rel="icon" href="https://cdn-icons-png.flaticon.com/512/921/921490.png" />

  <!-- Google Fonts -->
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">

  <!-- Tailwind CSS -->
  <script src="https://cdn.tailwindcss.com"></script>
  <script>
    tailwind.config = {
      darkMode: 'class',
      theme: {
        extend: {
          fontFamily: { sans: ['"Plus Jakarta Sans"', 'sans-serif'] },
          colors: {
            spaceDark: '#0B0F19',
            cardDark: '#121826',
            cardBorder: 'rgba(255, 255, 255, 0.08)',
            coralPrimary: '#FF5E36',
            amberAccent: '#FFA000',
            cyanAccent: '#06B6D4',
            emeraldAccent: '#10B981',
            purpleAccent: '#8B5CF6',
          }
        }
      }
    }
  </script>

  <!-- Leaflet CSS & JS -->
  <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" crossorigin="" />
  <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js" crossorigin=""></script>

  <!-- Marked.js (Markdown parser) -->
  <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>

  <!-- html2pdf for PDF export -->
  <script src="https://cdnjs.cloudflare.com/ajax/libs/html2pdf.js/0.10.1/html2pdf.bundle.min.js"></script>

  <!-- Vanilla Tilt (3D Card Physics) -->
  <script src="https://cdnjs.cloudflare.com/ajax/libs/vanilla-tilt/1.8.1/vanilla-tilt.min.js"></script>

  <style>
    body {
      background-color: #0B0F19;
      color: #F3F4F6;
      font-family: 'Plus Jakarta Sans', sans-serif;
      overflow-x: hidden;
    }
    .bg-mesh {
      position: fixed;
      top: 0; left: 0; width: 100vw; height: 100vh;
      z-index: -1; pointer-events: none;
      background: 
        radial-gradient(circle at 15% 15%, rgba(255, 94, 54, 0.14) 0%, transparent 45%),
        radial-gradient(circle at 85% 25%, rgba(6, 182, 212, 0.12) 0%, transparent 45%),
        radial-gradient(circle at 50% 85%, rgba(139, 92, 246, 0.12) 0%, transparent 50%);
    }
    .glass-card {
      background: rgba(18, 24, 38, 0.8);
      backdrop-filter: blur(16px);
      border: 1px solid rgba(255, 255, 255, 0.09);
      box-shadow: 0 10px 30px rgba(0, 0, 0, 0.4);
      transition: all 0.3s ease;
    }
    .glass-card:hover {
      border-color: rgba(255, 94, 54, 0.35);
    }
    .btn-gradient {
      background: linear-gradient(135deg, #FF5E36 0%, #FFA000 100%);
      color: #FFFFFF;
      font-weight: 700;
      transition: all 0.3s ease;
      box-shadow: 0 4px 20px rgba(255, 94, 54, 0.35);
    }
    .btn-gradient:hover {
      transform: translateY(-2px) scale(1.01);
      box-shadow: 0 8px 25px rgba(255, 94, 54, 0.55);
    }
    .btn-secondary {
      background: rgba(255, 255, 255, 0.05);
      border: 1px solid rgba(255, 255, 255, 0.12);
      color: #E5E7EB;
      transition: all 0.2s ease;
    }
    .btn-secondary:hover {
      background: rgba(255, 255, 255, 0.1);
      border-color: rgba(255, 255, 255, 0.25);
      color: #FFFFFF;
    }
    .nav-tab.active {
      color: #FF5E36;
      font-weight: 700;
      position: relative;
    }
    .nav-tab.active::after {
      content: '';
      position: absolute;
      bottom: -6px; left: 15%; width: 70%; height: 3px;
      background: linear-gradient(90deg, #FF5E36, #FFA000);
      border-radius: 9999px;
      box-shadow: 0 0 10px #FF5E36;
    }
    .chip-tag {
      cursor: pointer;
      user-select: none;
      transition: all 0.2s ease;
      background: rgba(255, 255, 255, 0.04);
      border: 1px solid rgba(255, 255, 255, 0.1);
    }
    .chip-tag.active {
      background: linear-gradient(135deg, rgba(255, 94, 54, 0.2), rgba(255, 160, 0, 0.2));
      border-color: #FF5E36;
      color: #FFA000;
      font-weight: 600;
    }
    #map {
      height: 480px;
      border-radius: 1rem;
      z-index: 1;
    }
    .itinerary-prose h1 { font-size: 1.75rem; font-weight: 800; color: #FF5E36; margin-bottom: 1.25rem; }
    .itinerary-prose h2 { font-size: 1.35rem; font-weight: 700; color: #FFA000; margin-top: 1.5rem; margin-bottom: 0.75rem; }
    .itinerary-prose h3 { font-size: 1.15rem; font-weight: 600; color: #06B6D4; margin-top: 1.25rem; margin-bottom: 0.5rem; }
    .itinerary-prose p { margin-bottom: 0.75rem; line-height: 1.7; color: #D1D5DB; }
    .itinerary-prose ul { list-style: none; padding-left: 0; margin-bottom: 1rem; }
    .itinerary-prose li { position: relative; padding-left: 1.5rem; margin-bottom: 0.5rem; line-height: 1.6; color: #E5E7EB; }
    .itinerary-prose li::before { content: '✦'; position: absolute; left: 0; color: #FF5E36; }
    .itinerary-prose strong { color: #FFFFFF; }
  </style>
</head>
<body class="min-h-screen flex flex-col antialiased">
  <div class="bg-mesh"></div>

  <!-- Header -->
  <header class="sticky top-0 z-50 backdrop-blur-xl bg-spaceDark/85 border-b border-cardBorder">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-20 flex items-center justify-between">
      <div class="flex items-center gap-3 cursor-pointer" onclick="switchPage('home')">
        <div class="flex items-center justify-center w-11 h-11 rounded-2xl bg-gradient-to-br from-coralPrimary to-amberAccent p-0.5 shadow-lg shadow-coralPrimary/30">
          <div class="w-full h-full bg-spaceDark rounded-[14px] flex items-center justify-center">
            <span class="text-2xl">✈️</span>
          </div>
        </div>
        <div>
          <div class="flex items-center gap-1.5">
            <span class="text-xl font-extrabold tracking-tight bg-clip-text text-transparent bg-gradient-to-r from-white via-gray-100 to-coralPrimary">RoamAI</span>
            <span class="text-[10px] font-bold tracking-widest px-1.5 py-0.5 rounded-full bg-coralPrimary/20 text-coralPrimary border border-coralPrimary/30 uppercase">Student</span>
          </div>
          <p class="text-[11px] text-gray-400 font-medium">Smart AI Travel Architect</p>
        </div>
      </div>

      <nav class="hidden md:flex items-center gap-8 text-sm font-medium text-gray-300">
        <button onclick="switchPage('home')" id="tab-home" class="nav-tab active hover:text-white flex items-center gap-1.5"><span>🌟</span> Discover</button>
        <button onclick="switchPage('planner')" id="tab-planner" class="nav-tab hover:text-white flex items-center gap-1.5"><span>🚀</span> AI Planner</button>
        <button onclick="switchPage('budget')" id="tab-budget" class="nav-tab hover:text-white flex items-center gap-1.5"><span>💰</span> Budget Calc</button>
        <button onclick="switchPage('packing')" id="tab-packing" class="nav-tab hover:text-white flex items-center gap-1.5"><span>🎒</span> Packing List</button>
        <button onclick="switchPage('saved')" id="tab-saved" class="nav-tab hover:text-white flex items-center gap-1.5"><span>📂</span> Saved Trips (<span id="savedCount">0</span>)</button>
      </nav>

      <div>
        <button onclick="switchPage('planner')" class="btn-gradient text-xs sm:text-sm px-5 py-2.5 rounded-xl flex items-center gap-2">
          <span>⚡ Plan a Trip</span>
        </button>
      </div>
    </div>
  </header>

  <!-- Main Content -->
  <main class="flex-grow max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8">
    
    <!-- PAGE 1: DISCOVER -->
    <section id="page-home" class="space-y-16">
      <div class="relative rounded-3xl overflow-hidden glass-card p-8 sm:p-14 border border-white/10">
        <div class="max-w-3xl space-y-6">
          <span class="px-3.5 py-1.5 rounded-full bg-white/5 border border-white/10 text-xs font-semibold text-amberAccent">
            ✨ Powered by High-Performance Groq AI
          </span>
          <h1 class="text-4xl sm:text-6xl font-extrabold tracking-tight text-white leading-tight">
            Plan Epic Student Adventures <br/>
            <span class="bg-clip-text text-transparent bg-gradient-to-r from-coralPrimary via-amberAccent to-cyanAccent">
              On Any Budget in Seconds.
            </span>
          </h1>
          <p class="text-gray-300 text-base sm:text-lg leading-relaxed max-w-2xl">
            Personalized day-by-day schedules, student budget hacks, interactive 3D map pins, and offline PDF exports generated instantly.
          </p>
          <div class="pt-4 flex flex-col sm:flex-row gap-3 max-w-xl">
            <input
              type="text"
              id="heroDestInput"
              placeholder="Where to? (e.g. Tokyo, Bali, Rome, Goa)"
              class="flex-grow px-4 py-3.5 bg-spaceDark border border-white/15 rounded-2xl text-sm text-white placeholder-gray-500 focus:outline-none focus:border-coralPrimary shadow-inner"
              onkeypress="if(event.key === 'Enter') startQuickTrip()"
            />
            <button onclick="startQuickTrip()" class="btn-gradient px-7 py-3.5 rounded-2xl text-sm font-bold">🚀 Start Planning</button>
          </div>
          <div class="pt-6 grid grid-cols-3 gap-4 border-t border-white/10 max-w-lg">
            <div><p class="text-2xl font-extrabold text-white">50,000+</p><p class="text-xs text-gray-400">Trips Planned</p></div>
            <div><p class="text-2xl font-extrabold text-coralPrimary">120+</p><p class="text-xs text-gray-400">Countries</p></div>
            <div><p class="text-2xl font-extrabold text-cyanAccent">100% Free</p><p class="text-xs text-gray-400">For Students</p></div>
          </div>
        </div>
      </div>

      <!-- Hotspot Cards Grid -->
      <div class="space-y-6">
        <h2 class="text-2xl sm:text-3xl font-extrabold text-white">🔥 Trending Student Destinations</h2>
        <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
          <div class="glass-card rounded-2xl p-5 space-y-4 cursor-pointer group" data-tilt data-tilt-max="8" onclick="quickPlanHotspot('Tokyo, Japan', 4, 'Student (Low)', ['Street Food', 'Anime & Pop Culture', 'History'])">
            <img src="https://images.unsplash.com/photo-1503899036084-c55cdd92da26?auto=format&fit=crop&w=600&q=80" class="w-full h-44 object-cover rounded-xl group-hover:scale-105 transition duration-300" />
            <div>
              <h3 class="text-lg font-bold text-white group-hover:text-coralPrimary transition">Tokyo, Japan</h3>
              <p class="text-xs text-gray-400 mt-1">Neon street alleys, futuristic tech, and incredible cheap ramen.</p>
            </div>
            <div class="flex justify-between items-center pt-2 border-t border-white/5">
              <span class="text-xs font-bold text-amberAccent">💰 ~$50/day</span>
              <span class="text-xs font-bold text-coralPrimary">Plan Trip →</span>
            </div>
          </div>

          <div class="glass-card rounded-2xl p-5 space-y-4 cursor-pointer group" data-tilt data-tilt-max="8" onclick="quickPlanHotspot('Bali, Indonesia', 5, 'Student (Low)', ['Nature', 'Beaches', 'Adventure'])">
            <img src="https://images.unsplash.com/photo-1537996194471-e657df975ab4?auto=format&fit=crop&w=600&q=80" class="w-full h-44 object-cover rounded-xl group-hover:scale-105 transition duration-300" />
            <div>
              <h3 class="text-lg font-bold text-white group-hover:text-coralPrimary transition">Bali, Indonesia</h3>
              <p class="text-xs text-gray-400 mt-1">Lush waterfalls, surf beaches, and budget student hostels.</p>
            </div>
            <div class="flex justify-between items-center pt-2 border-t border-white/5">
              <span class="text-xs font-bold text-cyanAccent">💰 ~$30/day</span>
              <span class="text-xs font-bold text-coralPrimary">Plan Trip →</span>
            </div>
          </div>

          <div class="glass-card rounded-2xl p-5 space-y-4 cursor-pointer group" data-tilt data-tilt-max="8" onclick="quickPlanHotspot('Rome, Italy', 3, 'Moderate', ['History', 'Museums', 'Street Food'])">
            <img src="https://images.unsplash.com/photo-1552832230-c0197dd311b5?auto=format&fit=crop&w=600&q=80" class="w-full h-44 object-cover rounded-xl group-hover:scale-105 transition duration-300" />
            <div>
              <h3 class="text-lg font-bold text-white group-hover:text-coralPrimary transition">Rome, Italy</h3>
              <p class="text-xs text-gray-400 mt-1">Colosseum tours, Trevi fountain wishes, and authentic pasta.</p>
            </div>
            <div class="flex justify-between items-center pt-2 border-t border-white/5">
              <span class="text-xs font-bold text-coralPrimary">💰 ~$60/day</span>
              <span class="text-xs font-bold text-coralPrimary">Plan Trip →</span>
            </div>
          </div>

          <div class="glass-card rounded-2xl p-5 space-y-4 cursor-pointer group" data-tilt data-tilt-max="8" onclick="quickPlanHotspot('Amsterdam, Netherlands', 3, 'Student (Low)', ['Nightlife', 'Museums', 'Street Food'])">
            <img src="https://images.unsplash.com/photo-1512470876302-972faa2aa9a4?auto=format&fit=crop&w=600&q=80" class="w-full h-44 object-cover rounded-xl group-hover:scale-105 transition duration-300" />
            <div>
              <h3 class="text-lg font-bold text-white group-hover:text-coralPrimary transition">Amsterdam, Netherlands</h3>
              <p class="text-xs text-gray-400 mt-1">Historic canals, cycling tours, museums, and student vibes.</p>
            </div>
            <div class="flex justify-between items-center pt-2 border-t border-white/5">
              <span class="text-xs font-bold text-purpleAccent">💰 ~$65/day</span>
              <span class="text-xs font-bold text-coralPrimary">Plan Trip →</span>
            </div>
          </div>

          <div class="glass-card rounded-2xl p-5 space-y-4 cursor-pointer group" data-tilt data-tilt-max="8" onclick="quickPlanHotspot('Goa, India', 4, 'Student (Low)', ['Nightlife', 'Beaches', 'Street Food'])">
            <img src="https://images.unsplash.com/photo-1512343879784-a960bf40e7f2?auto=format&fit=crop&w=600&q=80" class="w-full h-44 object-cover rounded-xl group-hover:scale-105 transition duration-300" />
            <div>
              <h3 class="text-lg font-bold text-white group-hover:text-coralPrimary transition">Goa, India</h3>
              <p class="text-xs text-gray-400 mt-1">Sun-kissed beaches, night shacks, and seafood markets.</p>
            </div>
            <div class="flex justify-between items-center pt-2 border-t border-white/5">
              <span class="text-xs font-bold text-emeraldAccent">💰 ~$25/day</span>
              <span class="text-xs font-bold text-coralPrimary">Plan Trip →</span>
            </div>
          </div>

          <div class="glass-card rounded-2xl p-5 space-y-4 cursor-pointer group" data-tilt data-tilt-max="8" onclick="quickPlanHotspot('Kyoto, Japan', 3, 'Student (Low)', ['History', 'Nature', 'Street Food'])">
            <img src="https://images.unsplash.com/photo-1493976040374-85c8e12f0c0e?auto=format&fit=crop&w=600&q=80" class="w-full h-44 object-cover rounded-xl group-hover:scale-105 transition duration-300" />
            <div>
              <h3 class="text-lg font-bold text-white group-hover:text-coralPrimary transition">Kyoto, Japan</h3>
              <p class="text-xs text-gray-400 mt-1">Golden pavilions, bamboo groves, and torii gates.</p>
            </div>
            <div class="flex justify-between items-center pt-2 border-t border-white/5">
              <span class="text-xs font-bold text-amberAccent">💰 ~$45/day</span>
              <span class="text-xs font-bold text-coralPrimary">Plan Trip →</span>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- PAGE 2: AI TRIP PLANNER -->
    <section id="page-planner" class="hidden space-y-8">
      <div class="grid grid-cols-1 lg:grid-cols-12 gap-8">
        <aside class="lg:col-span-5 space-y-6">
          <div class="glass-card p-6 sm:p-7 rounded-3xl border border-white/10 space-y-5 shadow-2xl">
            <div class="flex items-center justify-between pb-3 border-b border-white/10">
              <h2 class="text-lg font-bold text-white flex items-center gap-2"><span>🧭</span> Trip Architect</h2>
              <span class="px-2 py-0.5 text-[10px] font-bold rounded-full bg-emeraldAccent/20 text-emeraldAccent">AI Active</span>
            </div>

            <div class="space-y-1.5">
              <label class="block text-xs font-bold uppercase text-gray-300">📍 Destination</label>
              <input type="text" id="plannerDest" placeholder="e.g. Kyoto, Japan" class="w-full px-4 py-3 bg-spaceDark border border-white/15 rounded-xl text-sm text-white focus:outline-none focus:border-coralPrimary shadow-inner" />
            </div>

            <div class="grid grid-cols-2 gap-4">
              <div class="space-y-1.5">
                <div class="flex justify-between text-xs font-bold text-gray-300">
                  <span>📅 Duration</span>
                  <span id="daysDisp" class="text-coralPrimary">3 Days</span>
                </div>
                <input type="range" id="plannerDays" min="1" max="14" value="3" class="w-full accent-coralPrimary cursor-pointer" oninput="document.getElementById('daysDisp').innerText = this.value + ' Days'" />
              </div>
              <div class="space-y-1.5">
                <label class="block text-xs font-bold uppercase text-gray-300">💰 Tier</label>
                <select id="plannerTier" class="w-full px-3 py-2.5 bg-spaceDark border border-white/15 rounded-xl text-xs text-white focus:outline-none focus:border-coralPrimary">
                  <option value="Student (Low)">Student (Low)</option>
                  <option value="Moderate">Moderate</option>
                  <option value="Luxury">Luxury</option>
                </select>
              </div>
            </div>

            <div class="grid grid-cols-3 gap-3">
              <div class="space-y-1">
                <label class="text-[11px] font-bold text-gray-400">Currency</label>
                <select id="plannerCurr" class="w-full px-2.5 py-2.5 bg-spaceDark border border-white/15 rounded-xl text-xs text-white">
                  <option value="USD">USD ($)</option>
                  <option value="INR">INR (₹)</option>
                  <option value="EUR">EUR (€)</option>
                  <option value="GBP">GBP (£)</option>
                  <option value="JPY">JPY (¥)</option>
                </select>
              </div>
              <div class="col-span-2 space-y-1">
                <label class="text-[11px] font-bold text-gray-400">Cap Budget (Optional)</label>
                <input type="text" id="plannerBudgetCap" placeholder="e.g. 500 or 25000" class="w-full px-3 py-2.5 bg-spaceDark border border-white/15 rounded-xl text-xs text-white" />
              </div>
            </div>

            <div class="space-y-2">
              <label class="block text-xs font-bold uppercase text-gray-300">❤️ Interests</label>
              <div class="flex flex-wrap gap-1.5" id="interestPills">
                <span class="chip-tag active text-xs px-3 py-1.5 rounded-full" onclick="toggleTag(this, 'Street Food')">🍜 Street Food</span>
                <span class="chip-tag active text-xs px-3 py-1.5 rounded-full" onclick="toggleTag(this, 'History & Shrines')">🏯 History</span>
                <span class="chip-tag text-xs px-3 py-1.5 rounded-full" onclick="toggleTag(this, 'Nature & Trekking')">🌲 Nature</span>
                <span class="chip-tag text-xs px-3 py-1.5 rounded-full" onclick="toggleTag(this, 'Nightlife')">🌙 Nightlife</span>
                <span class="chip-tag text-xs px-3 py-1.5 rounded-full" onclick="toggleTag(this, 'Museums')">🎨 Museums</span>
                <span class="chip-tag text-xs px-3 py-1.5 rounded-full" onclick="toggleTag(this, 'Adventure')">🏄 Adventure</span>
              </div>
            </div>

            <div class="grid grid-cols-2 gap-4">
              <div class="space-y-1">
                <label class="text-[11px] font-bold text-gray-400">Must-Visit</label>
                <input type="text" id="plannerMustVisit" placeholder="e.g. Fushimi Inari" class="w-full px-3 py-2.5 bg-spaceDark border border-white/15 rounded-xl text-xs text-white" />
              </div>
              <div class="space-y-1">
                <label class="text-[11px] font-bold text-gray-400">Pace</label>
                <select id="plannerPace" class="w-full px-2.5 py-2.5 bg-spaceDark border border-white/15 rounded-xl text-xs text-white">
                  <option value="Balanced">Balanced</option>
                  <option value="Relaxed">Relaxed</option>
                  <option value="Packed Action">Packed</option>
                </select>
              </div>
            </div>

            <button id="genBtn" onclick="planTrip()" class="w-full btn-gradient py-3.5 rounded-2xl font-extrabold text-sm flex items-center justify-center gap-2">
              <span>🚀 Generate AI Itinerary</span>
            </button>
          </div>
        </aside>

        <!-- Right Side: Results Area -->
        <div class="lg:col-span-7 space-y-6">
          <div id="plannerErr" class="hidden p-4 rounded-2xl bg-red-950/80 border border-red-800 text-red-200 text-sm"></div>

          <div id="plannerPlaceholder" class="glass-card rounded-3xl p-12 text-center space-y-4">
            <div class="text-4xl">🗺️</div>
            <h3 class="text-2xl font-extrabold text-white">Your Custom Plan Awaits</h3>
            <p class="text-gray-400 text-sm max-w-md mx-auto">
              Select your parameters on the left and hit generate to draft your itinerary & interactive map.
            </p>
          </div>

          <div id="plannerLoading" class="hidden glass-card rounded-3xl p-12 text-center space-y-4 border border-coralPrimary/30">
            <div class="w-14 h-14 border-4 border-coralPrimary/20 border-t-coralPrimary rounded-full animate-spin mx-auto"></div>
            <h3 class="text-xl font-bold text-white">Architecting Your Trip...</h3>
            <p class="text-xs text-coralPrimary animate-pulse">Calculating budget breakdowns and geocoding landmark pins...</p>
          </div>

          <div id="plannerResults" class="hidden space-y-6">
            <div class="glass-card p-6 rounded-3xl border border-white/10 space-y-4 shadow-xl">
              <h3 id="mapHeading" class="text-lg font-bold text-white">📍 Interactive Destination Map</h3>
              <div id="map"></div>
            </div>

            <div class="glass-card p-6 sm:p-8 rounded-3xl border border-white/10 space-y-6 shadow-xl">
              <div class="flex flex-wrap items-center justify-between gap-3 pb-4 border-b border-white/10">
                <h3 class="text-lg font-bold text-white">📝 Your Itinerary Blueprint</h3>
                <div class="flex flex-wrap gap-2">
                  <button onclick="saveTrip()" class="btn-secondary px-3 py-1.5 rounded-xl text-xs font-bold">💾 Save Trip</button>
                  <button onclick="copyTrip()" class="btn-secondary px-3 py-1.5 rounded-xl text-xs font-bold">📋 Copy</button>
                  <button onclick="downloadTripPDF()" class="btn-gradient px-3.5 py-1.5 rounded-xl text-xs font-bold">⬇️ Export PDF</button>
                </div>
              </div>
              <div id="itineraryView" class="itinerary-prose text-sm p-4 rounded-2xl bg-spaceDark/60 border border-white/5"></div>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- PAGE 3: BUDGET CALCULATOR -->
    <section id="page-budget" class="hidden space-y-8 max-w-4xl mx-auto">
      <div class="text-center space-y-2">
        <h2 class="text-3xl font-extrabold text-white">💰 Student Trip Budget Calculator</h2>
        <p class="text-gray-400 text-sm">Estimate and balance your trip expenses so you never run out of funds abroad.</p>
      </div>

      <div class="grid grid-cols-1 md:grid-cols-12 gap-8">
        <div class="md:col-span-7 glass-card p-6 sm:p-8 rounded-3xl border border-white/10 space-y-5">
          <div class="grid grid-cols-2 gap-4">
            <div><label class="text-xs font-bold text-gray-300">Days</label><input type="number" id="bDays" value="4" class="w-full px-3 py-2 bg-spaceDark border border-white/15 rounded-xl text-sm text-white" oninput="calcBudget()" /></div>
            <div><label class="text-xs font-bold text-gray-300">Currency</label><select id="bCurr" class="w-full px-3 py-2 bg-spaceDark border border-white/15 rounded-xl text-sm text-white" onchange="calcBudget()"><option value="$">$ (USD)</option><option value="₹">₹ (INR)</option><option value="€">€ (EUR)</option></select></div>
          </div>
          <div><div class="flex justify-between text-xs text-gray-300"><span>🚆 Flights / Trains</span><span id="bValTrans">$120</span></div><input type="range" id="bTrans" min="0" max="1000" step="10" value="120" class="w-full accent-coralPrimary cursor-pointer" oninput="calcBudget()" /></div>
          <div><div class="flex justify-between text-xs text-gray-300"><span>🏨 Hostel (Per Night)</span><span id="bValStay">$25</span></div><input type="range" id="bStay" min="5" max="200" step="5" value="25" class="w-full accent-cyanAccent cursor-pointer" oninput="calcBudget()" /></div>
          <div><div class="flex justify-between text-xs text-gray-300"><span>🍜 Food (Per Day)</span><span id="bValFood">$20</span></div><input type="range" id="bFood" min="5" max="150" step="5" value="20" class="w-full accent-amberAccent cursor-pointer" oninput="calcBudget()" /></div>
          <div><div class="flex justify-between text-xs text-gray-300"><span>🎟️ Activities (Per Day)</span><span id="bValAct">$15</span></div><input type="range" id="bAct" min="0" max="100" step="5" value="15" class="w-full accent-emeraldAccent cursor-pointer" oninput="calcBudget()" /></div>
          <div><div class="flex justify-between text-xs text-gray-300"><span>🛡️ Emergency Buffer</span><span id="bValBuf">$50</span></div><input type="range" id="bBuf" min="0" max="300" step="10" value="50" class="w-full accent-purpleAccent cursor-pointer" oninput="calcBudget()" /></div>
        </div>

        <div class="md:col-span-5 glass-card p-6 sm:p-8 rounded-3xl border border-white/10 flex flex-col justify-between">
          <div class="space-y-3">
            <span class="text-xs font-bold text-gray-400 uppercase">Estimated Total</span>
            <h1 class="text-5xl font-extrabold text-white" id="bTotal">$410</h1>
            <p class="text-xs text-cyanAccent font-semibold" id="bAvg">Avg $102.50 / day</p>
          </div>
          <div class="pt-4 border-t border-white/10 space-y-1 text-[11px] text-gray-400">
            <h4 class="font-bold text-amberAccent">💡 Student Savings Hacks:</h4>
            <p>• Flash your Student ID for 20-50% off museums.</p>
            <p>• Book night trains to save 1 night of hostel fees.</p>
          </div>
        </div>
      </div>
    </section>

    <!-- PAGE 4: PACKING CHECKLIST -->
    <section id="page-packing" class="hidden space-y-8 max-w-4xl mx-auto">
      <div class="text-center space-y-2">
        <h2 class="text-3xl font-extrabold text-white">🎒 Smart Student Packing Checklist</h2>
        <p class="text-gray-400 text-sm">Interactive checklist saved automatically to your device.</p>
      </div>

      <div class="glass-card p-6 rounded-3xl border border-white/10 space-y-3">
        <div class="flex justify-between text-xs font-bold">
          <span class="text-gray-300">Packing Progress</span>
          <span class="text-emeraldAccent" id="packProgressText">0% Packed</span>
        </div>
        <div class="h-3 w-full bg-gray-800 rounded-full overflow-hidden">
          <div id="packProgressBar" style="width: 0%" class="h-full bg-gradient-to-r from-coralPrimary to-emeraldAccent transition-all duration-300"></div>
        </div>
      </div>

      <div id="packingListContainer" class="grid grid-cols-1 md:grid-cols-2 gap-6"></div>
    </section>

    <!-- PAGE 5: SAVED TRIPS -->
    <section id="page-saved" class="hidden space-y-8 max-w-5xl mx-auto">
      <div class="flex justify-between items-center">
        <h2 class="text-3xl font-extrabold text-white">📂 My Saved Itineraries</h2>
        <button onclick="clearTrips()" class="text-xs text-red-400 hover:underline">Clear All</button>
      </div>
      <div id="savedGrid" class="grid grid-cols-1 md:grid-cols-3 gap-6"></div>
      <div id="savedEmpty" class="glass-card rounded-3xl p-12 text-center space-y-3">
        <p class="text-gray-400 text-sm">No saved trips yet. Generate a trip and click "Save Trip"!</p>
      </div>
    </section>

  </main>

  <footer class="mt-20 border-t border-cardBorder bg-spaceDark/90 py-8 text-center text-xs text-gray-500">
    RoamAI • AI Student Travel Planner • Powered by Groq AI & FastAPI
  </footer>

  <script>
    let activePage = 'home';
    let selectedInterests = ['Street Food', 'History & Shrines'];
    let currentTrip = null;
    let mapInstance = null;
    let markersLayer = null;

    function switchPage(page) {
      activePage = page;
      ['home', 'planner', 'budget', 'packing', 'saved'].forEach(p => {
        document.getElementById(`page-${p}`).classList.toggle('hidden', p !== page);
        const t = document.getElementById(`tab-${p}`);
        if (t) t.classList.toggle('active', p === page);
      });
      if (page === 'saved') renderSaved();
      if (page === 'packing') renderPacking();
      if (page === 'planner' && mapInstance) setTimeout(() => mapInstance.invalidateSize(), 200);
      window.scrollTo({ top: 0, behavior: 'smooth' });
    }

    function toggleTag(el, tag) {
      if (selectedInterests.includes(tag)) {
        selectedInterests = selectedInterests.filter(t => t !== tag);
        el.classList.remove('active');
      } else {
        selectedInterests.push(tag);
        el.classList.add('active');
      }
    }

    function startQuickTrip() {
      const dest = document.getElementById('heroDestInput').value.trim();
      if (dest) document.getElementById('plannerDest').value = dest;
      switchPage('planner');
    }

    function quickPlanHotspot(dest, days, tier, tags) {
      document.getElementById('plannerDest').value = dest;
      document.getElementById('plannerDays').value = days;
      document.getElementById('daysDisp').innerText = days + ' Days';
      document.getElementById('plannerTier').value = tier;
      selectedInterests = tags;
      switchPage('planner');
      planTrip();
    }

    async function planTrip() {
      const destination = document.getElementById('plannerDest').value.trim();
      if (!destination) return alert('Please enter a destination.');

      const days = parseInt(document.getElementById('plannerDays').value) || 3;
      const budgetTier = document.getElementById('plannerTier').value;
      const currency = document.getElementById('plannerCurr').value;
      const budgetAmount = document.getElementById('plannerBudgetCap').value.trim();
      const mustVisit = document.getElementById('plannerMustVisit').value.trim();
      const pace = document.getElementById('plannerPace').value;

      document.getElementById('plannerErr').classList.add('hidden');
      document.getElementById('plannerPlaceholder').classList.add('hidden');
      document.getElementById('plannerResults').classList.add('hidden');
      document.getElementById('plannerLoading').classList.remove('hidden');

      try {
        const res = await fetch('/api/generate', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            destination, days, budget_level: budgetTier, budget_amount: budgetAmount,
            currency, interests: selectedInterests, must_visit: mustVisit, travel_pace: pace
          })
        });

        if (!res.ok) {
          const err = await res.json().catch(() => ({}));
          throw new Error(err.detail || 'Failed to generate itinerary');
        }

        const data = await res.json();
        currentTrip = data;

        // Render Map
        renderMap(data.destination_coords, data.markers);

        // Render Markdown
        document.getElementById('itineraryView').innerHTML = marked.parse(data.itinerary);
        document.getElementById('mapHeading').innerText = `📍 Exploring ${destination}`;

        document.getElementById('plannerLoading').classList.add('hidden');
        document.getElementById('plannerResults').classList.remove('hidden');
      } catch (err) {
        document.getElementById('plannerLoading').classList.add('hidden');
        const errBox = document.getElementById('plannerErr');
        errBox.innerText = `Error: ${err.message}`;
        errBox.classList.remove('hidden');
      }
    }

    function renderMap(center, markers) {
      const centerCoords = center || (markers.length > 0 ? markers[0].coords : [20, 0]);
      if (!mapInstance) {
        mapInstance = L.map('map').setView(centerCoords, 13);
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', { maxZoom: 19 }).addTo(mapInstance);
        markersLayer = L.featureGroup().addTo(mapInstance);
      } else {
        markersLayer.clearLayers();
        mapInstance.setView(centerCoords, 13);
      }

      const bounds = [];
      markers.forEach(m => {
        if (!m.coords) return;
        bounds.push(m.coords);
        const marker = L.marker(m.coords).addTo(markersLayer);
        marker.bindPopup(`<b>${m.name}</b>`);
        marker.bindTooltip(m.name);
      });

      if (bounds.length > 1) mapInstance.fitBounds(bounds, { padding: [40, 40] });
      setTimeout(() => mapInstance.invalidateSize(), 300);
    }

    function copyTrip() {
      if (currentTrip) {
        navigator.clipboard.writeText(currentTrip.itinerary);
        alert('Itinerary copied to clipboard!');
      }
    }

    function downloadTripPDF() {
      if (!currentTrip) return;
      const el = document.getElementById('itineraryView');
      const opt = {
        margin: [10, 10, 10, 10],
        filename: `Trip_to_${currentTrip.trip_summary.destination}.pdf`,
        image: { type: 'jpeg', quality: 0.98 },
        html2canvas: { scale: 2, useCORS: true },
        jsPDF: { unit: 'mm', format: 'a4', orientation: 'portrait' }
      };
      html2pdf().set(opt).from(el).save();
    }

    function saveTrip() {
      if (!currentTrip) return;
      const trips = JSON.parse(localStorage.getItem('saved_trips') || '[]');
      trips.unshift({
        id: Date.now(),
        destination: currentTrip.trip_summary.destination,
        days: currentTrip.trip_summary.days,
        itinerary: currentTrip.itinerary,
        date: new Date().toLocaleDateString()
      });
      localStorage.setItem('saved_trips', JSON.stringify(trips));
      document.getElementById('savedCount').innerText = trips.length;
      alert('Trip saved successfully!');
    }

    function renderSaved() {
      const trips = JSON.parse(localStorage.getItem('saved_trips') || '[]');
      document.getElementById('savedCount').innerText = trips.length;
      const grid = document.getElementById('savedGrid');
      const empty = document.getElementById('savedEmpty');

      if (trips.length === 0) {
        grid.innerHTML = '';
        empty.classList.remove('hidden');
        return;
      }
      empty.classList.add('hidden');
      grid.innerHTML = trips.map(t => `
        <div class="glass-card p-5 rounded-2xl border border-white/10 space-y-3">
          <div class="flex justify-between">
            <h4 class="text-base font-bold text-white">${t.destination}</h4>
            <span class="text-xs text-coralPrimary font-bold">${t.days} Days</span>
          </div>
          <p class="text-xs text-gray-400">Saved: ${t.date}</p>
          <button onclick='loadSaved(${JSON.stringify(t.itinerary)}, "${t.destination}")' class="w-full btn-gradient py-2 rounded-xl text-xs font-bold">View Plan</button>
        </div>
      `).join('');
    }

    function loadSaved(itinerary, dest) {
      document.getElementById('plannerDest').value = dest;
      switchPage('planner');
      document.getElementById('plannerPlaceholder').classList.add('hidden');
      document.getElementById('plannerResults').classList.remove('hidden');
      document.getElementById('itineraryView').innerHTML = marked.parse(itinerary);
      document.getElementById('mapHeading').innerText = `📍 Exploring ${dest}`;
    }

    function clearTrips() {
      localStorage.removeItem('saved_trips');
      renderSaved();
    }

    function calcBudget() {
      const days = parseInt(document.getElementById('bDays').value) || 1;
      const curr = document.getElementById('bCurr').value;
      const trans = parseFloat(document.getElementById('bTrans').value) || 0;
      const stay = parseFloat(document.getElementById('bStay').value) || 0;
      const food = parseFloat(document.getElementById('bFood').value) || 0;
      const act = parseFloat(document.getElementById('bAct').value) || 0;
      const buf = parseFloat(document.getElementById('bBuf').value) || 0;

      document.getElementById('bValTrans').innerText = `${curr}${trans}`;
      document.getElementById('bValStay').innerText = `${curr}${stay}/night`;
      document.getElementById('bValFood').innerText = `${curr}${food}/day`;
      document.getElementById('bValAct').innerText = `${curr}${act}/day`;
      document.getElementById('bValBuf').innerText = `${curr}${buf}`;

      const total = trans + (stay * Math.max(days - 1, 1)) + (food * days) + (act * days) + buf;
      document.getElementById('bTotal').innerText = `${curr}${total.toFixed(0)}`;
      document.getElementById('bAvg').innerText = `Avg ${curr}${(total / days).toFixed(2)} / day`;
    }

    const packItems = [
      { id: 1, name: 'Passport / Student ID', checked: true },
      { id: 2, name: 'Zero-Forex Travel Card & Cash', checked: true },
      { id: 3, name: 'Universal Power Adapter', checked: true },
      { id: 4, name: 'Power Bank (10,000mAh)', checked: false },
      { id: 5, name: 'Comfortable Walking Sneakers', checked: true },
      { id: 6, name: 'Quick-dry Hostel Towel', checked: false },
      { id: 7, name: 'First Aid & Meds', checked: false }
    ];

    function renderPacking() {
      const container = document.getElementById('packingListContainer');
      const total = packItems.length;
      const checked = packItems.filter(i => i.checked).length;
      const pct = Math.round((checked / total) * 100);

      document.getElementById('packProgressText').innerText = `${pct}% Packed (${checked}/${total})`;
      document.getElementById('packProgressBar').style.width = `${pct}%`;

      container.innerHTML = `
        <div class="glass-card p-5 rounded-2xl border border-white/10 space-y-2 col-span-full">
          ${packItems.map(item => `
            <label class="flex items-center gap-3 p-2 rounded-xl hover:bg-white/5 cursor-pointer">
              <input type="checkbox" ${item.checked ? 'checked' : ''} onchange="togglePack(${item.id})" class="accent-coralPrimary" />
              <span class="text-xs ${item.checked ? 'line-through text-gray-500' : 'text-gray-200'}">${item.name}</span>
            </label>
          `).join('')}
        </div>
      `;
    }

    function togglePack(id) {
      const item = packItems.find(i => i.id === id);
      if (item) item.checked = !item.checked;
      renderPacking();
    }

    document.addEventListener('DOMContentLoaded', () => {
      calcBudget();
      renderPacking();
      const trips = JSON.parse(localStorage.getItem('saved_trips') || '[]');
      document.getElementById('savedCount').innerText = trips.length;
    });
  </script>
</body>
</html>"""

@app.get("/", response_class=HTMLResponse)
def serve_index():
    return HTMLResponse(content=HTML_CONTENT, status_code=200)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)