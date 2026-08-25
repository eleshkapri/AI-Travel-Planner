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
    version="2.1.0"
)

# Enable CORS
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
    region: Optional[str] = "Global / USD"
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
        "version": "2.1.0",
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
    region_info = req.region or "Global"
    budget_text = f"{req.budget_level} Tier ({curr}) for {region_info} traveler"
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
    - Traveler Region/Currency: {region_info} ({curr})
    - Budget Level: {budget_text}
    - Specific Interests: {interests_string}
    - {pace_text}
    - {must_visit_instruction}

    Structure your response strictly in clean Markdown as follows:
    # 🌍 [Catchy Trip Title & Emoji]

    ## 💰 Estimated Student Budget Breakdown ({curr})
    - 🏨 **Accommodation ({req.accommodation_style or 'Hostel'}):** [Estimated cost per night & total in {curr}]
    - 🍜 **Food & Street Eats:** [Daily & total food estimate in {curr}]
    - 🚇 **Local Transport:** [Passes/Subway/Bus estimates in {curr}]
    - 🎟️ **Activities & Entry Fees:** [Cost estimates for attractions in {curr}]
    - 💡 **Region-Specific Student Savings Tip:** [1 high-impact money-saving hack tailored for students]

    ## 🗓️ Day-by-Day Itinerary

    ### Day 1: [Day 1 Theme]
    - ☀️ **Morning:** [Actionable morning activity + budget tip]
    - 🌤️ **Afternoon:** [Actionable afternoon activity + food spot recommendation]
    - 🌙 **Evening:** [Evening vibes, sunset spot, or student nightlife]

    (Repeat detailed ### Day X format for all {req.days} days)

    ## 🎒 Essential Student Tips for {req.destination}
    - 3 practical tips for safety, local transit apps, SIM cards, or student discounts.

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
            "region": region_info,
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
        radial-gradient(circle at 12% 15%, rgba(255, 94, 54, 0.14) 0%, transparent 45%),
        radial-gradient(circle at 88% 22%, rgba(6, 182, 212, 0.12) 0%, transparent 45%),
        radial-gradient(circle at 50% 88%, rgba(139, 92, 246, 0.12) 0%, transparent 50%);
    }
    .glass-card {
      background: rgba(18, 24, 38, 0.85);
      backdrop-filter: blur(16px);
      -webkit-backdrop-filter: blur(16px);
      border: 1px solid rgba(255, 255, 255, 0.09);
      box-shadow: 0 10px 30px rgba(0, 0, 0, 0.4);
      transition: all 0.3s ease;
    }
    .glass-card:hover {
      border-color: rgba(255, 94, 54, 0.35);
      transform: translateY(-2px);
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

  <!-- ==================== PROPERLY DESIGNED NAVBAR WITH REGION SELECTOR ==================== -->
  <header class="sticky top-0 z-50 backdrop-blur-xl bg-spaceDark/90 border-b border-cardBorder shadow-2xl">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-20 flex items-center justify-between gap-4">
      
      <!-- Brand Logo (Left) -->
      <div class="flex items-center gap-3 cursor-pointer shrink-0" onclick="switchPage('home')">
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

      <!-- Navigation Tabs (Center) -->
      <nav class="hidden lg:flex items-center gap-7 text-sm font-medium text-gray-300">
        <button onclick="switchPage('home')" id="tab-home" class="nav-tab active hover:text-white flex items-center gap-1.5 transition"><span>🌟</span> Discover</button>
        <button onclick="switchPage('planner')" id="tab-planner" class="nav-tab hover:text-white flex items-center gap-1.5 transition"><span>🚀</span> AI Planner</button>
        <button onclick="switchPage('budget')" id="tab-budget" class="nav-tab hover:text-white flex items-center gap-1.5 transition"><span>💰</span> Budget Calc</button>
        <button onclick="switchPage('packing')" id="tab-packing" class="nav-tab hover:text-white flex items-center gap-1.5 transition"><span>🎒</span> Packing List</button>
        <button onclick="switchPage('saved')" id="tab-saved" class="nav-tab hover:text-white flex items-center gap-1.5 transition"><span>📂</span> Saved (<span id="savedCount">0</span>)</button>
      </nav>

      <!-- Region Selector & CTA (Right) -->
      <div class="flex items-center gap-3 shrink-0">
        
        <!-- Region & Currency Selector -->
        <div class="relative flex items-center">
          <span class="absolute left-3 text-sm pointer-events-none" id="navRegionFlag">🇮🇳</span>
          <select
            id="navRegionSelector"
            onchange="onRegionChange(this.value)"
            class="pl-8 pr-8 py-2 bg-cardDark/90 border border-white/15 hover:border-coralPrimary/50 rounded-xl text-xs font-semibold text-white focus:outline-none focus:border-coralPrimary cursor-pointer shadow-sm transition"
          >
            <option value="INR" data-flag="🇮🇳" data-curr="INR" data-sym="₹" data-name="India" selected>🇮🇳 India (INR ₹)</option>
            <option value="USD" data-flag="🇺🇸" data-curr="USD" data-sym="$" data-name="United States">🇺🇸 USA (USD $)</option>
            <option value="EUR" data-flag="🇪🇺" data-curr="EUR" data-sym="€" data-name="Europe">🇪🇺 Europe (EUR €)</option>
            <option value="GBP" data-flag="🇬🇧" data-curr="GBP" data-sym="£" data-name="United Kingdom">🇬🇧 UK (GBP £)</option>
            <option value="JPY" data-flag="🇯🇵" data-curr="JPY" data-sym="¥" data-name="Japan">🇯🇵 Japan (JPY ¥)</option>
            <option value="AUD" data-flag="🇦🇺" data-curr="AUD" data-sym="A$" data-name="Australia">🇦🇺 Australia (AUD A$)</option>
            <option value="CAD" data-flag="🇨🇦" data-curr="CAD" data-sym="C$" data-name="Canada">🇨🇦 Canada (CAD C$)</option>
            <option value="AED" data-flag="🇦🇪" data-curr="AED" data-sym="AED" data-name="UAE">🇦🇪 UAE (AED)</option>
            <option value="THB" data-flag="🇹🇭" data-curr="THB" data-sym="฿" data-name="Thailand">🇹🇭 Thailand (THB ฿)</option>
          </select>
        </div>

        <!-- Plan Button -->
        <button onclick="switchPage('planner')" class="btn-gradient text-xs sm:text-sm px-4 sm:px-5 py-2.5 rounded-xl flex items-center gap-1.5 whitespace-nowrap">
          <span>⚡ Plan Trip</span>
        </button>
      </div>

    </div>

    <!-- Mobile Sub-Nav -->
    <div class="lg:hidden flex items-center justify-around py-2.5 px-2 bg-cardDark/95 border-t border-cardBorder text-xs text-gray-400">
      <button onclick="switchPage('home')" id="mob-home" class="text-coralPrimary font-bold flex flex-col items-center"><span>🌟</span>Home</button>
      <button onclick="switchPage('planner')" id="mob-planner" class="flex flex-col items-center"><span>🚀</span>Planner</button>
      <button onclick="switchPage('budget')" id="mob-budget" class="flex flex-col items-center"><span>💰</span>Budget</button>
      <button onclick="switchPage('packing')" id="mob-packing" class="flex flex-col items-center"><span>🎒</span>Packing</button>
      <button onclick="switchPage('saved')" id="mob-saved" class="flex flex-col items-center"><span>📂</span>Saved</button>
    </div>
  </header>

  <!-- ==================== MAIN CONTENT ==================== -->
  <main class="flex-grow max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8">

    <!-- Region Information Alert Banner -->
    <div id="regionInfoBanner" class="mb-8 p-4 rounded-2xl bg-gradient-to-r from-coralPrimary/10 via-amberAccent/10 to-cyanAccent/10 border border-coralPrimary/30 flex items-center justify-between text-xs sm:text-sm text-gray-200">
      <div class="flex items-center gap-3">
        <span class="text-2xl" id="bannerFlag">🇮🇳</span>
        <div>
          <span class="font-bold text-amberAccent" id="bannerRegionTitle">Active Region: India (INR ₹)</span>
          <p class="text-xs text-gray-400" id="bannerRegionTip">
            Student Perks: Use IRCTC student concessions for rail travel & Google Pay/UPI for zero-fee local food stalls.
          </p>
        </div>
      </div>
      <button onclick="switchPage('planner')" class="hidden sm:inline-block px-3 py-1.5 rounded-lg bg-white/10 hover:bg-white/15 text-xs font-bold text-white transition">
        Explore Plans →
      </button>
    </div>
    
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

      <!-- Hotspot Cards Grid with Regionally Synced Budgets -->
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
              <span class="text-xs font-bold text-amberAccent" id="hotspotTokyoCost">💰 ~₹4,000 / day</span>
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
              <span class="text-xs font-bold text-cyanAccent" id="hotspotBaliCost">💰 ~₹2,500 / day</span>
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
              <span class="text-xs font-bold text-coralPrimary" id="hotspotRomeCost">💰 ~₹5,000 / day</span>
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
              <span class="text-xs font-bold text-purpleAccent" id="hotspotAmsterdamCost">💰 ~₹5,500 / day</span>
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
              <span class="text-xs font-bold text-emeraldAccent" id="hotspotGoaCost">💰 ~₹2,000 / day</span>
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
              <span class="text-xs font-bold text-amberAccent" id="hotspotKyotoCost">💰 ~₹3,800 / day</span>
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
              <span class="px-2 py-0.5 text-[10px] font-bold rounded-full bg-emeraldAccent/20 text-emeraldAccent" id="activeRegionBadge">🇮🇳 INR Active</span>
            </div>

            <div class="space-y-1.5">
              <label class="block text-xs font-bold uppercase text-gray-300">📍 Destination</label>
              <input type="text" id="plannerDest" placeholder="e.g. Kyoto, Japan or Manali, India" class="w-full px-4 py-3 bg-spaceDark border border-white/15 rounded-xl text-sm text-white focus:outline-none focus:border-coralPrimary shadow-inner" />
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
                <input type="text" id="plannerCurr" readonly value="INR (₹)" class="w-full px-2.5 py-2.5 bg-spaceDark/60 border border-white/10 rounded-xl text-xs text-amberAccent font-bold" />
              </div>
              <div class="col-span-2 space-y-1">
                <label class="text-[11px] font-bold text-gray-400">Cap Budget (Optional)</label>
                <input type="text" id="plannerBudgetCap" placeholder="e.g. 20000 or 500" class="w-full px-3 py-2.5 bg-spaceDark border border-white/15 rounded-xl text-xs text-white" />
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
            <p class="text-xs text-coralPrimary animate-pulse">Calculating regional budget breakdowns and geocoding landmark pins...</p>
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
        <p class="text-gray-400 text-sm">Estimate and balance your trip expenses synced to your selected region currency.</p>
      </div>

      <div class="grid grid-cols-1 md:grid-cols-12 gap-8">
        <div class="md:col-span-7 glass-card p-6 sm:p-8 rounded-3xl border border-white/10 space-y-5">
          <div class="grid grid-cols-2 gap-4">
            <div><label class="text-xs font-bold text-gray-300">Days</label><input type="number" id="bDays" value="4" class="w-full px-3 py-2 bg-spaceDark border border-white/15 rounded-xl text-sm text-white" oninput="calcBudget()" /></div>
            <div><label class="text-xs font-bold text-gray-300">Region Currency</label><input type="text" id="bCurrDisplay" readonly value="INR (₹)" class="w-full px-3 py-2 bg-spaceDark/60 border border-white/10 rounded-xl text-sm text-amberAccent font-bold" /></div>
          </div>
          <div><div class="flex justify-between text-xs text-gray-300"><span>🚆 Flights / Trains</span><span id="bValTrans">₹3,000</span></div><input type="range" id="bTrans" min="0" max="50000" step="500" value="3000" class="w-full accent-coralPrimary cursor-pointer" oninput="calcBudget()" /></div>
          <div><div class="flex justify-between text-xs text-gray-300"><span>🏨 Hostel (Per Night)</span><span id="bValStay">₹800</span></div><input type="range" id="bStay" min="200" max="10000" step="100" value="800" class="w-full accent-cyanAccent cursor-pointer" oninput="calcBudget()" /></div>
          <div><div class="flex justify-between text-xs text-gray-300"><span>🍜 Food (Per Day)</span><span id="bValFood">₹600</span></div><input type="range" id="bFood" min="100" max="8000" step="100" value="600" class="w-full accent-amberAccent cursor-pointer" oninput="calcBudget()" /></div>
          <div><div class="flex justify-between text-xs text-gray-300"><span>🎟️ Activities (Per Day)</span><span id="bValAct">₹400</span></div><input type="range" id="bAct" min="0" max="5000" step="100" value="400" class="w-full accent-emeraldAccent cursor-pointer" oninput="calcBudget()" /></div>
          <div><div class="flex justify-between text-xs text-gray-300"><span>🛡️ Emergency Buffer</span><span id="bValBuf">₹1,500</span></div><input type="range" id="bBuf" min="0" max="15000" step="250" value="1500" class="w-full accent-purpleAccent cursor-pointer" oninput="calcBudget()" /></div>
        </div>

        <div class="md:col-span-5 glass-card p-6 sm:p-8 rounded-3xl border border-white/10 flex flex-col justify-between">
          <div class="space-y-3">
            <span class="text-xs font-bold text-gray-400 uppercase">Estimated Total</span>
            <h1 class="text-5xl font-extrabold text-white" id="bTotal">₹10,500</h1>
            <p class="text-xs text-cyanAccent font-semibold" id="bAvg">Avg ₹2,625 / day</p>
          </div>
          <div class="pt-4 border-t border-white/10 space-y-2 text-[11px] text-gray-400" id="budgetRegionalTips">
            <h4 class="font-bold text-amberAccent">💡 Student Regional Hacks:</h4>
            <p>• Book Indian Railway tickets in advance or look for Tatkal/student quotas.</p>
            <p>• Use youth hostels (Zostel/Hosteller) for budget social stays.</p>
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
    RoamAI • AI Student Travel Planner • Multi-Region Support • Powered by Groq AI & FastAPI
  </footer>

  <!-- ==================== JAVASCRIPT LOGIC ==================== -->
  <script>
    // Region Configuration Database
    const REGIONS = {
      INR: {
        flag: "🇮🇳", name: "India", curr: "INR", sym: "₹", multiplier: 80,
        tip: "Student Perks: Use IRCTC student concessions for rail travel & UPI / Google Pay for zero-fee local food carts.",
        budgetTips: [
          "• Book Indian Railway tickets in advance or look for Tatkal/student quotas.",
          "• Stay in verified youth backpacker hostels (Zostel, Hosteller, goSTOPS).",
          "• Eat at local thali joints and morning street food stalls."
        ],
        defaults: { trans: 3000, stay: 800, food: 600, act: 400, buf: 1500, maxTrans: 40000, maxStay: 8000, maxFood: 6000, maxAct: 4000, maxBuf: 10000, step: 100 },
        hotspots: { tokyo: "₹4,000", bali: "₹2,500", rome: "₹5,000", amsterdam: "₹5,500", goa: "₹2,000", kyoto: "₹3,800" }
      },
      USD: {
        flag: "🇺🇸", name: "United States", curr: "USD", sym: "$", multiplier: 1,
        tip: "Student Perks: Use Amtrak student discounts (15% off) & Unisdays / StudentBeans for museum passes.",
        budgetTips: [
          "• Flash your student ID for 20-50% off museums and galleries.",
          "• Take Megabus or Flixbus for cheap inter-city travel.",
          "• Use grocery store delis and campus dining deals."
        ],
        defaults: { trans: 120, stay: 30, food: 25, act: 15, buf: 50, maxTrans: 1000, maxStay: 200, maxFood: 150, maxAct: 100, maxBuf: 300, step: 5 },
        hotspots: { tokyo: "$50", bali: "$30", rome: "$60", amsterdam: "$65", goa: "$25", kyoto: "$45" }
      },
      EUR: {
        flag: "🇪🇺", name: "Europe", curr: "EUR", sym: "€", multiplier: 0.92,
        tip: "Student Perks: EU students under 26 get FREE entry to Louvre, Colosseum, and many state monuments!",
        budgetTips: [
          "• Book Eurail / Interrail Youth Passes for unlimited train travel.",
          "• Look for 'First Sunday of the month' free museum entries across Europe.",
          "• Buy fresh baguettes, cheese, and fruit from local market stalls."
        ],
        defaults: { trans: 100, stay: 25, food: 20, act: 12, buf: 45, maxTrans: 900, maxStay: 180, maxFood: 140, maxAct: 90, maxBuf: 250, step: 5 },
        hotspots: { tokyo: "€45", bali: "€28", rome: "€55", amsterdam: "€60", goa: "€22", kyoto: "€40" }
      },
      GBP: {
        flag: "🇬🇧", name: "United Kingdom", curr: "GBP", sym: "£", multiplier: 0.79,
        tip: "Student Perks: Get a 16-25 Railcard for 1/3 off all UK train fares & free entry to all major London museums!",
        budgetTips: [
          "• Major national museums in London/Edinburgh have 100% free permanent exhibits.",
          "• Grab 'Meal Deals' at Tesco/Sainsbury's for under £4.",
          "• Book National Express coach tickets early for £5 intercity routes."
        ],
        defaults: { trans: 85, stay: 22, food: 18, act: 10, buf: 40, maxTrans: 800, maxStay: 160, maxFood: 120, maxAct: 80, maxBuf: 220, step: 5 },
        hotspots: { tokyo: "£40", bali: "£24", rome: "£48", amsterdam: "£52", goa: "£20", kyoto: "£36" }
      },
      JPY: {
        flag: "🇯🇵", name: "Japan", curr: "JPY", sym: "¥", multiplier: 155,
        tip: "Student Perks: Load a Suica/Pasmo IC card for easy subway transit & look for 100-yen convenience stores.",
        budgetTips: [
          "• Eat hot delicious meals at 7-Eleven, Lawson, and FamilyMart for under ¥600.",
          "• Buy regional JR passes if traveling between Tokyo, Kyoto, and Osaka.",
          "• Visit shrine grounds which are almost always completely free to explore."
        ],
        defaults: { trans: 18000, stay: 4500, food: 3500, act: 2000, buf: 7500, maxTrans: 150000, maxStay: 30000, maxFood: 25000, maxAct: 15000, maxBuf: 45000, step: 500 },
        hotspots: { tokyo: "¥7,500", bali: "¥4,500", rome: "¥9,000", amsterdam: "¥10,000", goa: "¥3,500", kyoto: "¥6,800" }
      },
      AUD: {
        flag: "🇦🇺", name: "Australia", curr: "AUD", sym: "A$", multiplier: 1.52,
        tip: "Student Perks: Use student concession Opal/Myki cards & cook in hostel communal kitchens.",
        budgetTips: [
          "• Major Australian state galleries and botanical gardens are 100% free.",
          "• Shop at ALDI or local fruit markets for budget meal prep.",
          "• Utilize free city center trams in Melbourne and Adelaide."
        ],
        defaults: { trans: 180, stay: 45, food: 35, act: 20, buf: 75, maxTrans: 1500, maxStay: 300, maxFood: 220, maxAct: 150, maxBuf: 450, step: 5 },
        hotspots: { tokyo: "A$75", bali: "A$45", rome: "A$90", amsterdam: "A$95", goa: "A$38", kyoto: "A$68" }
      },
      CAD: {
        flag: "🇨🇦", name: "Canada", curr: "CAD", sym: "C$", multiplier: 1.36,
        tip: "Student Perks: Use Via Rail youth passes and SPC card for student retail & food discounts.",
        budgetTips: [
          "• Free entry to Canadian National Parks for youth under 17.",
          "• Use Megabus/Rider Express for budget travel across Ontario/Quebec.",
          "• Eat at student food co-ops and local poutine joints."
        ],
        defaults: { trans: 160, stay: 40, food: 32, act: 18, buf: 65, maxTrans: 1300, maxStay: 260, maxFood: 200, maxAct: 130, maxBuf: 400, step: 5 },
        hotspots: { tokyo: "C$68", bali: "C$40", rome: "C$80", amsterdam: "C$85", goa: "C$34", kyoto: "C$60" }
      },
      AED: {
        flag: "🇦🇪", name: "UAE", curr: "AED", sym: "AED", multiplier: 3.67,
        tip: "Student Perks: Use the Nol Silver card on Dubai Metro & look for student discounts at museums.",
        budgetTips: [
          "• Ride the 1-dirham traditional Abra boat across Dubai Creek.",
          "• Explore Old Dubai (Al Fahidi, Deira Spice Souk) which are free to visit.",
          "• Eat delicious shawarma and street falafels for under 10 AED."
        ],
        defaults: { trans: 440, stay: 110, food: 90, act: 55, buf: 180, maxTrans: 3600, maxStay: 750, maxFood: 550, maxAct: 350, maxBuf: 1100, step: 10 },
        hotspots: { tokyo: "180 AED", bali: "110 AED", rome: "220 AED", amsterdam: "240 AED", goa: "90 AED", kyoto: "165 AED" }
      },
      THB: {
        flag: "🇹🇭", name: "Thailand", curr: "THB", sym: "฿", multiplier: 36.5,
        tip: "Student Perks: Use the BTS Skytrain / MRT Rabbit student card & eat at world-famous night markets.",
        budgetTips: [
          "• Eat authentic Pad Thai and Mango Sticky Rice at night markets for 50-80 THB.",
          "• Use the Chao Phraya Express Boat for 15-30 THB scenic river transit.",
          "• Stay in stylish social backpacker hostels for under 400 THB/night."
        ],
        defaults: { trans: 4000, stay: 900, food: 700, act: 500, buf: 1800, maxTrans: 35000, maxStay: 7000, maxFood: 5500, maxAct: 3500, maxBuf: 10000, step: 50 },
        hotspots: { tokyo: "฿1,800", bali: "฿1,100", rome: "฿2,200", amsterdam: "฿2,400", goa: "฿900", kyoto: "฿1,650" }
      }
    };

    let activeRegionKey = "INR";
    let activePage = "home";
    let selectedInterests = ["Street Food", "History & Shrines"];
    let currentTrip = null;
    let mapInstance = null;
    let markersLayer = null;

    // --- On Region Change Handler with Persistence ---
    function onRegionChange(regionKey, savePreference = true) {
      activeRegionKey = regionKey;
      if (savePreference) {
        try { localStorage.setItem('roamai_selected_region', regionKey); } catch (e) {}
      }
      const selector = document.getElementById('navRegionSelector');
      if (selector && selector.value !== regionKey) {
        selector.value = regionKey;
      }
      const reg = REGIONS[regionKey] || REGIONS.INR;

      // Update Navbar Flag
      document.getElementById('navRegionFlag').innerText = reg.flag;

      // Update Banner
      document.getElementById('bannerFlag').innerText = reg.flag;
      document.getElementById('bannerRegionTitle').innerText = `Active Region: ${reg.name} (${reg.curr} ${reg.sym})`;
      document.getElementById('bannerRegionTip').innerText = reg.tip;

      // Update Planner Region Badge & Currency
      document.getElementById('activeRegionBadge').innerText = `${reg.flag} ${reg.curr} Active`;
      document.getElementById('plannerCurr').value = `${reg.curr} (${reg.sym})`;

      // Update Hotspot Cards Costs
      document.getElementById('hotspotTokyoCost').innerText = `💰 ~${reg.hotspots.tokyo} / day`;
      document.getElementById('hotspotBaliCost').innerText = `💰 ~${reg.hotspots.bali} / day`;
      document.getElementById('hotspotRomeCost').innerText = `💰 ~${reg.hotspots.rome} / day`;
      document.getElementById('hotspotAmsterdamCost').innerText = `💰 ~${reg.hotspots.amsterdam} / day`;
      document.getElementById('hotspotGoaCost').innerText = `💰 ~${reg.hotspots.goa} / day`;
      document.getElementById('hotspotKyotoCost').innerText = `💰 ~${reg.hotspots.kyoto} / day`;

      // Update Budget Calculator Inputs & Sliders
      document.getElementById('bCurrDisplay').value = `${reg.curr} (${reg.sym})`;
      
      const bTrans = document.getElementById('bTrans');
      const bStay = document.getElementById('bStay');
      const bFood = document.getElementById('bFood');
      const bAct = document.getElementById('bAct');
      const bBuf = document.getElementById('bBuf');

      bTrans.max = reg.defaults.maxTrans;
      bTrans.step = reg.defaults.step;
      bTrans.value = reg.defaults.trans;

      bStay.max = reg.defaults.maxStay;
      bStay.step = reg.defaults.step;
      bStay.value = reg.defaults.stay;

      bFood.max = reg.defaults.maxFood;
      bFood.step = reg.defaults.step;
      bFood.value = reg.defaults.food;

      bAct.max = reg.defaults.maxAct;
      bAct.step = reg.defaults.step;
      bAct.value = reg.defaults.act;

      bBuf.max = reg.defaults.maxBuf;
      bBuf.step = reg.defaults.step;
      bBuf.value = reg.defaults.buf;

      // Update Budget Tips
      document.getElementById('budgetRegionalTips').innerHTML = `
        <h4 class="font-bold text-amberAccent">💡 Student ${reg.name} Hacks:</h4>
        ${reg.budgetTips.map(t => `<p>${t}</p>`).join('')}
      `;

      calcBudget();
    }

    function switchPage(page, saveState = true) {
      activePage = page;
      if (saveState) {
        try {
          localStorage.setItem('roamai_active_page', page);
          history.replaceState(null, null, '#' + page);
        } catch (e) {}
      }
      ['home', 'planner', 'budget', 'packing', 'saved'].forEach(p => {
        const pageEl = document.getElementById(`page-${p}`);
        if (pageEl) pageEl.classList.toggle('hidden', p !== page);
        const t = document.getElementById(`tab-${p}`);
        if (t) t.classList.toggle('active', p === page);
        const m = document.getElementById(`mob-${p}`);
        if (m) {
          m.classList.toggle('text-coralPrimary', p === page);
          m.classList.toggle('font-bold', p === page);
        }
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
      const reg = REGIONS[activeRegionKey] || REGIONS.INR;
      const currency = reg.curr;
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
            currency, region: reg.name, interests: selectedInterests, must_visit: mustVisit, travel_pace: pace
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
      const reg = REGIONS[activeRegionKey] || REGIONS.INR;
      const sym = reg.sym;

      const days = parseInt(document.getElementById('bDays').value) || 1;
      const trans = parseFloat(document.getElementById('bTrans').value) || 0;
      const stay = parseFloat(document.getElementById('bStay').value) || 0;
      const food = parseFloat(document.getElementById('bFood').value) || 0;
      const act = parseFloat(document.getElementById('bAct').value) || 0;
      const buf = parseFloat(document.getElementById('bBuf').value) || 0;

      document.getElementById('bValTrans').innerText = `${sym}${trans.toLocaleString()}`;
      document.getElementById('bValStay').innerText = `${sym}${stay.toLocaleString()}/night`;
      document.getElementById('bValFood').innerText = `${sym}${food.toLocaleString()}/day`;
      document.getElementById('bValAct').innerText = `${sym}${act.toLocaleString()}/day`;
      document.getElementById('bValBuf').innerText = `${sym}${buf.toLocaleString()}`;

      const total = trans + (stay * Math.max(days - 1, 1)) + (food * days) + (act * days) + buf;
      document.getElementById('bTotal').innerText = `${sym}${Math.round(total).toLocaleString()}`;
      document.getElementById('bAvg').innerText = `Avg ${sym}${Math.round(total / days).toLocaleString()} / day`;
    }

    const packItems = [
      { id: 1, name: 'Passport & Student ID Card', checked: true },
      { id: 2, name: 'Zero-Forex Travel Card & Cash', checked: true },
      { id: 3, name: 'Universal Travel Power Adapter', checked: true },
      { id: 4, name: 'Power Bank (10,000mAh+)', checked: false },
      { id: 5, name: 'Comfortable Walking Sneakers', checked: true },
      { id: 6, name: 'Quick-dry Microfiber Hostel Towel', checked: false },
      { id: 7, name: 'First Aid Kit & Prescription Meds', checked: false }
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
      // 1. Restore saved region (prevent resetting to INR on reload)
      const savedRegion = localStorage.getItem('roamai_selected_region') || 'INR';
      onRegionChange(savedRegion, false);

      // 2. Restore saved active page (prevent automatically resetting to home on reload)
      const hashPage = window.location.hash.replace('#', '');
      const savedPage = hashPage || localStorage.getItem('roamai_active_page') || 'home';
      switchPage(savedPage, false);

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