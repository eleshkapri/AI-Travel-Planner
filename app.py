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

  <!-- Instant Pre-Paint Router & Theme Engine (Executes BEFORE styles/DOM to guarantee ZERO reload flicker) -->
  <script>
    (function() {
      try {
        var savedTheme = localStorage.getItem('roamai_theme');
        var isLight = savedTheme ? (savedTheme === 'light') : (window.matchMedia && window.matchMedia('(prefers-color-scheme: light)').matches);
        if (isLight) {
          document.documentElement.classList.add('light-theme');
        }

        var rawHash = window.location.hash ? window.location.hash.replace('#', '') : (localStorage.getItem('roamai_active_page') || 'home');
        var validPages = ['home', 'planner', 'budget', 'packing', 'saved'];
        var activePage = validPages.indexOf(rawHash) !== -1 ? rawHash : 'home';
        document.documentElement.setAttribute('data-active-page', activePage);
      } catch(e) {}
    })();
  </script>

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
    html {
      background-color: #080C14;
    }
    html.light-theme {
      background-color: #EEF4FB !important;
    }
    body {
      background-color: #080C14;
      color: #F3F4F6;
      font-family: 'Plus Jakarta Sans', sans-serif;
      overflow-x: hidden;
    }
    html.light-theme body,
    body.light-theme {
      background-color: #EEF4FB !important;
      color: #0B132B !important;
    }

    /* ========================================================
       STUDENTFIT-STYLE MODERN INSET PILL SCROLLBAR
       ======================================================== */
    /* Firefox */
    * {
      scrollbar-width: thin;
      scrollbar-color: #374151 #080C14;
    }
    html.light-theme * {
      scrollbar-color: #94A3B8 #EEF4FB;
    }

    /* WebKit (Chrome, Edge, Safari, Brave, Opera) */
    ::-webkit-scrollbar {
      width: 10px;
      height: 10px;
    }
    ::-webkit-scrollbar-track {
      background: #080C14;
    }
    html.light-theme ::-webkit-scrollbar-track {
      background: #EEF4FB;
    }
    ::-webkit-scrollbar-thumb {
      background-color: #374151;
      border-radius: 9999px;
      border: 3px solid #080C14;
      background-clip: padding-box;
      transition: background-color 0.2s ease;
    }
    ::-webkit-scrollbar-thumb:hover {
      background-color: #FF5E36;
    }
    ::-webkit-scrollbar-corner {
      background: #080C14;
    }

    /* Light Theme Inset Pill */
    html.light-theme ::-webkit-scrollbar-thumb {
      background-color: #94A3B8;
      border: 3px solid #EEF4FB;
      background-clip: padding-box;
    }
    html.light-theme ::-webkit-scrollbar-thumb:hover {
      background-color: #FF5E36;
    }
    html.light-theme ::-webkit-scrollbar-corner {
      background: #EEF4FB;
    }

    /* Pre-Paint Instant Zero-Flicker Page View Router */
    html[data-active-page="home"] #page-home { display: block !important; }
    html[data-active-page="home"] #page-planner,
    html[data-active-page="home"] #page-budget,
    html[data-active-page="home"] #page-packing,
    html[data-active-page="home"] #page-saved { display: none !important; }

    html[data-active-page="planner"] #page-home { display: none !important; }
    html[data-active-page="planner"] #page-planner { display: block !important; }

    html[data-active-page="budget"] #page-home { display: none !important; }
    html[data-active-page="budget"] #page-budget { display: block !important; }

    html[data-active-page="packing"] #page-home { display: none !important; }
    html[data-active-page="packing"] #page-packing { display: block !important; }

    html[data-active-page="saved"] #page-home { display: none !important; }
    html[data-active-page="saved"] #page-saved { display: block !important; }

    /* Instant CSS Theme Icon Indicator (Zero-Flicker Synchronous Rendering) */
    .theme-icon::before {
      content: '🌙';
    }
    html.light-theme .theme-icon::before {
      content: '☀️';
    }

    /* Ambient Floating Orbs */
    @keyframes floatOrb1 {
      0%, 100% { transform: translate(0px, 0px) scale(1); }
      50% { transform: translate(70px, 50px) scale(1.2); }
    }
    @keyframes floatOrb2 {
      0%, 100% { transform: translate(0px, 0px) scale(1); }
      50% { transform: translate(-60px, 70px) scale(1.25); }
    }
    @keyframes floatOrb3 {
      0%, 100% { transform: translate(0px, 0px) scale(1); }
      50% { transform: translate(50px, -60px) scale(0.9); }
    }
    @keyframes pulseGlow {
      0%, 100% { opacity: 0.5; transform: scale(1); }
      50% { opacity: 0.9; transform: scale(1.05); }
    }
    @keyframes textShimmer {
      0% { background-position: 0% 50%; }
      50% { background-position: 100% 50%; }
      100% { background-position: 0% 50%; }
    }
    @keyframes badgePulse {
      0%, 100% { box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.4); }
      70% { box-shadow: 0 0 0 10px rgba(16, 185, 129, 0); }
    }

    .animate-text-shimmer {
      background-size: 200% auto;
      animation: textShimmer 4s ease infinite;
    }

    .orb-1 {
      position: fixed; top: -10%; left: -8%; width: 55vw; height: 55vw;
      background: radial-gradient(circle, rgba(255, 94, 54, 0.22) 0%, transparent 65%);
      filter: blur(70px); z-index: 0; pointer-events: none;
      animation: floatOrb1 18s ease-in-out infinite;
    }
    .orb-2 {
      position: fixed; top: 20%; right: -12%; width: 50vw; height: 50vw;
      background: radial-gradient(circle, rgba(6, 182, 212, 0.18) 0%, transparent 65%);
      filter: blur(80px); z-index: 0; pointer-events: none;
      animation: floatOrb2 22s ease-in-out infinite;
    }
    .orb-3 {
      position: fixed; bottom: -15%; left: 20%; width: 60vw; height: 60vw;
      background: radial-gradient(circle, rgba(139, 92, 246, 0.20) 0%, transparent 65%);
      filter: blur(90px); z-index: 0; pointer-events: none;
      animation: floatOrb3 20s ease-in-out infinite;
    }
    .travel-sky-pattern {
      position: fixed; inset: 0; z-index: 0; pointer-events: none;
      background: radial-gradient(circle at 20% 15%, rgba(255, 94, 54, 0.08) 0%, transparent 50%),
                  radial-gradient(circle at 85% 30%, rgba(6, 182, 212, 0.08) 0%, transparent 45%),
                  radial-gradient(circle at 50% 80%, rgba(255, 160, 0, 0.06) 0%, transparent 60%);
    }

    .glass-card {
      background: linear-gradient(135deg, rgba(255, 255, 255, 0.04) 0%, rgba(255, 255, 255, 0.01) 100%), rgba(14, 20, 32, 0.82);
      backdrop-filter: blur(20px);
      -webkit-backdrop-filter: blur(20px);
      border: 1px solid rgba(255, 255, 255, 0.09);
      box-shadow: 0 15px 35px rgba(0, 0, 0, 0.45), inset 0 1px 0 rgba(255, 255, 255, 0.12);
      transition: all 0.35s cubic-bezier(0.16, 1, 0.3, 1);
    }
    .glass-card:hover {
      border-color: rgba(255, 94, 54, 0.4);
      box-shadow: 0 20px 45px rgba(255, 94, 54, 0.15), inset 0 1px 0 rgba(255, 255, 255, 0.2);
      transform: translateY(-4px);
    }
    .btn-gradient {
      background: linear-gradient(135deg, #FF5E36 0%, #FFA000 100%);
      color: #FFFFFF;
      font-weight: 700;
      transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
      box-shadow: 0 6px 25px rgba(255, 94, 54, 0.35);
    }
    .btn-gradient:hover {
      transform: translateY(-2px) scale(1.02);
      box-shadow: 0 10px 30px rgba(255, 94, 54, 0.55);
    }
    .btn-secondary {
      background: rgba(255, 255, 255, 0.06);
      border: 1px solid rgba(255, 255, 255, 0.12);
      color: #E5E7EB;
      transition: all 0.2s ease;
    }
    .btn-secondary:hover {
      background: rgba(255, 255, 255, 0.12);
      border-color: rgba(255, 255, 255, 0.25);
      color: #FFFFFF;
      transform: translateY(-1px);
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
      box-shadow: 0 0 12px #FF5E36;
    }
    .chip-tag {
      cursor: pointer;
      user-select: none;
      transition: all 0.2s ease;
      background: rgba(255, 255, 255, 0.04);
      border: 1px solid rgba(255, 255, 255, 0.1);
    }
    .chip-tag.active {
      background: linear-gradient(135deg, rgba(255, 94, 54, 0.25), rgba(255, 160, 0, 0.25));
      border-color: #FF5E36;
      color: #FFA000;
      font-weight: 600;
    }
    #map {
      height: 100%;
      min-height: 420px;
      width: 100%;
      border-radius: 1.25rem;
      z-index: 1;
    }
    .itinerary-prose h1 {
      font-size: 1.75rem;
      font-weight: 800;
      color: #FF5E36;
      line-height: 1.35;
      margin-top: 0.5rem;
      margin-bottom: 1.25rem;
      word-break: break-word;
    }
    .itinerary-prose h2 {
      font-size: 1.35rem;
      font-weight: 700;
      color: #FFA000;
      line-height: 1.4;
      margin-top: 1.75rem;
      margin-bottom: 0.85rem;
      word-break: break-word;
    }
    .itinerary-prose h3 {
      font-size: 1.15rem;
      font-weight: 600;
      color: #06B6D4;
      line-height: 1.45;
      margin-top: 1.35rem;
      margin-bottom: 0.6rem;
      word-break: break-word;
    }
    .itinerary-prose p {
      margin-bottom: 0.85rem;
      line-height: 1.75;
      color: #D1D5DB;
      font-size: 0.925rem;
    }
    .itinerary-prose ul {
      list-style: none;
      padding-left: 0;
      margin-bottom: 1.15rem;
    }
    .itinerary-prose li {
      position: relative;
      padding-left: 1.5rem;
      margin-bottom: 0.6rem;
      line-height: 1.65;
      color: #E5E7EB;
      font-size: 0.925rem;
    }
    .itinerary-prose li::before {
      content: '✦';
      position: absolute;
      left: 0;
      color: #FF5E36;
    }
    .itinerary-prose strong {
      color: #FFFFFF;
      font-weight: 700;
    }
    .itinerary-prose table {
      width: 100%;
      border-collapse: separate;
      border-spacing: 0;
      margin: 1.25rem 0;
      font-size: 0.85rem;
      border-radius: 0.85rem;
      overflow: hidden;
      border: 1px solid rgba(255, 255, 255, 0.1);
    }
    .itinerary-prose th {
      background: rgba(255, 255, 255, 0.08);
      color: #FFA000;
      font-weight: 700;
      text-align: left;
      padding: 0.75rem 1rem;
      border-bottom: 1px solid rgba(255, 255, 255, 0.1);
    }
    .itinerary-prose td {
      padding: 0.75rem 1rem;
      border-bottom: 1px solid rgba(255, 255, 255, 0.05);
      color: #E5E7EB;
    }
    .itinerary-prose tr:last-child td {
      border-bottom: none;
    }
    .itinerary-prose blockquote {
      border-left: 3px solid #FF5E36;
      padding-left: 1rem;
      margin: 1rem 0;
      color: #9CA3AF;
      font-style: italic;
    }

    /* ========================================================
       PREMIUM LIGHT THEME (VIBRANT MORNING SKY & CELESTIAL MIST)
       ======================================================== */
    html.light-theme,
    body.light-theme {
      background-color: #EEF4FB;
      color: #0B132B;
    }
    /* ========================================================
       TRANSLUCENT FROSTED GLASS HEADER & SCROLL DYNAMICS
       ======================================================== */
    header {
      background-color: rgba(11, 15, 25, 0.75) !important;
      backdrop-filter: blur(20px) saturate(180%);
      -webkit-backdrop-filter: blur(20px) saturate(180%);
      border-bottom: 1px solid rgba(255, 255, 255, 0.08);
      box-shadow: 0 4px 30px rgba(0, 0, 0, 0.25);
      transition: transform 0.45s cubic-bezier(0.16, 1, 0.3, 1), opacity 0.35s ease, background-color 0.3s ease, box-shadow 0.35s ease;
      will-change: transform;
    }
    header.nav-hidden {
      transform: translateY(-110%);
      opacity: 0;
      pointer-events: none;
    }
    header.nav-scrolled {
      box-shadow: 0 20px 40px -10px rgba(0, 0, 0, 0.5);
    }
    .light-theme header {
      background-color: rgba(255, 255, 255, 0.78) !important;
      backdrop-filter: blur(20px) saturate(180%);
      -webkit-backdrop-filter: blur(20px) saturate(180%);
      border-bottom-color: rgba(203, 213, 225, 0.65) !important;
      box-shadow: 0 4px 25px rgba(11, 19, 43, 0.05);
    }
    .light-theme header.nav-scrolled {
      box-shadow: 0 20px 40px -10px rgba(11, 19, 43, 0.10);
    }
    .brand-logo-title {
      background: linear-gradient(135deg, #FFFFFF 0%, #F3F4F6 50%, #FF5E36 100%);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
    }
    .light-theme .brand-logo-title {
      background: linear-gradient(135deg, #0B132B 0%, #1E293B 40%, #FF5E36 100%);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
    }
    .light-theme .glass-card {
      background: linear-gradient(135deg, rgba(255, 255, 255, 0.92) 0%, rgba(255, 255, 255, 0.82) 100%);
      backdrop-filter: blur(16px);
      -webkit-backdrop-filter: blur(16px);
      border: 1px solid #E2E8F0;
      box-shadow: 0 15px 35px -10px rgba(11, 19, 43, 0.07), 0 0 0 1px rgba(226, 232, 240, 0.8);
    }
    .light-theme .glass-card:hover {
      border-color: rgba(255, 94, 54, 0.5);
      box-shadow: 0 20px 40px -10px rgba(255, 94, 54, 0.15), 0 0 0 1px rgba(255, 94, 54, 0.3);
      transform: translateY(-4px);
    }
    
    /* Light Theme Typography & Global High Contrast */
    .light-theme h1,
    .light-theme h2,
    .light-theme h3,
    .light-theme h4,
    .light-theme h5 {
      color: #0F172A !important;
    }
    .light-theme p {
      color: #334155;
    }
    .light-theme label {
      color: #1E293B !important;
      font-weight: 600;
    }
    .light-theme .text-white {
      color: #0F172A !important;
    }
    .light-theme .text-gray-300 {
      color: #334155 !important;
    }
    .light-theme .text-gray-400 {
      color: #64748B !important;
    }
    .light-theme .text-gray-200 {
      color: #1E293B !important;
    }
    .light-theme .text-coralPrimary {
      color: #EA580C !important;
    }
    .light-theme .text-amberAccent {
      color: #D97706 !important;
    }
    .light-theme .text-cyanAccent {
      color: #0284C7 !important;
    }
    .light-theme .text-emeraldAccent {
      color: #059669 !important;
    }

    /* Floating Image Badges & Gradient Buttons ALWAYS keep pure white & bright gold text */
    .light-theme [class*="bg-spaceDark/80"],
    .light-theme [class*="bg-black/60"],
    .light-theme [class*="bg-spaceDark/80"] *,
    .light-theme [class*="bg-black/60"] *,
    .light-theme .btn-gradient,
    .light-theme .btn-gradient * {
      color: #FFFFFF !important;
    }
    .light-theme [class*="bg-spaceDark/80"] {
      background-color: rgba(11, 15, 25, 0.82) !important;
      border-color: rgba(255, 255, 255, 0.20) !important;
    }
    .light-theme [class*="bg-black/60"] {
      background-color: rgba(0, 0, 0, 0.70) !important;
      border-color: rgba(255, 255, 255, 0.15) !important;
    }
    .light-theme [class*="bg-black/60"].text-amberAccent,
    .light-theme [class*="bg-spaceDark/80"].text-amberAccent {
      color: #FFA000 !important;
    }

    /* Light Theme Map Placeholder & Frame Fix */
    .light-theme .map-frame-box,
    .light-theme #mapPlaceholder {
      background: linear-gradient(135deg, #F8FAFC 0%, #EEF2F6 100%) !important;
      border-color: #CBD5E1 !important;
    }
    .light-theme #mapPlaceholder h4 {
      color: #0F172A !important;
      font-weight: 800;
    }
    .light-theme #mapPlaceholder p {
      color: #475569 !important;
    }
    .light-theme .map-pill-badge {
      background-color: #FFFFFF !important;
      border-color: #CBD5E1 !important;
      box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
    }
    .light-theme .map-pill-badge span {
      color: #0F172A !important;
      font-weight: 700;
    }
    .light-theme #plannerPlaceholder {
      background: linear-gradient(135deg, rgba(255, 255, 255, 0.95) 0%, rgba(248, 250, 252, 0.95) 100%) !important;
      border-color: #E2E8F0 !important;
    }
    .light-theme #plannerPlaceholder h3 {
      color: #0F172A !important;
    }
    .light-theme #plannerPlaceholder p {
      color: #475569 !important;
    }

    .light-theme .bg-spaceDark {
      background-color: rgba(255, 255, 255, 0.92) !important;
    }
    .light-theme .bg-cardDark {
      background-color: rgba(241, 245, 249, 0.92) !important;
    }
    .light-theme [class*="border-white/10"],
    .light-theme [class*="border-white/5"],
    .light-theme .border-cardBorder {
      border-color: #E2E8F0 !important;
    }
    .light-theme input,
    .light-theme select {
      background-color: #FFFFFF !important;
      color: #0B132B !important;
      border-color: #CBD5E1 !important;
      box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
    }
    .light-theme input::placeholder {
      color: #94A3B8 !important;
    }
    .light-theme input:focus,
    .light-theme select:focus {
      border-color: #FF5E36 !important;
      box-shadow: 0 0 0 3px rgba(255, 94, 54, 0.15);
    }
    .light-theme .btn-secondary {
      background: #FFFFFF;
      border-color: #CBD5E1;
      color: #1E293B;
      box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
    }
    .light-theme .btn-secondary:hover {
      background: #F8FAFC;
      border-color: #94A3B8;
      color: #0B132B;
    }
    .light-theme .chip-tag {
      background: #F1F5F9;
      border-color: #E2E8F0;
      color: #334155;
    }
    .light-theme .chip-tag.active {
      background: linear-gradient(135deg, rgba(255, 94, 54, 0.15), rgba(255, 160, 0, 0.15));
      border-color: #FF5E36;
      color: #C2410C;
      font-weight: 700;
    }
    .light-theme .hero-badge {
      background: #FFFFFF !important;
      border-color: #E2E8F0 !important;
      color: #0B132B !important;
      box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
    }
    .light-theme #regionInfoBanner {
      background: linear-gradient(135deg, rgba(255, 94, 54, 0.08), rgba(2, 132, 199, 0.08)) !important;
      border-color: rgba(255, 94, 54, 0.3) !important;
    }
    .light-theme #bannerRegionTitle {
      color: #C2410C !important;
    }
    .light-theme #bannerRegionTip {
      color: #475569 !important;
    }
    .light-theme .itinerary-prose {
      background-color: rgba(255, 255, 255, 0.95) !important;
      border-color: #E2E8F0 !important;
      box-shadow: 0 10px 30px rgba(0, 0, 0, 0.04);
    }
    .light-theme .itinerary-prose p {
      color: #334155;
    }
    .light-theme .itinerary-prose li {
      color: #1E293B;
    }
    .light-theme .itinerary-prose strong {
      color: #0B132B;
    }
    .light-theme .itinerary-prose table {
      border-color: #E2E8F0;
    }
    .light-theme .itinerary-prose th {
      background: #F8FAFC;
      color: #C2410C;
      border-bottom: 2px solid #E2E8F0;
    }
    .light-theme .itinerary-prose td {
      border-bottom-color: #F1F5F9;
      color: #1E293B;
    }
    .light-theme #themeToggleBtn {
      background-color: #FFFFFF;
      border-color: #CBD5E1;
      color: #0B132B;
    }
    .light-theme #navRegionSelector {
      background-color: #FFFFFF !important;
      color: #0B132B !important;
      border-color: #CBD5E1 !important;
    }
    .light-theme .nav-tab {
      color: #475569 !important;
    }
    .light-theme .nav-tab:hover {
      color: #FF5E36 !important;
    }
    .light-theme .nav-tab.active {
      color: #FF5E36 !important;
    }
    .light-theme #mob-home,
    .light-theme #mob-planner,
    .light-theme #mob-budget,
    .light-theme #mob-packing,
    .light-theme #mob-saved {
      color: #475569;
    }
    .light-theme .travel-sky-pattern {
      background: radial-gradient(circle at 15% 15%, rgba(255, 94, 54, 0.12) 0%, transparent 55%),
                  radial-gradient(circle at 85% 25%, rgba(2, 132, 199, 0.14) 0%, transparent 50%),
                  radial-gradient(circle at 50% 85%, rgba(245, 158, 11, 0.10) 0%, transparent 60%);
    }
    .light-theme .orb-1 {
      background: radial-gradient(circle, rgba(255, 94, 54, 0.18) 0%, transparent 65%);
    }
    .light-theme .orb-2 {
      background: radial-gradient(circle, rgba(2, 132, 199, 0.18) 0%, transparent 65%);
    }
    .light-theme .orb-3 {
      background: radial-gradient(circle, rgba(245, 158, 11, 0.15) 0%, transparent 65%);
    }
  </style>
</head>
<body class="min-h-screen flex flex-col antialiased relative">
  <!-- Dynamic Animated Wanderlust Sky Canvas, Floating Ambient Glow & Travel Texture -->
  <canvas id="bgParticleCanvas" class="fixed inset-0 pointer-events-none" style="z-index: 1;"></canvas>
  <div class="orb-1"></div>
  <div class="orb-2"></div>
  <div class="orb-3"></div>
  <div class="travel-sky-pattern"></div>

  <!-- ==================== PROPERLY DESIGNED NAVBAR WITH REGION SELECTOR ==================== -->
  <header id="mainHeader" class="sticky top-0 z-50 backdrop-blur-xl border-b border-cardBorder shadow-2xl">
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
            <span class="text-xl font-extrabold tracking-tight brand-logo-title">RoamAI</span>
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

      <!-- Theme Switcher, Region Selector & CTA (Right) -->
      <div class="flex items-center gap-2.5 shrink-0">
        
        <!-- Theme Mood Switcher (Dark / Light) -->
        <button
          id="themeToggleBtn"
          onclick="toggleThemeMood()"
          class="w-9 h-9 rounded-xl bg-cardDark/90 border border-white/15 hover:border-coralPrimary/50 flex items-center justify-center text-sm text-gray-300 hover:text-white transition shadow-sm"
          title="Toggle Light / Dark Mode"
          aria-label="Toggle Theme Mood"
        >
          <span id="themeToggleIcon" class="theme-icon inline-block"></span>
        </button>

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
      <button onclick="toggleThemeMood()" class="flex flex-col items-center"><span id="mobThemeToggleIcon" class="theme-icon inline-block"></span>Mood</button>
    </div>
  </header>

  <!-- ==================== MAIN CONTENT ==================== -->
  <main class="flex-grow max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8 relative" style="z-index: 10;">

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
    <section id="page-home" class="space-y-20">
      
      <!-- HERO SECTION WITH 3D DEPTH & PREVIEW WIDGET -->
      <div class="relative rounded-3xl overflow-hidden glass-card p-8 sm:p-12 lg:p-14 border border-white/15 shadow-2xl">
        <div class="grid grid-cols-1 lg:grid-cols-12 gap-10 items-center">
          
          <!-- Hero Left Column -->
          <div class="lg:col-span-7 space-y-6">
            <div class="inline-flex items-center gap-2.5 px-4 py-1.5 rounded-full bg-white/5 border border-white/10 text-xs font-semibold text-amberAccent shadow-inner">
              <span class="w-2 h-2 rounded-full bg-emeraldAccent animate-ping"></span>
              <span class="text-white">Next-Gen Student Travel Architect</span>
              <span class="text-gray-400">•</span>
              <span>Sub-Second AI Engine</span>
            </div>

            <h1 class="text-4xl sm:text-5xl lg:text-6xl font-extrabold tracking-tight text-white leading-[1.15]">
              Plan Epic Student Adventures <br/>
              <span class="bg-clip-text text-transparent bg-gradient-to-r from-coralPrimary via-amberAccent to-cyanAccent animate-text-shimmer">
                On Any Budget in Seconds.
              </span>
            </h1>

            <p class="text-gray-300 text-sm sm:text-base leading-relaxed max-w-xl">
              Day-by-day itineraries, verified local student discounts, interactive 3D map pins, and offline PDF exports powered by high-speed Groq AI.
            </p>

            <!-- Quick Search Input & CTA -->
            <div class="pt-2 space-y-3">
              <div class="flex flex-col sm:flex-row gap-3 max-w-xl">
                <input
                  type="text"
                  id="heroDestInput"
                  placeholder="Where to? (e.g. Tokyo, Bali, Rome, Goa, Manali)"
                  class="flex-grow px-5 py-4 bg-spaceDark/90 border border-white/20 hover:border-coralPrimary/50 rounded-2xl text-sm text-white placeholder-gray-500 focus:outline-none focus:border-coralPrimary shadow-inner transition"
                  onkeypress="if(event.key === 'Enter') startQuickTrip()"
                />
                <button onclick="startQuickTrip()" class="btn-gradient px-8 py-4 rounded-2xl text-sm font-bold flex items-center justify-center gap-2 whitespace-nowrap shadow-xl">
                  <span>🚀 Start Planning</span>
                </button>
              </div>

              <!-- Quick Trending Chips -->
              <div class="flex flex-wrap items-center gap-2 pt-1">
                <span class="text-xs text-gray-400 font-semibold flex items-center gap-1">🔥 Trending:</span>
                <button onclick="quickPlanHotspot('Tokyo, Japan', 4, 'Student (Low)', ['Street Food', 'Anime & Pop Culture', 'History'])" class="text-xs px-2.5 py-1 rounded-lg bg-white/5 hover:bg-white/10 text-gray-300 hover:text-white border border-white/10 transition">Tokyo 🗼</button>
                <button onclick="quickPlanHotspot('Bali, Indonesia', 5, 'Student (Low)', ['Nature', 'Beaches', 'Adventure'])" class="text-xs px-2.5 py-1 rounded-lg bg-white/5 hover:bg-white/10 text-gray-300 hover:text-white border border-white/10 transition">Bali 🌴</button>
                <button onclick="quickPlanHotspot('Amsterdam, Netherlands', 3, 'Student (Low)', ['Nightlife', 'Museums', 'Street Food'])" class="text-xs px-2.5 py-1 rounded-lg bg-white/5 hover:bg-white/10 text-gray-300 hover:text-white border border-white/10 transition">Amsterdam 🚲</button>
                <button onclick="quickPlanHotspot('Goa, India', 4, 'Student (Low)', ['Nightlife', 'Beaches', 'Street Food'])" class="text-xs px-2.5 py-1 rounded-lg bg-white/5 hover:bg-white/10 text-gray-300 hover:text-white border border-white/10 transition">Goa 🏖️</button>
                <button onclick="quickPlanHotspot('Kyoto, Japan', 3, 'Student (Low)', ['History', 'Nature', 'Street Food'])" class="text-xs px-2.5 py-1 rounded-lg bg-white/5 hover:bg-white/10 text-gray-300 hover:text-white border border-white/10 transition">Kyoto ⛩️</button>
              </div>
            </div>

            <!-- Trust Stats Row -->
            <div class="pt-6 grid grid-cols-3 gap-6 border-t border-white/10 max-w-lg">
              <div>
                <p class="text-2xl sm:text-3xl font-extrabold text-white">50,000+</p>
                <p class="text-xs text-gray-400 font-medium">Trips Planned</p>
              </div>
              <div>
                <p class="text-2xl sm:text-3xl font-extrabold text-coralPrimary">120+</p>
                <p class="text-xs text-gray-400 font-medium">Countries Mapped</p>
              </div>
              <div>
                <p class="text-2xl sm:text-3xl font-extrabold text-cyanAccent">100% Free</p>
                <p class="text-xs text-gray-400 font-medium">For All Students</p>
              </div>
            </div>
          </div>

          <!-- Hero Right Column: 3D Floating Interactive Preview Widget -->
          <div class="lg:col-span-5 flex justify-center">
            <div class="w-full max-w-sm glass-card p-6 rounded-3xl border border-white/20 shadow-2xl space-y-4 transform lg:rotate-1 hover:rotate-0 transition duration-500" data-tilt data-tilt-max="10">
              <div class="relative rounded-2xl overflow-hidden aspect-video">
                <img src="https://images.unsplash.com/photo-1503899036084-c55cdd92da26?auto=format&fit=crop&w=600&q=80" class="w-full h-full object-cover" />
                <div class="absolute inset-0 bg-gradient-to-t from-black/80 via-black/20 to-transparent"></div>
                <div class="absolute top-3 left-3 px-2.5 py-1 rounded-full bg-spaceDark/80 backdrop-blur-md text-[10px] font-bold text-amberAccent border border-white/10 flex items-center gap-1.5">
                  <span class="w-1.5 h-1.5 rounded-full bg-amberAccent"></span> Live Itinerary Preview
                </div>
                <div class="absolute bottom-3 left-3 right-3 flex justify-between items-end">
                  <div>
                    <h4 class="text-sm font-bold text-white">Tokyo, Japan</h4>
                    <p class="text-[11px] text-gray-300">3 Days • Student Low Budget</p>
                  </div>
                  <span class="text-xs font-extrabold px-2 py-1 rounded-lg bg-coralPrimary/90 text-white shadow">~₹4,000 / day</span>
                </div>
              </div>

              <!-- Mini Timeline Steps -->
              <div class="space-y-2 text-xs">
                <div class="p-2.5 rounded-xl bg-white/5 border border-white/5 flex items-center justify-between">
                  <div class="flex items-center gap-2">
                    <span class="text-base">🍜</span>
                    <span class="text-gray-300 font-medium">Day 1: Shibuya Crossing & Ramen Alley</span>
                  </div>
                  <span class="text-[10px] text-emeraldAccent font-bold">Free Walk</span>
                </div>
                <div class="p-2.5 rounded-xl bg-white/5 border border-white/5 flex items-center justify-between">
                  <div class="flex items-center gap-2">
                    <span class="text-base">🏯</span>
                    <span class="text-gray-300 font-medium">Day 2: Senso-ji & Akihabara Tech</span>
                  </div>
                  <span class="text-[10px] text-cyanAccent font-bold">Transit Pass</span>
                </div>
              </div>

              <button onclick="quickPlanHotspot('Tokyo, Japan', 3, 'Student (Low)', ['Street Food', 'Anime', 'History'])" class="w-full btn-gradient py-2.5 rounded-xl text-xs font-bold flex items-center justify-center gap-1.5 shadow-lg">
                <span>⚡ Load This Trip into Planner →</span>
              </button>
            </div>
          </div>

        </div>
      </div>

      <!-- HOTSPOT CARDS WITH NATIONAL / INTERNATIONAL CLASSIFICATION & CATEGORY FILTER TABS -->
      <div class="space-y-8">
        <div class="flex flex-col lg:flex-row lg:items-end justify-between gap-6 pb-2 border-b border-white/10">
          <div class="space-y-1">
            <div class="flex items-center gap-2">
              <span class="text-xs font-bold uppercase tracking-wider text-coralPrimary">Curated For Students</span>
              <span class="text-[10px] font-extrabold px-2.5 py-0.5 rounded-full bg-emeraldAccent/20 text-emeraldAccent border border-emeraldAccent/30">16 Destinations</span>
            </div>
            <h2 class="text-2xl sm:text-3xl font-extrabold text-white">🔥 Trending Student Destinations</h2>
            <p class="text-gray-400 text-xs sm:text-sm">Classified by National (India) and International hotspots with auto-converting student budgets.</p>
          </div>

          <!-- Scope & Theme Filters -->
          <div class="flex flex-col sm:flex-row sm:items-center gap-3">
            <!-- National vs International Scope Toggle -->
            <div class="p-1 rounded-full bg-white/5 border border-white/10 flex items-center gap-1 shadow-inner">
              <button
                type="button"
                data-scope="all"
                onclick="setHotspotScope('all')"
                class="hotspot-scope-btn active text-xs px-4 py-2 rounded-full border border-transparent bg-gradient-to-r from-coralPrimary to-amberAccent text-white font-extrabold transition shadow-md flex items-center gap-1.5"
              >
                <span>🌍</span> All (16)
              </button>
              <button
                type="button"
                data-scope="national"
                onclick="setHotspotScope('national')"
                class="hotspot-scope-btn text-xs px-4 py-2 rounded-full border border-white/10 bg-white/5 text-gray-300 hover:text-white hover:border-white/20 transition flex items-center gap-1.5"
              >
                <span>🇮🇳</span> National (8)
              </button>
              <button
                type="button"
                data-scope="international"
                onclick="setHotspotScope('international')"
                class="hotspot-scope-btn text-xs px-4 py-2 rounded-full border border-white/10 bg-white/5 text-gray-300 hover:text-white hover:border-white/20 transition flex items-center gap-1.5"
              >
                <span>✈️</span> International (8)
              </button>
            </div>
          </div>
        </div>

        <!-- Secondary Theme Filter Pills -->
        <div class="flex flex-wrap items-center gap-2" id="hotspotFilterPills">
          <span class="text-xs font-bold text-gray-400 mr-1 flex items-center gap-1"><span>✨</span> Vibe:</span>
          <button type="button" data-cat="all" onclick="setHotspotCategory('all')" class="hotspot-filter-btn active text-xs px-3.5 py-1.5 rounded-full border border-transparent bg-white/20 text-white font-bold transition shadow-sm">All Vibes</button>
          <button type="button" data-cat="beach" onclick="setHotspotCategory('beach')" class="hotspot-filter-btn text-xs px-3.5 py-1.5 rounded-full border border-white/10 bg-white/5 text-gray-400 hover:text-white transition">🏖️ Beach & Coastal</button>
          <button type="button" data-cat="mountain" onclick="setHotspotCategory('mountain')" class="hotspot-filter-btn text-xs px-3.5 py-1.5 rounded-full border border-white/10 bg-white/5 text-gray-400 hover:text-white transition">🏔️ Mountains & Trekking</button>
          <button type="button" data-cat="culture" onclick="setHotspotCategory('culture')" class="hotspot-filter-btn text-xs px-3.5 py-1.5 rounded-full border border-white/10 bg-white/5 text-gray-400 hover:text-white transition">🏛️ History & Culture</button>
          <button type="button" data-cat="nightlife" onclick="setHotspotCategory('nightlife')" class="hotspot-filter-btn text-xs px-3.5 py-1.5 rounded-full border border-white/10 bg-white/5 text-gray-400 hover:text-white transition">🎉 Nightlife & Food</button>
          <button type="button" data-cat="adventure" onclick="setHotspotCategory('adventure')" class="hotspot-filter-btn text-xs px-3.5 py-1.5 rounded-full border border-white/10 bg-white/5 text-gray-400 hover:text-white transition">⚡ Adventure & Nature</button>
        </div>

        <!-- HOTSPOT CARDS GRID -->
        <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6" id="hotspotCardsGrid">
          
          <!-- ============================================ -->
          <!-- 🇮🇳 NATIONAL DESTINATIONS (DOMESTIC INDIA) -->
          <!-- ============================================ -->

          <!-- 1. Goa -->
          <div class="hotspot-card glass-card rounded-3xl p-5 space-y-4 cursor-pointer group flex flex-col justify-between" data-scope="national" data-cat="beach nightlife" data-cost-inr="2000" data-tilt data-tilt-max="6" onclick="quickPlanHotspot('Goa, India', 4, 'Student (Low)', ['Nightlife', 'Beaches', 'Street Food'])">
            <div class="space-y-3">
              <div class="relative rounded-2xl overflow-hidden h-44">
                <img src="https://images.unsplash.com/photo-1512343879784-a960bf40e7f2?auto=format&fit=crop&w=600&q=80" alt="Goa Beaches" class="w-full h-full object-cover group-hover:scale-105 transition duration-500" />
                <span class="absolute top-3 left-3 px-2.5 py-1 rounded-full bg-spaceDark/85 backdrop-blur-md text-[10px] font-extrabold text-emeraldAccent border border-emeraldAccent/30 flex items-center gap-1">🇮🇳 National</span>
                <span class="absolute top-3 right-3 px-2 py-0.5 rounded-full bg-black/60 backdrop-blur-md text-[10px] font-bold text-amberAccent">⭐ 4.9</span>
              </div>
              <div>
                <div class="flex items-center gap-2">
                  <span class="text-[10px] font-bold px-2 py-0.5 rounded-md bg-emeraldAccent/20 text-emeraldAccent border border-emeraldAccent/30">Coastal Shacks & Parties</span>
                </div>
                <h3 class="text-base font-bold text-white group-hover:text-coralPrimary transition mt-1.5">Goa, India</h3>
                <p class="text-xs text-gray-400 mt-1 leading-relaxed">Sun-kissed beaches, night flea markets, sunset cruise parties, and affordable student shacks.</p>
              </div>
            </div>
            <div class="flex justify-between items-center pt-3 border-t border-white/10">
              <span class="text-xs font-bold text-emeraldAccent hotspot-cost-val">💰 ~₹2,000 / day</span>
              <span class="text-xs font-bold text-coralPrimary flex items-center gap-1 group-hover:translate-x-1 transition">Plan Trip →</span>
            </div>
          </div>

          <!-- 2. Manali & Kasol -->
          <div class="hotspot-card glass-card rounded-3xl p-5 space-y-4 cursor-pointer group flex flex-col justify-between" data-scope="national" data-cat="mountain adventure nature" data-cost-inr="1800" data-tilt data-tilt-max="6" onclick="quickPlanHotspot('Manali, Himachal Pradesh, India', 4, 'Student (Low)', ['Nature', 'Adventure', 'Hiking'])">
            <div class="space-y-3">
              <div class="relative rounded-2xl overflow-hidden h-44">
                <img src="https://images.unsplash.com/photo-1626621341517-bbf3d9990a23?auto=format&fit=crop&w=600&q=80" alt="Manali Mountains" class="w-full h-full object-cover group-hover:scale-105 transition duration-500" />
                <span class="absolute top-3 left-3 px-2.5 py-1 rounded-full bg-spaceDark/85 backdrop-blur-md text-[10px] font-extrabold text-emeraldAccent border border-emeraldAccent/30 flex items-center gap-1">🇮🇳 National</span>
                <span class="absolute top-3 right-3 px-2 py-0.5 rounded-full bg-black/60 backdrop-blur-md text-[10px] font-bold text-amberAccent">⭐ 4.8</span>
              </div>
              <div>
                <div class="flex items-center gap-2">
                  <span class="text-[10px] font-bold px-2 py-0.5 rounded-md bg-cyanAccent/20 text-cyanAccent border border-cyanAccent/30">Mountains & Trekking</span>
                </div>
                <h3 class="text-base font-bold text-white group-hover:text-coralPrimary transition mt-1.5">Manali & Kasol, HP</h3>
                <p class="text-xs text-gray-400 mt-1 leading-relaxed">Snowcapped Himalayan passes, riverside cafes, vibrant backpacker hostels, and Kheerganga treks.</p>
              </div>
            </div>
            <div class="flex justify-between items-center pt-3 border-t border-white/10">
              <span class="text-xs font-bold text-cyanAccent hotspot-cost-val">💰 ~₹1,800 / day</span>
              <span class="text-xs font-bold text-coralPrimary flex items-center gap-1 group-hover:translate-x-1 transition">Plan Trip →</span>
            </div>
          </div>

          <!-- 3. Jaipur & Udaipur -->
          <div class="hotspot-card glass-card rounded-3xl p-5 space-y-4 cursor-pointer group flex flex-col justify-between" data-scope="national" data-cat="culture" data-cost-inr="2200" data-tilt data-tilt-max="6" onclick="quickPlanHotspot('Jaipur, Rajasthan, India', 3, 'Student (Low)', ['History', 'Culture', 'Street Food'])">
            <div class="space-y-3">
              <div class="relative rounded-2xl overflow-hidden h-44">
                <img src="https://images.unsplash.com/photo-1599661046289-e31897846e41?auto=format&fit=crop&w=600&q=80" alt="Jaipur Palace" class="w-full h-full object-cover group-hover:scale-105 transition duration-500" />
                <span class="absolute top-3 left-3 px-2.5 py-1 rounded-full bg-spaceDark/85 backdrop-blur-md text-[10px] font-extrabold text-emeraldAccent border border-emeraldAccent/30 flex items-center gap-1">🇮🇳 National</span>
                <span class="absolute top-3 right-3 px-2 py-0.5 rounded-full bg-black/60 backdrop-blur-md text-[10px] font-bold text-amberAccent">⭐ 4.9</span>
              </div>
              <div>
                <div class="flex items-center gap-2">
                  <span class="text-[10px] font-bold px-2 py-0.5 rounded-md bg-amberAccent/20 text-amberAccent border border-amberAccent/30">Royal Forts & Bazaars</span>
                </div>
                <h3 class="text-base font-bold text-white group-hover:text-coralPrimary transition mt-1.5">Jaipur & Udaipur, India</h3>
                <p class="text-xs text-gray-400 mt-1 leading-relaxed">Hawa Mahal, Amer Fort views, lakeside sunsets, student heritage discounts, and spicy street food.</p>
              </div>
            </div>
            <div class="flex justify-between items-center pt-3 border-t border-white/10">
              <span class="text-xs font-bold text-amberAccent hotspot-cost-val">💰 ~₹2,200 / day</span>
              <span class="text-xs font-bold text-coralPrimary flex items-center gap-1 group-hover:translate-x-1 transition">Plan Trip →</span>
            </div>
          </div>

          <!-- 4. Rishikesh -->
          <div class="hotspot-card glass-card rounded-3xl p-5 space-y-4 cursor-pointer group flex flex-col justify-between" data-scope="national" data-cat="adventure mountain" data-cost-inr="1600" data-tilt data-tilt-max="6" onclick="quickPlanHotspot('Rishikesh, Uttarakhand, India', 3, 'Student (Low)', ['Adventure', 'Nature', 'Culture'])">
            <div class="space-y-3">
              <div class="relative rounded-2xl overflow-hidden h-44">
                <img src="https://images.unsplash.com/photo-1596401057633-54a8fe8ef647?auto=format&fit=crop&w=600&q=80" alt="Rishikesh River & Bridges" class="w-full h-full object-cover group-hover:scale-105 transition duration-500" />
                <span class="absolute top-3 left-3 px-2.5 py-1 rounded-full bg-spaceDark/85 backdrop-blur-md text-[10px] font-extrabold text-emeraldAccent border border-emeraldAccent/30 flex items-center gap-1">🇮🇳 National</span>
                <span class="absolute top-3 right-3 px-2 py-0.5 rounded-full bg-black/60 backdrop-blur-md text-[10px] font-bold text-amberAccent">⭐ 4.9</span>
              </div>
              <div>
                <div class="flex items-center gap-2">
                  <span class="text-[10px] font-bold px-2 py-0.5 rounded-md bg-purpleAccent/20 text-purpleAccent border border-purpleAccent/30">Rafting & Yoga Vibe</span>
                </div>
                <h3 class="text-base font-bold text-white group-hover:text-coralPrimary transition mt-1.5">Rishikesh, India</h3>
                <p class="text-xs text-gray-400 mt-1 leading-relaxed">White-water Ganga rafting, cliff jumping, riverside camping tents, Beatles Ashram, and evening aarti.</p>
              </div>
            </div>
            <div class="flex justify-between items-center pt-3 border-t border-white/10">
              <span class="text-xs font-bold text-purpleAccent hotspot-cost-val">💰 ~₹1,600 / day</span>
              <span class="text-xs font-bold text-coralPrimary flex items-center gap-1 group-hover:translate-x-1 transition">Plan Trip →</span>
            </div>
          </div>

          <!-- 5. Varanasi -->
          <div class="hotspot-card glass-card rounded-3xl p-5 space-y-4 cursor-pointer group flex flex-col justify-between" data-scope="national" data-cat="culture" data-cost-inr="1400" data-tilt data-tilt-max="6" onclick="quickPlanHotspot('Varanasi, Uttar Pradesh, India', 3, 'Student (Low)', ['History', 'Culture', 'Street Food'])">
            <div class="space-y-3">
              <div class="relative rounded-2xl overflow-hidden h-44">
                <img src="https://images.unsplash.com/photo-1571536802807-30451e3955d8?auto=format&fit=crop&w=600&q=80" alt="Varanasi Ganga Ghats" class="w-full h-full object-cover group-hover:scale-105 transition duration-500" />
                <span class="absolute top-3 left-3 px-2.5 py-1 rounded-full bg-spaceDark/85 backdrop-blur-md text-[10px] font-extrabold text-emeraldAccent border border-emeraldAccent/30 flex items-center gap-1">🇮🇳 National</span>
                <span class="absolute top-3 right-3 px-2 py-0.5 rounded-full bg-black/60 backdrop-blur-md text-[10px] font-bold text-amberAccent">⭐ 4.8</span>
              </div>
              <div>
                <div class="flex items-center gap-2">
                  <span class="text-[10px] font-bold px-2 py-0.5 rounded-md bg-amberAccent/20 text-amberAccent border border-amberAccent/30">Ancient Ghats & Chaat</span>
                </div>
                <h3 class="text-base font-bold text-white group-hover:text-coralPrimary transition mt-1.5">Varanasi, India</h3>
                <p class="text-xs text-gray-400 mt-1 leading-relaxed">Sunrise boat rides along the sacred Ganga, labyrinth heritage lanes, and world-famous street food.</p>
              </div>
            </div>
            <div class="flex justify-between items-center pt-3 border-t border-white/10">
              <span class="text-xs font-bold text-amberAccent hotspot-cost-val">💰 ~₹1,400 / day</span>
              <span class="text-xs font-bold text-coralPrimary flex items-center gap-1 group-hover:translate-x-1 transition">Plan Trip →</span>
            </div>
          </div>

          <!-- 6. Munnar & Kochi -->
          <div class="hotspot-card glass-card rounded-3xl p-5 space-y-4 cursor-pointer group flex flex-col justify-between" data-scope="national" data-cat="nature beach" data-cost-inr="2100" data-tilt data-tilt-max="6" onclick="quickPlanHotspot('Munnar, Kerala, India', 4, 'Student (Low)', ['Nature', 'Culture', 'Photography'])">
            <div class="space-y-3">
              <div class="relative rounded-2xl overflow-hidden h-44">
                <img src="https://images.unsplash.com/photo-1602216056096-3b40cc0c9944?auto=format&fit=crop&w=600&q=80" alt="Munnar Tea Hills" class="w-full h-full object-cover group-hover:scale-105 transition duration-500" />
                <span class="absolute top-3 left-3 px-2.5 py-1 rounded-full bg-spaceDark/85 backdrop-blur-md text-[10px] font-extrabold text-emeraldAccent border border-emeraldAccent/30 flex items-center gap-1">🇮🇳 National</span>
                <span class="absolute top-3 right-3 px-2 py-0.5 rounded-full bg-black/60 backdrop-blur-md text-[10px] font-bold text-amberAccent">⭐ 4.8</span>
              </div>
              <div>
                <div class="flex items-center gap-2">
                  <span class="text-[10px] font-bold px-2 py-0.5 rounded-md bg-emeraldAccent/20 text-emeraldAccent border border-emeraldAccent/30">Tea Hills & Coastal Art</span>
                </div>
                <h3 class="text-base font-bold text-white group-hover:text-coralPrimary transition mt-1.5">Munnar & Kochi, Kerala</h3>
                <p class="text-xs text-gray-400 mt-1 leading-relaxed">Misty tea estate walks, budget backwater ferries, Fort Kochi art cafes, and spice plantations.</p>
              </div>
            </div>
            <div class="flex justify-between items-center pt-3 border-t border-white/10">
              <span class="text-xs font-bold text-emeraldAccent hotspot-cost-val">💰 ~₹2,100 / day</span>
              <span class="text-xs font-bold text-coralPrimary flex items-center gap-1 group-hover:translate-x-1 transition">Plan Trip →</span>
            </div>
          </div>

          <!-- 7. Leh-Ladakh -->
          <div class="hotspot-card glass-card rounded-3xl p-5 space-y-4 cursor-pointer group flex flex-col justify-between" data-scope="national" data-cat="mountain adventure nature" data-cost-inr="2400" data-tilt data-tilt-max="6" onclick="quickPlanHotspot('Leh Ladakh, India', 5, 'Student (Low)', ['Adventure', 'Nature', 'Hiking'])">
            <div class="space-y-3">
              <div class="relative rounded-2xl overflow-hidden h-44">
                <img src="https://images.unsplash.com/photo-1581793745862-99fde7fa73d2?auto=format&fit=crop&w=600&q=80" alt="Leh Ladakh Pangong Lake" class="w-full h-full object-cover group-hover:scale-105 transition duration-500" />
                <span class="absolute top-3 left-3 px-2.5 py-1 rounded-full bg-spaceDark/85 backdrop-blur-md text-[10px] font-extrabold text-emeraldAccent border border-emeraldAccent/30 flex items-center gap-1">🇮🇳 National</span>
                <span class="absolute top-3 right-3 px-2 py-0.5 rounded-full bg-black/60 backdrop-blur-md text-[10px] font-bold text-amberAccent">⭐ 4.9</span>
              </div>
              <div>
                <div class="flex items-center gap-2">
                  <span class="text-[10px] font-bold px-2 py-0.5 rounded-md bg-cyanAccent/20 text-cyanAccent border border-cyanAccent/30">Himalayan Passes & Lakes</span>
                </div>
                <h3 class="text-base font-bold text-white group-hover:text-coralPrimary transition mt-1.5">Leh-Ladakh, India</h3>
                <p class="text-xs text-gray-400 mt-1 leading-relaxed">Pangong Tso blue waters, Khardung La pass, Magnetic Hill, and ancient Buddhist monastery trails.</p>
              </div>
            </div>
            <div class="flex justify-between items-center pt-3 border-t border-white/10">
              <span class="text-xs font-bold text-cyanAccent hotspot-cost-val">💰 ~₹2,400 / day</span>
              <span class="text-xs font-bold text-coralPrimary flex items-center gap-1 group-hover:translate-x-1 transition">Plan Trip →</span>
            </div>
          </div>

          <!-- 8. Shillong & Meghalaya -->
          <div class="hotspot-card glass-card rounded-3xl p-5 space-y-4 cursor-pointer group flex flex-col justify-between" data-scope="national" data-cat="nature adventure" data-cost-inr="1900" data-tilt data-tilt-max="6" onclick="quickPlanHotspot('Shillong, Meghalaya, India', 4, 'Student (Low)', ['Nature', 'Adventure', 'Photography'])">
            <div class="space-y-3">
              <div class="relative rounded-2xl overflow-hidden h-44">
                <img src="https://images.unsplash.com/photo-1607604276583-eef5d076aa5f?auto=format&fit=crop&w=600&q=80" alt="Meghalaya Living Root Bridge & Waterfalls" class="w-full h-full object-cover group-hover:scale-105 transition duration-500" />
                <span class="absolute top-3 left-3 px-2.5 py-1 rounded-full bg-spaceDark/85 backdrop-blur-md text-[10px] font-extrabold text-emeraldAccent border border-emeraldAccent/30 flex items-center gap-1">🇮🇳 National</span>
                <span class="absolute top-3 right-3 px-2 py-0.5 rounded-full bg-black/60 backdrop-blur-md text-[10px] font-bold text-amberAccent">⭐ 4.9</span>
              </div>
              <div>
                <div class="flex items-center gap-2">
                  <span class="text-[10px] font-bold px-2 py-0.5 rounded-md bg-emeraldAccent/20 text-emeraldAccent border border-emeraldAccent/30">Living Root Bridges & Caves</span>
                </div>
                <h3 class="text-base font-bold text-white group-hover:text-coralPrimary transition mt-1.5">Shillong & Meghalaya</h3>
                <p class="text-xs text-gray-400 mt-1 leading-relaxed">Living root bridges, glass-clear Umngot river boating, Nohkalikai waterfalls, and live music cafes.</p>
              </div>
            </div>
            <div class="flex justify-between items-center pt-3 border-t border-white/10">
              <span class="text-xs font-bold text-emeraldAccent hotspot-cost-val">💰 ~₹1,900 / day</span>
              <span class="text-xs font-bold text-coralPrimary flex items-center gap-1 group-hover:translate-x-1 transition">Plan Trip →</span>
            </div>
          </div>

          <!-- ============================================ -->
          <!-- ✈️ INTERNATIONAL DESTINATIONS (GLOBAL) -->
          <!-- ============================================ -->

          <!-- 9. Tokyo -->
          <div class="hotspot-card glass-card rounded-3xl p-5 space-y-4 cursor-pointer group flex flex-col justify-between" data-scope="international" data-cat="culture nightlife" data-cost-inr="4200" data-tilt data-tilt-max="6" onclick="quickPlanHotspot('Tokyo, Japan', 4, 'Student (Low)', ['Street Food', 'Anime & Pop Culture', 'History'])">
            <div class="space-y-3">
              <div class="relative rounded-2xl overflow-hidden h-44">
                <img src="https://images.unsplash.com/photo-1503899036084-c55cdd92da26?auto=format&fit=crop&w=600&q=80" alt="Tokyo City" class="w-full h-full object-cover group-hover:scale-105 transition duration-500" />
                <span class="absolute top-3 left-3 px-2.5 py-1 rounded-full bg-spaceDark/85 backdrop-blur-md text-[10px] font-extrabold text-cyanAccent border border-cyanAccent/30 flex items-center gap-1">✈️ International (🇯🇵)</span>
                <span class="absolute top-3 right-3 px-2 py-0.5 rounded-full bg-black/60 backdrop-blur-md text-[10px] font-bold text-amberAccent">⭐ 4.9</span>
              </div>
              <div>
                <div class="flex items-center gap-2">
                  <span class="text-[10px] font-bold px-2 py-0.5 rounded-md bg-purpleAccent/20 text-purpleAccent border border-purpleAccent/30">Pop Culture & Tech</span>
                </div>
                <h3 class="text-base font-bold text-white group-hover:text-coralPrimary transition mt-1.5">Tokyo, Japan</h3>
                <p class="text-xs text-gray-400 mt-1 leading-relaxed">Neon Shibuya alleys, high-speed rail, anime arcades, 100-yen stores, and incredible budget ramen stalls.</p>
              </div>
            </div>
            <div class="flex justify-between items-center pt-3 border-t border-white/10">
              <span class="text-xs font-bold text-amberAccent hotspot-cost-val">💰 ~₹4,200 / day</span>
              <span class="text-xs font-bold text-coralPrimary flex items-center gap-1 group-hover:translate-x-1 transition">Plan Trip →</span>
            </div>
          </div>

          <!-- 8. Bali -->
          <div class="hotspot-card glass-card rounded-3xl p-5 space-y-4 cursor-pointer group flex flex-col justify-between" data-scope="international" data-cat="beach nature" data-cost-inr="2500" data-tilt data-tilt-max="6" onclick="quickPlanHotspot('Bali, Indonesia', 5, 'Student (Low)', ['Nature', 'Beaches', 'Adventure'])">
            <div class="space-y-3">
              <div class="relative rounded-2xl overflow-hidden h-44">
                <img src="https://images.unsplash.com/photo-1537996194471-e657df975ab4?auto=format&fit=crop&w=600&q=80" alt="Bali Beach" class="w-full h-full object-cover group-hover:scale-105 transition duration-500" />
                <span class="absolute top-3 left-3 px-2.5 py-1 rounded-full bg-spaceDark/85 backdrop-blur-md text-[10px] font-extrabold text-cyanAccent border border-cyanAccent/30 flex items-center gap-1">✈️ International (🇮🇩)</span>
                <span class="absolute top-3 right-3 px-2 py-0.5 rounded-full bg-black/60 backdrop-blur-md text-[10px] font-bold text-amberAccent">⭐ 4.8</span>
              </div>
              <div>
                <div class="flex items-center gap-2">
                  <span class="text-[10px] font-bold px-2 py-0.5 rounded-md bg-cyanAccent/20 text-cyanAccent border border-cyanAccent/30">Beaches & Jungles</span>
                </div>
                <h3 class="text-base font-bold text-white group-hover:text-coralPrimary transition mt-1.5">Bali, Indonesia</h3>
                <p class="text-xs text-gray-400 mt-1 leading-relaxed">Lush jungle waterfalls, world-class surf breaks, sunset beach clubs, and vibrant backpacker hostels.</p>
              </div>
            </div>
            <div class="flex justify-between items-center pt-3 border-t border-white/10">
              <span class="text-xs font-bold text-cyanAccent hotspot-cost-val">💰 ~₹2,500 / day</span>
              <span class="text-xs font-bold text-coralPrimary flex items-center gap-1 group-hover:translate-x-1 transition">Plan Trip →</span>
            </div>
          </div>

          <!-- 9. Bangkok & Phuket -->
          <div class="hotspot-card glass-card rounded-3xl p-5 space-y-4 cursor-pointer group flex flex-col justify-between" data-scope="international" data-cat="beach nightlife" data-cost-inr="2300" data-tilt data-tilt-max="6" onclick="quickPlanHotspot('Bangkok, Thailand', 4, 'Student (Low)', ['Street Food', 'Nightlife', 'Beaches'])">
            <div class="space-y-3">
              <div class="relative rounded-2xl overflow-hidden h-44">
                <img src="https://images.unsplash.com/photo-1508009603885-50cf7c579365?auto=format&fit=crop&w=600&q=80" alt="Bangkok Temples" class="w-full h-full object-cover group-hover:scale-105 transition duration-500" />
                <span class="absolute top-3 left-3 px-2.5 py-1 rounded-full bg-spaceDark/85 backdrop-blur-md text-[10px] font-extrabold text-cyanAccent border border-cyanAccent/30 flex items-center gap-1">✈️ International (🇹🇭)</span>
                <span class="absolute top-3 right-3 px-2 py-0.5 rounded-full bg-black/60 backdrop-blur-md text-[10px] font-bold text-amberAccent">⭐ 4.8</span>
              </div>
              <div>
                <div class="flex items-center gap-2">
                  <span class="text-[10px] font-bold px-2 py-0.5 rounded-md bg-coralPrimary/20 text-coralPrimary border border-coralPrimary/30">Night Markets & Islands</span>
                </div>
                <h3 class="text-base font-bold text-white group-hover:text-coralPrimary transition mt-1.5">Bangkok & Phuket, Thailand</h3>
                <p class="text-xs text-gray-400 mt-1 leading-relaxed">Street food paradise, Chao Phraya express river boats, Phi Phi island trips, and lively night markets.</p>
              </div>
            </div>
            <div class="flex justify-between items-center pt-3 border-t border-white/10">
              <span class="text-xs font-bold text-coralPrimary hotspot-cost-val">💰 ~₹2,300 / day</span>
              <span class="text-xs font-bold text-coralPrimary flex items-center gap-1 group-hover:translate-x-1 transition">Plan Trip →</span>
            </div>
          </div>

          <!-- 10. Rome -->
          <div class="hotspot-card glass-card rounded-3xl p-5 space-y-4 cursor-pointer group flex flex-col justify-between" data-scope="international" data-cat="culture" data-cost-inr="5000" data-tilt data-tilt-max="6" onclick="quickPlanHotspot('Rome, Italy', 3, 'Moderate', ['History', 'Museums', 'Street Food'])">
            <div class="space-y-3">
              <div class="relative rounded-2xl overflow-hidden h-44">
                <img src="https://images.unsplash.com/photo-1552832230-c0197dd311b5?auto=format&fit=crop&w=600&q=80" alt="Rome Colosseum" class="w-full h-full object-cover group-hover:scale-105 transition duration-500" />
                <span class="absolute top-3 left-3 px-2.5 py-1 rounded-full bg-spaceDark/85 backdrop-blur-md text-[10px] font-extrabold text-cyanAccent border border-cyanAccent/30 flex items-center gap-1">✈️ International (🇮🇹)</span>
                <span class="absolute top-3 right-3 px-2 py-0.5 rounded-full bg-black/60 backdrop-blur-md text-[10px] font-bold text-amberAccent">⭐ 4.9</span>
              </div>
              <div>
                <div class="flex items-center gap-2">
                  <span class="text-[10px] font-bold px-2 py-0.5 rounded-md bg-amberAccent/20 text-amberAccent border border-amberAccent/30">History & Architecture</span>
                </div>
                <h3 class="text-base font-bold text-white group-hover:text-coralPrimary transition mt-1.5">Rome, Italy</h3>
                <p class="text-xs text-gray-400 mt-1 leading-relaxed">Colosseum tours, Trevi fountain wishes, free museum days for students, and authentic woodfire pizza.</p>
              </div>
            </div>
            <div class="flex justify-between items-center pt-3 border-t border-white/10">
              <span class="text-xs font-bold text-amberAccent hotspot-cost-val">💰 ~₹5,000 / day</span>
              <span class="text-xs font-bold text-coralPrimary flex items-center gap-1 group-hover:translate-x-1 transition">Plan Trip →</span>
            </div>
          </div>

          <!-- 11. Amsterdam -->
          <div class="hotspot-card glass-card rounded-3xl p-5 space-y-4 cursor-pointer group flex flex-col justify-between" data-scope="international" data-cat="nightlife culture" data-cost-inr="5500" data-tilt data-tilt-max="6" onclick="quickPlanHotspot('Amsterdam, Netherlands', 3, 'Student (Low)', ['Nightlife', 'Museums', 'Street Food'])">
            <div class="space-y-3">
              <div class="relative rounded-2xl overflow-hidden h-44">
                <img src="https://images.unsplash.com/photo-1512470876302-972faa2aa9a4?auto=format&fit=crop&w=600&q=80" alt="Amsterdam Canals" class="w-full h-full object-cover group-hover:scale-105 transition duration-500" />
                <span class="absolute top-3 left-3 px-2.5 py-1 rounded-full bg-spaceDark/85 backdrop-blur-md text-[10px] font-extrabold text-cyanAccent border border-cyanAccent/30 flex items-center gap-1">✈️ International (🇳🇱)</span>
                <span class="absolute top-3 right-3 px-2 py-0.5 rounded-full bg-black/60 backdrop-blur-md text-[10px] font-bold text-amberAccent">⭐ 4.8</span>
              </div>
              <div>
                <div class="flex items-center gap-2">
                  <span class="text-[10px] font-bold px-2 py-0.5 rounded-md bg-purpleAccent/20 text-purpleAccent border border-purpleAccent/30">Canals & Nightlife</span>
                </div>
                <h3 class="text-base font-bold text-white group-hover:text-coralPrimary transition mt-1.5">Amsterdam, Netherlands</h3>
                <p class="text-xs text-gray-400 mt-1 leading-relaxed">Historic canals, cycling paths, world-class art museums, and unmatched student hostel vibes.</p>
              </div>
            </div>
            <div class="flex justify-between items-center pt-3 border-t border-white/10">
              <span class="text-xs font-bold text-purpleAccent hotspot-cost-val">💰 ~₹5,500 / day</span>
              <span class="text-xs font-bold text-coralPrimary flex items-center gap-1 group-hover:translate-x-1 transition">Plan Trip →</span>
            </div>
          </div>

          <!-- 12. Kyoto -->
          <div class="hotspot-card glass-card rounded-3xl p-5 space-y-4 cursor-pointer group flex flex-col justify-between" data-scope="international" data-cat="culture nature" data-cost-inr="3800" data-tilt data-tilt-max="6" onclick="quickPlanHotspot('Kyoto, Japan', 3, 'Student (Low)', ['History', 'Nature', 'Street Food'])">
            <div class="space-y-3">
              <div class="relative rounded-2xl overflow-hidden h-44">
                <img src="https://images.unsplash.com/photo-1493976040374-85c8e12f0c0e?auto=format&fit=crop&w=600&q=80" alt="Kyoto Shrine" class="w-full h-full object-cover group-hover:scale-105 transition duration-500" />
                <span class="absolute top-3 left-3 px-2.5 py-1 rounded-full bg-spaceDark/85 backdrop-blur-md text-[10px] font-extrabold text-cyanAccent border border-cyanAccent/30 flex items-center gap-1">✈️ International (🇯🇵)</span>
                <span class="absolute top-3 right-3 px-2 py-0.5 rounded-full bg-black/60 backdrop-blur-md text-[10px] font-bold text-amberAccent">⭐ 4.9</span>
              </div>
              <div>
                <div class="flex items-center gap-2">
                  <span class="text-[10px] font-bold px-2 py-0.5 rounded-md bg-amberAccent/20 text-amberAccent border border-amberAccent/30">Shrines & Bamboo Groves</span>
                </div>
                <h3 class="text-base font-bold text-white group-hover:text-coralPrimary transition mt-1.5">Kyoto, Japan</h3>
                <p class="text-xs text-gray-400 mt-1 leading-relaxed">Fushimi Inari thousand torii gates, Arashiyama bamboo forests, and traditional matcha desserts.</p>
              </div>
            </div>
            <div class="flex justify-between items-center pt-3 border-t border-white/10">
              <span class="text-xs font-bold text-amberAccent hotspot-cost-val">💰 ~₹3,800 / day</span>
              <span class="text-xs font-bold text-coralPrimary flex items-center gap-1 group-hover:translate-x-1 transition">Plan Trip →</span>
            </div>
          </div>

          <!-- 13. Paris -->
          <div class="hotspot-card glass-card rounded-3xl p-5 space-y-4 cursor-pointer group flex flex-col justify-between" data-scope="international" data-cat="culture" data-cost-inr="5200" data-tilt data-tilt-max="6" onclick="quickPlanHotspot('Paris, France', 3, 'Moderate', ['Museums', 'Culture', 'Photography'])">
            <div class="space-y-3">
              <div class="relative rounded-2xl overflow-hidden h-44">
                <img src="https://images.unsplash.com/photo-1502602898657-3e91760cbb34?auto=format&fit=crop&w=600&q=80" alt="Paris Eiffel Tower" class="w-full h-full object-cover group-hover:scale-105 transition duration-500" />
                <span class="absolute top-3 left-3 px-2.5 py-1 rounded-full bg-spaceDark/85 backdrop-blur-md text-[10px] font-extrabold text-cyanAccent border border-cyanAccent/30 flex items-center gap-1">✈️ International (🇫🇷)</span>
                <span class="absolute top-3 right-3 px-2 py-0.5 rounded-full bg-black/60 backdrop-blur-md text-[10px] font-bold text-amberAccent">⭐ 4.8</span>
              </div>
              <div>
                <div class="flex items-center gap-2">
                  <span class="text-[10px] font-bold px-2 py-0.5 rounded-md bg-coralPrimary/20 text-coralPrimary border border-coralPrimary/30">Art, Cafes & Architecture</span>
                </div>
                <h3 class="text-base font-bold text-white group-hover:text-coralPrimary transition mt-1.5">Paris, France</h3>
                <p class="text-xs text-gray-400 mt-1 leading-relaxed">Seine river sunset picnics, Montmartre artists, youth museum access, and fresh neighborhood bakeries.</p>
              </div>
            </div>
            <div class="flex justify-between items-center pt-3 border-t border-white/10">
              <span class="text-xs font-bold text-coralPrimary hotspot-cost-val">💰 ~₹5,200 / day</span>
              <span class="text-xs font-bold text-coralPrimary flex items-center gap-1 group-hover:translate-x-1 transition">Plan Trip →</span>
            </div>
          </div>

          <!-- 14. Dubai -->
          <div class="hotspot-card glass-card rounded-3xl p-5 space-y-4 cursor-pointer group flex flex-col justify-between" data-scope="international" data-cat="nightlife adventure" data-cost-inr="4500" data-tilt data-tilt-max="6" onclick="quickPlanHotspot('Dubai, UAE', 3, 'Student (Low)', ['Adventure', 'Sightseeing', 'Shopping'])">
            <div class="space-y-3">
              <div class="relative rounded-2xl overflow-hidden h-44">
                <img src="https://images.unsplash.com/photo-1512453979798-5ea266f8880c?auto=format&fit=crop&w=600&q=80" alt="Dubai Skyline" class="w-full h-full object-cover group-hover:scale-105 transition duration-500" />
                <span class="absolute top-3 left-3 px-2.5 py-1 rounded-full bg-spaceDark/85 backdrop-blur-md text-[10px] font-extrabold text-cyanAccent border border-cyanAccent/30 flex items-center gap-1">✈️ International (🇦🇪)</span>
                <span class="absolute top-3 right-3 px-2 py-0.5 rounded-full bg-black/60 backdrop-blur-md text-[10px] font-bold text-amberAccent">⭐ 4.8</span>
              </div>
              <div>
                <div class="flex items-center gap-2">
                  <span class="text-[10px] font-bold px-2 py-0.5 rounded-md bg-cyanAccent/20 text-cyanAccent border border-cyanAccent/30">Desert Safaris & Skylines</span>
                </div>
                <h3 class="text-base font-bold text-white group-hover:text-coralPrimary transition mt-1.5">Dubai, UAE</h3>
                <p class="text-xs text-gray-400 mt-1 leading-relaxed">Red dune sandboarding safaris, 1-dirham creek abra rides, Spice Souks, and futuristic architecture.</p>
              </div>
            </div>
            <div class="flex justify-between items-center pt-3 border-t border-white/10">
              <span class="text-xs font-bold text-cyanAccent hotspot-cost-val">💰 ~₹4,500 / day</span>
              <span class="text-xs font-bold text-coralPrimary flex items-center gap-1 group-hover:translate-x-1 transition">Plan Trip →</span>
            </div>
          </div>

        </div>

        <!-- Empty State Message when filters yield no matches -->
        <div id="hotspotEmptyMsg" class="hidden glass-card p-10 rounded-3xl border border-dashed border-white/15 text-center space-y-3 shadow-lg">
          <span class="text-3xl">🧭</span>
          <h4 class="text-base font-bold text-white">No destinations match the selected filters</h4>
          <p class="text-xs text-gray-400">Try selecting "All" in the scope or vibe tabs above to explore all 14 student hotspots.</p>
          <button onclick="setHotspotScope('all'); setHotspotCategory('all')" class="btn-secondary px-4 py-2 rounded-xl text-xs font-semibold text-coralPrimary mx-auto">
            <span>Reset Hotspot Filters</span>
          </button>
        </div>
      </div>

      <!-- 3D BENTO GRID: WHY ROAMAI -->
      <div class="space-y-8">
        <div class="text-center max-w-2xl mx-auto space-y-2">
          <span class="text-xs font-bold uppercase tracking-wider text-cyanAccent">Architected For Gen-Z & Students</span>
          <h2 class="text-3xl font-extrabold text-white">Superpowers That Make Travel Effortless</h2>
          <p class="text-gray-400 text-xs sm:text-sm">Built specifically to eliminate overspending, scheduling chaos, and packing anxiety.</p>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          
          <!-- Bento 1 -->
          <div class="glass-card p-6 sm:p-7 rounded-3xl border border-white/10 space-y-4 hover:border-coralPrimary/40 transition">
            <div class="w-12 h-12 rounded-2xl bg-coralPrimary/20 border border-coralPrimary/30 flex items-center justify-center text-2xl">
              ⚡
            </div>
            <h3 class="text-base font-bold text-white">Sub-Second AI Planning</h3>
            <p class="text-xs text-gray-400 leading-relaxed">
              Powered by Groq LPUs with multi-model fallback, crafting detailed hour-by-hour schedules in under 1.5 seconds.
            </p>
          </div>

          <!-- Bento 2 -->
          <div class="glass-card p-6 sm:p-7 rounded-3xl border border-white/10 space-y-4 hover:border-cyanAccent/40 transition">
            <div class="w-12 h-12 rounded-2xl bg-cyanAccent/20 border border-cyanAccent/30 flex items-center justify-center text-2xl">
              🗺️
            </div>
            <h3 class="text-base font-bold text-white">Dynamic 3D GPS Mapping</h3>
            <p class="text-xs text-gray-400 leading-relaxed">
              Auto-geocodes tourist attractions, food alleys, and transit hubs directly onto interactive Leaflet maps.
            </p>
          </div>

          <!-- Bento 3 -->
          <div class="glass-card p-6 sm:p-7 rounded-3xl border border-white/10 space-y-4 hover:border-amberAccent/40 transition">
            <div class="w-12 h-12 rounded-2xl bg-amberAccent/20 border border-amberAccent/30 flex items-center justify-center text-2xl">
              💰
            </div>
            <h3 class="text-base font-bold text-white">9-Region Currency Sync</h3>
            <p class="text-xs text-gray-400 leading-relaxed">
              Seamlessly toggle between INR, USD, EUR, GBP, JPY, AUD, CAD, AED, and THB with real-time budget adjustments.
            </p>
          </div>

          <!-- Bento 4 -->
          <div class="glass-card p-6 sm:p-7 rounded-3xl border border-white/10 space-y-4 hover:border-emeraldAccent/40 transition">
            <div class="w-12 h-12 rounded-2xl bg-emeraldAccent/20 border border-emeraldAccent/30 flex items-center justify-center text-2xl">
              🎒
            </div>
            <h3 class="text-base font-bold text-white">Smart Packing Architect</h3>
            <p class="text-xs text-gray-400 leading-relaxed">
              Auto-adapts to your destination's vibe (Beach, Mountain, City, Snow) with offline device persistence.
            </p>
          </div>

        </div>
      </div>

      <!-- 3-STEP "HOW IT WORKS" -->
      <div class="glass-card p-8 sm:p-12 rounded-3xl border border-white/10 space-y-10">
        <div class="text-center max-w-xl mx-auto space-y-2">
          <span class="text-xs font-bold uppercase tracking-wider text-coralPrimary">Simple 3-Step Journey</span>
          <h2 class="text-2xl sm:text-3xl font-extrabold text-white">How RoamAI Crafts Your Trip</h2>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-3 gap-8 relative">
          <div class="space-y-3 relative z-10">
            <div class="w-10 h-10 rounded-2xl bg-gradient-to-r from-coralPrimary to-amberAccent text-white font-extrabold flex items-center justify-center text-sm shadow-lg">1</div>
            <h3 class="text-base font-bold text-white">Choose Place & Budget</h3>
            <p class="text-xs text-gray-400 leading-relaxed">Enter any destination, select your trip duration, budget tier, and tailor your personal interests.</p>
          </div>
          <div class="space-y-3 relative z-10">
            <div class="w-10 h-10 rounded-2xl bg-gradient-to-r from-amberAccent to-cyanAccent text-white font-extrabold flex items-center justify-center text-sm shadow-lg">2</div>
            <h3 class="text-base font-bold text-white">AI Maps Route & Costs</h3>
            <p class="text-xs text-gray-400 leading-relaxed">Groq AI generates day-by-day stops, budget hacks, transit tips, and plots live GPS map pins.</p>
          </div>
          <div class="space-y-3 relative z-10">
            <div class="w-10 h-10 rounded-2xl bg-gradient-to-r from-cyanAccent to-emeraldAccent text-white font-extrabold flex items-center justify-center text-sm shadow-lg">3</div>
            <h3 class="text-base font-bold text-white">Pack & Export Offline</h3>
            <p class="text-xs text-gray-400 leading-relaxed">Check off essential gear, calculate total expenses in your currency, and export a clean PDF.</p>
          </div>
        </div>
      </div>

      <!-- STUDENT TESTIMONIALS -->
      <div class="space-y-8">
        <div class="text-center max-w-xl mx-auto space-y-2">
          <span class="text-xs font-bold uppercase tracking-wider text-amberAccent">Student Verified</span>
          <h2 class="text-2xl sm:text-3xl font-extrabold text-white">Loved by Travelers Worldwide</h2>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div class="glass-card p-6 rounded-3xl border border-white/10 space-y-4">
            <div class="flex items-center gap-1 text-amberAccent text-xs">⭐⭐⭐⭐⭐</div>
            <p class="text-xs text-gray-300 leading-relaxed italic">"Planned our 5-day Goa college trip in 10 seconds. The hostel tips and budget calculator saved each of us ₹4,000!"</p>
            <div class="flex items-center gap-3 pt-2 border-t border-white/5">
              <div class="w-8 h-8 rounded-full bg-coralPrimary/30 flex items-center justify-center font-bold text-xs text-coralPrimary">AK</div>
              <div>
                <h4 class="text-xs font-bold text-white">Aryan K.</h4>
                <p class="text-[10px] text-gray-400">IIT Bombay • Visited Goa</p>
              </div>
            </div>
          </div>

          <div class="glass-card p-6 rounded-3xl border border-white/10 space-y-4">
            <div class="flex items-center gap-1 text-amberAccent text-xs">⭐⭐⭐⭐⭐</div>
            <p class="text-xs text-gray-300 leading-relaxed italic">"The Tokyo ramen spots and subway pass suggestions were spot on. The interactive map made navigation super easy."</p>
            <div class="flex items-center gap-3 pt-2 border-t border-white/5">
              <div class="w-8 h-8 rounded-full bg-cyanAccent/30 flex items-center justify-center font-bold text-xs text-cyanAccent">SL</div>
              <div>
                <h4 class="text-xs font-bold text-white">Sarah L.</h4>
                <p class="text-[10px] text-gray-400">UC Berkeley • Visited Tokyo</p>
              </div>
            </div>
          </div>

          <div class="glass-card p-6 rounded-3xl border border-white/10 space-y-4">
            <div class="flex items-center gap-1 text-amberAccent text-xs">⭐⭐⭐⭐⭐</div>
            <p class="text-xs text-gray-300 leading-relaxed italic">"Exporting the PDF itinerary for my Europe backpack tour gave me offline access throughout Rome and Amsterdam!"</p>
            <div class="flex items-center gap-3 pt-2 border-t border-white/5">
              <div class="w-8 h-8 rounded-full bg-emeraldAccent/30 flex items-center justify-center font-bold text-xs text-emeraldAccent">MR</div>
              <div>
                <h4 class="text-xs font-bold text-white">Matteo R.</h4>
                <p class="text-[10px] text-gray-400">Politecnico di Milano • Visited Rome</p>
              </div>
            </div>
          </div>
        </div>
      </div>

    </section>

    <!-- PAGE 2: AI TRIP PLANNER -->
    <section id="page-planner" class="hidden space-y-8">
      
      <!-- Top Row: 2 Equal Width & Matching Length Grids (1. Trip Architect Form, 2. Interactive Map) -->
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-8 items-stretch" id="plannerTopGrids">
        
        <!-- Grid 1: Trip Architect Parameter Form -->
        <div class="glass-card p-6 sm:p-7 rounded-3xl border border-white/10 flex flex-col justify-between space-y-5 shadow-2xl h-full">
          <div>
            <div class="flex items-center justify-between pb-3 border-b border-white/10">
              <div class="flex items-center gap-2">
                <span class="text-xl">🧭</span>
                <div>
                  <h2 class="text-lg font-bold text-white leading-tight">Trip Architect</h2>
                  <p class="text-[11px] text-gray-400">Step 1: Set Destination & Vibe</p>
                </div>
              </div>
              <div class="flex items-center gap-2">
                <button
                  type="button"
                  onclick="resetPlannerAll()"
                  class="px-2.5 py-1 text-[11px] font-bold rounded-full bg-white/10 hover:bg-rose-500/20 text-gray-300 hover:text-rose-400 border border-white/15 hover:border-rose-500/30 transition flex items-center gap-1 shadow-sm"
                  title="Reset all inputs, draft and clear current trip"
                >
                  <span>🔄</span> Reset All
                </button>
                <span class="px-2.5 py-1 text-[10px] font-bold rounded-full bg-emeraldAccent/20 text-emeraldAccent border border-emeraldAccent/30" id="activeRegionBadge">🇮🇳 INR Active</span>
              </div>
            </div>

            <div class="space-y-4 pt-3">
              <div class="space-y-1.5">
                <label class="block text-xs font-bold uppercase text-gray-300">📍 Destination</label>
                <input type="text" id="plannerDest" placeholder="e.g. Kyoto, Japan or Rome, Italy" class="w-full px-4 py-3 bg-spaceDark border border-white/15 rounded-xl text-sm text-white focus:outline-none focus:border-coralPrimary shadow-inner" />
              </div>

              <div class="grid grid-cols-2 gap-4">
                <div class="space-y-1.5">
                  <div class="flex justify-between text-xs font-bold text-gray-300">
                    <span>📅 Duration</span>
                    <span id="daysDisp" class="text-coralPrimary">3 Days</span>
                  </div>
                  <input type="range" id="plannerDays" min="1" max="90" value="3" class="w-full accent-coralPrimary cursor-pointer" oninput="document.getElementById('daysDisp').innerText = this.value + ' Days'" />
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
                  <input type="text" id="plannerMustVisit" placeholder="e.g. Colosseum" class="w-full px-3 py-2.5 bg-spaceDark border border-white/15 rounded-xl text-xs text-white" />
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
            </div>
          </div>

          <button id="genBtn" onclick="planTrip()" class="w-full mt-4 btn-gradient py-3.5 rounded-2xl font-extrabold text-sm flex items-center justify-center gap-2 shadow-xl">
            <span>🚀 Generate AI Itinerary</span>
          </button>
        </div>

        <!-- Grid 2: Interactive Destination Map (Equal Height & Width with Grid 1) -->
        <div class="glass-card p-6 rounded-3xl border border-white/10 flex flex-col justify-between shadow-2xl h-full min-h-[540px]" id="plannerMapCard">
          <div class="flex items-center justify-between pb-3 border-b border-white/10">
            <div class="flex items-center gap-2">
              <span class="text-xl">📍</span>
              <div>
                <h3 id="mapHeading" class="text-base sm:text-lg font-bold text-white leading-tight">Interactive Destination Map</h3>
                <p class="text-[11px] text-gray-400">Step 2: Explore Geo-Coordinates</p>
              </div>
            </div>
            <span class="text-xs text-amberAccent font-semibold px-2.5 py-0.5 rounded-full bg-amberAccent/10 border border-amberAccent/20" id="mapStatusBadge">Awaiting Destination</span>
          </div>
          
          <div class="map-frame-box flex-grow w-full rounded-2xl overflow-hidden mt-4 relative bg-spaceDark/60 border border-white/10 min-h-[440px] flex items-center justify-center">
            <!-- Sleek Interactive Map Filler / Template State -->
            <div id="mapPlaceholder" class="w-full h-full flex flex-col items-center justify-center p-6 text-center space-y-4">
              <div class="relative flex items-center justify-center">
                <div class="w-20 h-20 rounded-full bg-coralPrimary/10 border border-coralPrimary/20 flex items-center justify-center text-4xl shadow-inner animate-pulse">
                  🗺️
                </div>
                <div class="absolute -top-1 -right-1 w-7 h-7 rounded-full bg-gradient-to-tr from-coralPrimary to-amberAccent flex items-center justify-center text-xs text-white shadow-md animate-bounce">
                  ✨
                </div>
              </div>

              <div class="space-y-1.5 max-w-sm">
                <h4 class="text-base font-bold text-white">Interactive Geo-Map Awaiting Coordinates</h4>
                <p class="text-xs text-gray-400 leading-relaxed">
                  Enter your destination in <span class="text-coralPrimary font-semibold">Step 1</span> and generate your itinerary to plot real-time GPS landmarks, transport hubs, and student budget hotspots.
                </p>
              </div>

              <div class="grid grid-cols-2 gap-2.5 w-full max-w-xs pt-2 text-[11px] text-gray-400">
                <div class="map-pill-badge p-2.5 rounded-xl bg-white/5 border border-white/10 flex items-center gap-2">
                  <span class="text-base">📍</span> <span>Landmark Pins</span>
                </div>
                <div class="map-pill-badge p-2.5 rounded-xl bg-white/5 border border-white/10 flex items-center gap-2">
                  <span class="text-base">🧭</span> <span>Route Guidance</span>
                </div>
                <div class="map-pill-badge p-2.5 rounded-xl bg-white/5 border border-white/10 flex items-center gap-2">
                  <span class="text-base">🍜</span> <span>Food Hubs</span>
                </div>
                <div class="map-pill-badge p-2.5 rounded-xl bg-white/5 border border-white/10 flex items-center gap-2">
                  <span class="text-base">🎟️</span> <span>Student Deals</span>
                </div>
              </div>
            </div>

            <!-- Leaflet Map (Hidden initially until trip coordinates are loaded) -->
            <div id="map" class="hidden w-full h-full min-h-[440px]"></div>
          </div>
        </div>

      </div>

      <!-- Grid 3: Your Itinerary Blueprint (Full Width: Combination of 1 & 2 Below Top Grids) -->
      <div id="plannerResultsContainer" class="w-full space-y-6">
        <div id="plannerErr" class="hidden p-4 rounded-2xl bg-red-950/80 border border-red-800 text-red-200 text-sm"></div>

        <!-- Initial Placeholder when no trip is planned yet -->
        <div id="plannerPlaceholder" class="glass-card rounded-3xl p-10 sm:p-12 text-center space-y-4 shadow-xl border border-white/10">
          <div class="w-16 h-16 rounded-3xl bg-coralPrimary/10 border border-coralPrimary/20 flex items-center justify-center text-3xl mx-auto shadow-inner">
            📝
          </div>
          <h3 class="text-2xl font-extrabold text-white">Your Itinerary Blueprint</h3>
          <p class="text-gray-400 text-xs sm:text-sm max-w-xl mx-auto leading-relaxed">
            Customize your parameters above and click "Generate AI Itinerary". Your comprehensive day-by-day itinerary, budget breakdown matrix, and local student tips will appear here in full widescreen format spanning the entire width.
          </p>
        </div>

        <!-- Loading State -->
        <div id="plannerLoading" class="hidden glass-card rounded-3xl p-12 text-center space-y-4 border border-coralPrimary/30 shadow-2xl">
          <div class="w-14 h-14 border-4 border-coralPrimary/20 border-t-coralPrimary rounded-full animate-spin mx-auto"></div>
          <h3 class="text-xl font-bold text-white">Architecting Your Trip...</h3>
          <p class="text-xs text-coralPrimary animate-pulse">Calculating regional budget breakdowns and geocoding landmark pins...</p>
        </div>

        <!-- Itinerary Blueprint Card (Full Width: Combination of 1 and 2 below top grids) -->
        <div id="plannerResults" class="hidden glass-card p-6 sm:p-10 rounded-3xl border border-white/10 space-y-6 shadow-2xl">
          <div class="flex flex-wrap items-center justify-between gap-4 pb-5 border-b border-white/10">
            <div>
              <h3 class="text-xl sm:text-2xl font-extrabold text-white flex items-center gap-2">
                <span>📝</span> Your Itinerary Blueprint
              </h3>
              <p class="text-xs sm:text-sm text-gray-400 mt-0.5">Comprehensive day-by-day plan, budget breakdown & student hacks</p>
            </div>
            <div class="flex flex-wrap items-center gap-2.5">
              <button onclick="saveTrip()" class="btn-secondary px-4 py-2 rounded-xl text-xs font-bold flex items-center gap-1.5 shadow-sm">
                <span>💾 Save Trip</span>
              </button>
              <button onclick="copyTrip()" class="btn-secondary px-4 py-2 rounded-xl text-xs font-bold flex items-center gap-1.5 shadow-sm">
                <span>📋 Copy</span>
              </button>
              <button onclick="downloadTripPDF()" class="btn-gradient px-5 py-2 rounded-xl text-xs font-bold flex items-center gap-1.5 shadow-md">
                <span>⬇️ Export PDF</span>
              </button>
            </div>
          </div>

          <div id="itineraryView" class="itinerary-prose text-sm p-5 sm:p-8 rounded-2xl bg-spaceDark/70 border border-white/5 shadow-inner"></div>
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
            <div><label class="text-xs font-bold text-gray-300">Days</label><input type="number" id="bDays" value="4" min="1" max="90" class="w-full px-3 py-2 bg-spaceDark border border-white/15 rounded-xl text-sm text-white" oninput="calcBudget()" /></div>
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
    <section id="page-packing" class="hidden space-y-8 max-w-5xl mx-auto">
      <div class="text-center space-y-2">
        <span class="text-xs font-bold uppercase tracking-wider text-emeraldAccent">🎒 Never Forget Essentials</span>
        <h2 class="text-3xl font-extrabold text-white">Smart Student Packing Checklist</h2>
        <p class="text-gray-400 text-sm max-w-lg mx-auto">
          Customized checklist tailored to your planned destination, itinerary vibe, and personal essentials.
        </p>
      </div>

      <!-- Overall Progress & Vibe Selector Toolbar -->
      <div class="glass-card p-6 sm:p-7 rounded-3xl border border-white/10 space-y-5 shadow-xl">
        <div class="flex flex-wrap items-center justify-between gap-4">
          <div class="flex items-center gap-2">
            <span class="text-xl">📍</span>
            <div>
              <span class="text-[11px] font-bold text-gray-400 uppercase tracking-wider">Itinerary & Destination Vibe</span>
              <div class="flex items-center gap-2 mt-0.5">
                <select
                  id="packVibeSelector"
                  onchange="onPackVibeChange(this.value)"
                  class="px-3 py-1.5 bg-spaceDark border border-white/15 rounded-xl text-xs font-semibold text-white focus:outline-none focus:border-emeraldAccent"
                >
                  <option value="auto">📍 Auto-detect from Itinerary / Planner</option>
                  <option value="beach">🏖️ Beach, Island & Coastal (Goa, Bali, Phuket)</option>
                  <option value="mountain">🏔️ Mountains, Hiking & Trekking (Manali, Alps)</option>
                  <option value="city">🏙️ City Sightseeing & Culture (Tokyo, Rome, London)</option>
                  <option value="winter">❄️ Cold Weather & Snow (Alps, Sapporo, Kashmir)</option>
                  <option value="hostel">🎒 Classic Backpacker & Hostel Dorm</option>
                </select>
                <span id="packVibeBadge" class="text-[10px] font-bold px-2 py-1 rounded-full bg-emeraldAccent/20 text-emeraldAccent border border-emeraldAccent/30">Auto Active</span>
              </div>
            </div>
          </div>

          <div class="flex items-center gap-2">
            <button onclick="checkAllPacking(true)" class="btn-secondary px-3 py-1.5 rounded-xl text-xs font-semibold">
              ✅ Check All
            </button>
            <button onclick="checkAllPacking(false)" class="btn-secondary px-3 py-1.5 rounded-xl text-xs font-semibold">
              🔄 Uncheck All
            </button>
            <button onclick="resetPackingDefaults()" class="p-1.5 rounded-xl text-xs text-gray-400 hover:text-red-400 hover:bg-white/5 transition" title="Reset to Defaults">
              🗑️
            </button>
          </div>
        </div>

        <!-- Progress Bar -->
        <div class="space-y-2 pt-2 border-t border-white/10">
          <div class="flex justify-between text-xs font-bold">
            <span class="text-gray-300">Total Packing Progress</span>
            <span class="text-emeraldAccent font-extrabold" id="packProgressText">0% Packed</span>
          </div>
          <div class="h-3 w-full bg-gray-800 rounded-full overflow-hidden">
            <div id="packProgressBar" style="width: 0%" class="h-full bg-gradient-to-r from-coralPrimary via-amberAccent to-emeraldAccent transition-all duration-300"></div>
          </div>
        </div>
      </div>

      <!-- Add Custom Item Card -->
      <div class="glass-card p-6 rounded-3xl border border-white/10 space-y-4 shadow-xl">
        <h3 class="text-sm font-bold text-white flex items-center gap-2">
          <span>➕</span> Add Custom Item
        </h3>
        <div class="flex flex-col sm:flex-row gap-3">
          <input
            type="text"
            id="customPackInput"
            placeholder="e.g. GoPro Hero 12, Extra Contact Lenses, Power Strip, Sunglasses..."
            class="flex-grow px-4 py-2.5 bg-spaceDark border border-white/15 rounded-xl text-xs text-white placeholder-gray-500 focus:outline-none focus:border-emeraldAccent shadow-inner"
            onkeypress="if(event.key === 'Enter') addCustomPackingItem()"
          />
          <select
            id="customPackCategory"
            class="px-3 py-2.5 bg-spaceDark border border-white/15 rounded-xl text-xs text-white focus:outline-none focus:border-emeraldAccent"
          >
            <option value="custom">✨ Custom Personal Items</option>
            <option value="docs">📄 Documents & Finance</option>
            <option value="tech">🔌 Tech & Gadgets</option>
            <option value="clothing">👕 Clothing & Footwear</option>
            <option value="health">💊 Toiletries & Health</option>
            <option value="dest">📍 Destination Specific</option>
          </select>
          <button
            onclick="addCustomPackingItem()"
            class="btn-gradient px-5 py-2.5 rounded-xl text-xs font-bold flex items-center justify-center gap-1.5 whitespace-nowrap"
          >
            <span>+ Add to List</span>
          </button>
        </div>
      </div>

      <!-- Category Filter Pills -->
      <div class="flex flex-wrap gap-2 items-center" id="packCategoryFilterPills">
        <!-- Injected via JS -->
      </div>

      <!-- Categorized Grid Cards -->
      <div id="packingListContainer" class="grid grid-cols-1 md:grid-cols-2 gap-6">
        <!-- Injected via JS -->
      </div>
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

  <!-- Toast Notification Container -->
  <div id="toastContainer" class="fixed bottom-6 right-6 z-50 flex flex-col gap-3 max-w-sm w-full pointer-events-none"></div>

  <!-- Modern 3D Glass Confirmation Modal -->
  <div id="confirmModalBackdrop" class="fixed inset-0 z-50 bg-black/75 backdrop-blur-md hidden flex items-center justify-center p-4 transition-opacity duration-300">
    <div id="confirmModalCard" class="glass-card max-w-md w-full p-6 sm:p-7 rounded-3xl border border-white/15 shadow-2xl space-y-5 transform scale-95 transition-all duration-300">
      <div class="flex items-center gap-3">
        <div id="confirmModalIconBg" class="w-12 h-12 rounded-2xl bg-coralPrimary/20 border border-coralPrimary/30 flex items-center justify-center text-2xl shrink-0">
          <span id="confirmModalIcon">⚠️</span>
        </div>
        <div>
          <h3 id="confirmModalTitle" class="text-lg font-bold text-white">Confirmation</h3>
          <p id="confirmModalSubtitle" class="text-xs text-gray-400">Please review before proceeding</p>
        </div>
      </div>
      <p id="confirmModalMessage" class="text-xs sm:text-sm text-gray-300 leading-relaxed">
        Are you sure you want to proceed?
      </p>
      <div class="flex items-center justify-end gap-3 pt-3 border-t border-white/10">
        <button id="confirmModalCancelBtn" class="btn-secondary px-4 py-2 rounded-xl text-xs font-bold">
          Cancel
        </button>
        <button id="confirmModalConfirmBtn" class="btn-gradient px-5 py-2 rounded-xl text-xs font-bold shadow-lg">
          Confirm
        </button>
      </div>
    </div>
  </div>

  <!-- ==================== DISTINCT MINIMALIST MODERN FOOTER ==================== -->
  <footer class="mt-24 pb-12 px-4 sm:px-6 lg:px-8 relative" style="z-index: 10;">
    <div class="max-w-3xl mx-auto glass-card p-6 sm:p-8 rounded-3xl border border-white/10 text-center space-y-4 shadow-2xl relative overflow-hidden">
      
      <!-- Subtle Ambient Glow Behind Footer -->
      <div class="absolute inset-0 bg-gradient-to-r from-coralPrimary/5 via-amberAccent/5 to-cyanAccent/5 pointer-events-none"></div>

      <!-- Centered Brand & Status Pill -->
      <div class="inline-flex items-center gap-2.5 px-4 py-1.5 rounded-full bg-white/5 border border-white/10 text-xs font-semibold text-white shadow-inner">
        <span class="text-coralPrimary text-base">✈️</span>
        <span class="font-extrabold tracking-tight brand-logo-title">RoamAI</span>
        <span class="text-gray-500">•</span>
        <span class="flex items-center gap-1.5 text-emeraldAccent font-bold text-[11px]">
          <span class="w-1.5 h-1.5 rounded-full bg-emeraldAccent animate-pulse"></span> Free for Students
        </span>
      </div>

      <!-- Inspirational Travel Micro-Copy -->
      <p class="text-xs sm:text-sm text-gray-300 font-medium leading-relaxed max-w-lg mx-auto">
        "Go further, spend smarter, explore everywhere."
      </p>

      <!-- Bottom Metadata Badges & Attribution -->
      <div class="pt-4 border-t border-white/10 space-y-2.5">
        <div class="flex flex-wrap items-center justify-center gap-4 text-[11px] text-gray-400 font-medium">
          <span class="flex items-center gap-1"><span>🌍</span> 9-Region Currency Engine</span>
          <span class="text-gray-600">•</span>
          <span class="flex items-center gap-1"><span>⚡</span> Sub-Second AI Planning</span>
          <span class="text-gray-600">•</span>
          <span class="flex items-center gap-1"><span>🎒</span> Smart Packing Architect</span>
        </div>
        
        <!-- Creator Attribution Text -->
        <p class="text-xs text-gray-400 font-medium pt-0.5">
          © RoamAI • Built with <span class="text-rose-500 animate-pulse">❤️</span> by <span class="text-coralPrimary font-bold hover:underline cursor-pointer">Elesh Kapri</span> for students worldwide
        </p>
      </div>

    </div>
  </footer>

  <!-- ==================== JAVASCRIPT LOGIC ==================== -->
  <script>
    // ========================================================
    // THEME MOOD SYSTEM (DEVICE PREFERRED & USER TOGGLEABLE)
    // ========================================================
    let currentTheme = 'dark';

    function initThemeMood() {
      const savedTheme = localStorage.getItem('roamai_theme');
      if (savedTheme) {
        setThemeMood(savedTheme, false);
      } else {
        // First prefer the mood of the site by device preference
        const systemPrefersLight = window.matchMedia && window.matchMedia('(prefers-color-scheme: light)').matches;
        setThemeMood(systemPrefersLight ? 'light' : 'dark', false);
      }

      // Automatically sync if system theme changes and user hasn't set manual override
      if (window.matchMedia) {
        window.matchMedia('(prefers-color-scheme: light)').addEventListener('change', e => {
          if (!localStorage.getItem('roamai_theme')) {
            setThemeMood(e.matches ? 'light' : 'dark', false);
          }
        });
      }
    }

    function setThemeMood(theme, saveManual = true) {
      currentTheme = theme;
      if (saveManual) {
        try { localStorage.setItem('roamai_theme', theme); } catch(e) {}
      }

      const isLight = theme === 'light';
      document.documentElement.classList.toggle('light-theme', isLight);
      document.body.classList.toggle('light-theme', isLight);

      const btn = document.getElementById('themeToggleBtn');
      if (btn) {
        btn.title = isLight ? 'Switch to Dark Mode (🌙)' : 'Switch to Light Mode (☀️)';
      }
    }

    function toggleThemeMood() {
      const newTheme = currentTheme === 'light' ? 'dark' : 'light';
      setThemeMood(newTheme, true);
      showToast(`Switched to ${newTheme === 'light' ? 'Daylight Light ☀️' : 'Deep Space Dark 🌙'} mode`, 'info');
    }

    // ========================================================
    // SMART GLASS NAVBAR AUTO-HIDE / REVEAL ON SCROLL
    // ========================================================
    let lastScrollY = window.scrollY;
    const scrollThreshold = 10;
    const headerEl = document.getElementById('mainHeader');

    window.addEventListener('scroll', () => {
      const currentScrollY = window.scrollY;
      if (!headerEl) return;

      if (currentScrollY > 70) {
        headerEl.classList.add('nav-scrolled');
        if (currentScrollY > lastScrollY + scrollThreshold) {
          // Scrolling Down -> Hide Navbar with smooth upward slide
          headerEl.classList.add('nav-hidden');
        } else if (currentScrollY < lastScrollY - scrollThreshold) {
          // Scrolling Up -> Reveal Navbar with smooth spring drop
          headerEl.classList.remove('nav-hidden');
        }
      } else {
        // At top of page -> Keep visible and clean
        headerEl.classList.remove('nav-scrolled');
        headerEl.classList.remove('nav-hidden');
      }

      lastScrollY = Math.max(0, currentScrollY);
    }, { passive: true });

    // ========================================================
    // TOAST NOTIFICATION & CONFIRMATION MODAL SYSTEM
    // ========================================================
    function showToast(message, type = 'success', duration = 3500) {
      const container = document.getElementById('toastContainer');
      if (!container) return;

      const icons = {
        success: '✅',
        error: '❌',
        warning: '⚠️',
        info: 'ℹ️'
      };

      const borderColors = {
        success: 'border-emeraldAccent/40 shadow-emeraldAccent/20',
        error: 'border-red-500/40 shadow-red-500/20',
        warning: 'border-amberAccent/40 shadow-amberAccent/20',
        info: 'border-cyanAccent/40 shadow-cyanAccent/20'
      };

      const titleColors = {
        success: 'text-emeraldAccent',
        error: 'text-red-400',
        warning: 'text-amberAccent',
        info: 'text-cyanAccent'
      };

      const titles = {
        success: 'Completed',
        error: 'Action Failed',
        warning: 'Attention',
        info: 'Notice'
      };

      const toastId = 'toast_' + Date.now();
      const toastEl = document.createElement('div');
      toastEl.id = toastId;
      toastEl.className = `glass-card p-4 rounded-2xl border ${borderColors[type] || borderColors.info} shadow-2xl flex items-start gap-3 pointer-events-auto transition-all duration-300 transform translate-y-4 opacity-0`;
      
      toastEl.innerHTML = `
        <span class="text-xl shrink-0">${icons[type] || 'ℹ️'}</span>
        <div class="flex-grow">
          <div class="flex items-center justify-between">
            <h4 class="text-xs font-extrabold uppercase tracking-wider ${titleColors[type] || titleColors.info}">${titles[type]}</h4>
            <button onclick="document.getElementById('${toastId}').remove()" class="text-xs text-gray-400 hover:text-white p-0.5 ml-2">✕</button>
          </div>
          <p class="text-xs text-gray-200 mt-0.5 leading-relaxed">${message}</p>
        </div>
      `;

      container.appendChild(toastEl);

      // Animate in
      setTimeout(() => {
        toastEl.classList.remove('translate-y-4', 'opacity-0');
        toastEl.classList.add('translate-y-0', 'opacity-100');
      }, 20);

      // Auto dismiss
      setTimeout(() => {
        toastEl.classList.add('translate-y-4', 'opacity-0');
        setTimeout(() => { toastEl.remove(); }, 300);
      }, duration);
    }

    let currentModalConfirmHandler = null;

    function showConfirmModal({ title, message, icon = '⚠️', confirmText = 'Confirm', onConfirm }) {
      const backdrop = document.getElementById('confirmModalBackdrop');
      const card = document.getElementById('confirmModalCard');
      const titleEl = document.getElementById('confirmModalTitle');
      const msgEl = document.getElementById('confirmModalMessage');
      const iconEl = document.getElementById('confirmModalIcon');
      const confirmBtn = document.getElementById('confirmModalConfirmBtn');
      const cancelBtn = document.getElementById('confirmModalCancelBtn');

      titleEl.innerText = title;
      msgEl.innerText = message;
      iconEl.innerText = icon;
      confirmBtn.innerText = confirmText;

      currentModalConfirmHandler = () => {
        hideConfirmModal();
        if (typeof onConfirm === 'function') onConfirm();
      };

      confirmBtn.onclick = currentModalConfirmHandler;
      cancelBtn.onclick = hideConfirmModal;
      backdrop.onclick = (e) => { if (e.target === backdrop) hideConfirmModal(); };

      backdrop.classList.remove('hidden');
      setTimeout(() => {
        card.classList.remove('scale-95');
        card.classList.add('scale-100');
      }, 20);
    }

    function hideConfirmModal() {
      const backdrop = document.getElementById('confirmModalBackdrop');
      const card = document.getElementById('confirmModalCard');
      card.classList.remove('scale-100');
      card.classList.add('scale-95');
      setTimeout(() => { backdrop.classList.add('hidden'); }, 150);
    }

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

      // Update Hotspot Cards Costs dynamically for all 14 destinations
      updateHotspotCosts();

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
      document.documentElement.setAttribute('data-active-page', page);
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
      if (page === 'planner') {
        if (mapInstance && currentTrip) {
          setTimeout(() => mapInstance.invalidateSize(), 200);
        }
      }
      if (saveState) {
        window.scrollTo({ top: 0, behavior: 'smooth' });
      }
    }

    // ========================================================
    // PLANNER FORM PERSISTENCE & SESSION RESET SYSTEM
    // (Uses sessionStorage: persists during tab refresh, but
    // automatically resets when site is closed & reopened)
    // ========================================================
    function savePlannerDraft() {
      try {
        const draft = {
          destination: document.getElementById('plannerDest')?.value || '',
          days: document.getElementById('plannerDays')?.value || '3',
          tier: document.getElementById('plannerTier')?.value || 'Student (Low)',
          budgetCap: document.getElementById('plannerBudgetCap')?.value || '',
          mustVisit: document.getElementById('plannerMustVisit')?.value || '',
          pace: document.getElementById('plannerPace')?.value || 'Balanced',
          interests: selectedInterests
        };
        sessionStorage.setItem('roamai_planner_draft', JSON.stringify(draft));
      } catch (e) {}
    }

    function initPlannerDraft() {
      try {
        // Clean up any legacy persistent localStorage from prior versions
        try {
          localStorage.removeItem('roamai_planner_draft');
          localStorage.removeItem('roamai_active_trip');
        } catch (e) {}

        // 1. Restore Form Draft from current session
        const draftStr = sessionStorage.getItem('roamai_planner_draft');
        if (draftStr) {
          const draft = JSON.parse(draftStr);
          if (draft.destination) document.getElementById('plannerDest').value = draft.destination;
          if (draft.days) {
            document.getElementById('plannerDays').value = draft.days;
            document.getElementById('daysDisp').innerText = `${draft.days} Days`;
          }
          if (draft.tier) document.getElementById('plannerTier').value = draft.tier;
          if (draft.budgetCap) document.getElementById('plannerBudgetCap').value = draft.budgetCap;
          if (draft.mustVisit) document.getElementById('plannerMustVisit').value = draft.mustVisit;
          if (draft.pace) document.getElementById('plannerPace').value = draft.pace;
          if (Array.isArray(draft.interests) && draft.interests.length > 0) {
            selectedInterests = draft.interests;
            document.querySelectorAll('#interestPills .chip-tag').forEach(tag => {
              const text = tag.innerText.replace(/^[^\\s]+\\s*/, '').trim();
              const isActive = selectedInterests.some(i => text.includes(i) || i.includes(text));
              tag.classList.toggle('active', isActive);
            });
          }
        }

        // 2. Attach Auto-Save listeners to all form controls
        ['plannerDest', 'plannerDays', 'plannerTier', 'plannerBudgetCap', 'plannerMustVisit', 'plannerPace'].forEach(id => {
          const el = document.getElementById(id);
          if (el) {
            el.addEventListener('input', savePlannerDraft);
            el.addEventListener('change', savePlannerDraft);
          }
        });

        // 3. Restore Active Trip in current session if available
        const activeTripStr = sessionStorage.getItem('roamai_active_trip');
        if (activeTripStr) {
          const tripData = JSON.parse(activeTripStr);
          if (tripData && tripData.itinerary) {
            currentTrip = tripData;
            document.getElementById('plannerPlaceholder').classList.add('hidden');
            document.getElementById('plannerResults').classList.remove('hidden');
            document.getElementById('itineraryView').innerHTML = marked.parse(tripData.itinerary);
            if (tripData.trip_summary && tripData.trip_summary.destination) {
              document.getElementById('mapHeading').innerText = `📍 Exploring ${tripData.trip_summary.destination}`;
            }
            renderMap(tripData.destination_coords, tripData.markers);
          }
        }
      } catch (e) {}
    }

    function resetPlannerAll() {
      showConfirmModal({
        title: 'Reset Trip Architect?',
        message: 'This will clear all destination parameters, draft inputs, and reset the current itinerary blueprint.',
        icon: '🔄',
        confirmText: 'Reset Everything',
        onConfirm: () => {
          try {
            sessionStorage.removeItem('roamai_planner_draft');
            sessionStorage.removeItem('roamai_active_trip');
            localStorage.removeItem('roamai_planner_draft');
            localStorage.removeItem('roamai_active_trip');
          } catch (e) {}

          currentTrip = null;

          // Reset Form inputs
          const dest = document.getElementById('plannerDest');
          if (dest) dest.value = '';
          const days = document.getElementById('plannerDays');
          if (days) {
            days.value = '3';
            document.getElementById('daysDisp').innerText = '3 Days';
          }
          const tier = document.getElementById('plannerTier');
          if (tier) tier.value = 'Student (Low)';
          const cap = document.getElementById('plannerBudgetCap');
          if (cap) cap.value = '';
          const must = document.getElementById('plannerMustVisit');
          if (must) must.value = '';
          const pace = document.getElementById('plannerPace');
          if (pace) pace.value = 'Balanced';

          // Reset interest tags to default
          selectedInterests = ['Street Food', 'History & Shrines'];
          document.querySelectorAll('#interestPills .chip-tag').forEach(tag => {
            const text = tag.innerText.replace(/^[^\\s]+\\s*/, '').trim();
            const isActive = selectedInterests.some(i => text.includes(i) || i.includes(text));
            tag.classList.toggle('active', isActive);
          });

          // Reset Map and Itinerary View back to clean template state
          resetMapPlaceholder();
          document.getElementById('plannerResults').classList.add('hidden');
          document.getElementById('plannerPlaceholder').classList.remove('hidden');
          document.getElementById('plannerErr').classList.add('hidden');

          showToast('Trip Architect and itinerary reset back to defaults!', 'info');
        }
      });
    }

    // --- Planner Sidebar & View Mode Controls ---
    let plannerSidebarCollapsed = false;
    let plannerCurrentViewMode = 'all'; // 'all' | 'itinerary' | 'map'

    function togglePlannerSidebar() {
      plannerSidebarCollapsed = !plannerSidebarCollapsed;
      const sidebar = document.getElementById('plannerSidebarCol');
      const results = document.getElementById('plannerResultsCol');
      const btn = document.getElementById('togglePlannerSidebarBtn');
      const icon = document.getElementById('toggleSidebarIcon');
      const text = document.getElementById('toggleSidebarText');

      if (plannerSidebarCollapsed) {
        if (sidebar) sidebar.classList.add('hidden');
        if (results) {
          results.classList.remove('lg:col-span-7');
          results.classList.add('lg:col-span-12');
        }
        if (icon) icon.innerText = '▶';
        if (text) text.innerText = 'Show Form & Parameters';
        if (btn) btn.className = 'btn-gradient px-4 py-2 rounded-xl text-xs font-bold flex items-center gap-2 transition shadow-md';
      } else {
        if (sidebar) sidebar.classList.remove('hidden');
        if (results) {
          results.classList.remove('lg:col-span-12');
          results.classList.add('lg:col-span-7');
        }
        if (icon) icon.innerText = '◀';
        if (text) text.innerText = 'Hide Form & Maximize View';
        if (btn) btn.className = 'btn-secondary px-4 py-2 rounded-xl text-xs font-bold flex items-center gap-2 transition shadow-sm';
      }

      if (mapInstance) {
        setTimeout(() => mapInstance.invalidateSize(), 250);
      }
    }

    function setPlannerViewMode(mode) {
      plannerCurrentViewMode = mode;
      const mapCard = document.getElementById('plannerMapCard');
      const itinCard = document.getElementById('plannerItineraryCard');

      const btnAll = document.getElementById('viewBtnAll');
      const btnItin = document.getElementById('viewBtnItinerary');
      const btnMap = document.getElementById('viewBtnMap');

      if (btnAll) {
        btnAll.className = mode === 'all' 
          ? 'px-3 py-1.5 rounded-lg font-bold bg-coralPrimary text-white shadow transition' 
          : 'px-3 py-1.5 rounded-lg font-medium text-gray-400 hover:text-white transition';
      }
      if (btnItin) {
        btnItin.className = mode === 'itinerary' 
          ? 'px-3 py-1.5 rounded-lg font-bold bg-coralPrimary text-white shadow transition' 
          : 'px-3 py-1.5 rounded-lg font-medium text-gray-400 hover:text-white transition';
      }
      if (btnMap) {
        btnMap.className = mode === 'map' 
          ? 'px-3 py-1.5 rounded-lg font-bold bg-coralPrimary text-white shadow transition' 
          : 'px-3 py-1.5 rounded-lg font-medium text-gray-400 hover:text-white transition';
      }

      if (mode === 'all') {
        if (mapCard) mapCard.classList.remove('hidden');
        if (itinCard) itinCard.classList.remove('hidden');
      } else if (mode === 'itinerary') {
        if (mapCard) mapCard.classList.add('hidden');
        if (itinCard) itinCard.classList.remove('hidden');
      } else if (mode === 'map') {
        if (mapCard) mapCard.classList.remove('hidden');
        if (itinCard) itinCard.classList.add('hidden');
      }

      if (mapInstance && (mode === 'all' || mode === 'map')) {
        setTimeout(() => mapInstance.invalidateSize(), 250);
      }
    }

    // ========================================================
    // TRENDING STUDENT DESTINATIONS: NATIONAL & INTERNATIONAL FILTERS
    // ========================================================
    let activeHotspotScope = 'all';
    let activeHotspotCat = 'all';

    function setHotspotScope(scope) {
      activeHotspotScope = scope;
      document.querySelectorAll('.hotspot-scope-btn').forEach(btn => {
        const isTarget = btn.getAttribute('data-scope') === scope;
        if (isTarget) {
          btn.className = 'hotspot-scope-btn active text-xs px-4 py-2 rounded-full border border-transparent bg-gradient-to-r from-coralPrimary to-amberAccent text-white font-extrabold transition shadow-md flex items-center gap-1.5';
        } else {
          btn.className = 'hotspot-scope-btn text-xs px-4 py-2 rounded-full border border-white/10 bg-white/5 text-gray-300 hover:text-white hover:border-white/20 transition flex items-center gap-1.5';
        }
      });
      applyHotspotFilters();
    }

    function setHotspotCategory(cat) {
      activeHotspotCat = cat;
      document.querySelectorAll('.hotspot-filter-btn').forEach(btn => {
        const isTarget = btn.getAttribute('data-cat') === cat;
        if (isTarget) {
          btn.className = 'hotspot-filter-btn active text-xs px-3.5 py-1.5 rounded-full border border-transparent bg-white/20 text-white font-bold transition shadow-sm';
        } else {
          btn.className = 'hotspot-filter-btn text-xs px-3.5 py-1.5 rounded-full border border-white/10 bg-white/5 text-gray-400 hover:text-white transition';
        }
      });
      applyHotspotFilters();
    }

    function filterHotspotGrid(category) {
      setHotspotCategory(category);
    }

    function applyHotspotFilters() {
      const cards = document.querySelectorAll('.hotspot-card');
      let visibleCount = 0;

      cards.forEach(card => {
        const scope = card.getAttribute('data-scope') || '';
        const cats = card.getAttribute('data-cat') || '';

        const scopeMatch = (activeHotspotScope === 'all' || scope === activeHotspotScope);
        const catMatch = (activeHotspotCat === 'all' || cats.includes(activeHotspotCat));

        if (scopeMatch && catMatch) {
          card.classList.remove('hidden');
          visibleCount++;
        } else {
          card.classList.add('hidden');
        }
      });

      const emptyMsg = document.getElementById('hotspotEmptyMsg');
      if (emptyMsg) {
        emptyMsg.classList.toggle('hidden', visibleCount > 0);
      }
    }

    function updateHotspotCosts() {
      const reg = REGIONS[activeRegionKey] || REGIONS.INR;
      document.querySelectorAll('.hotspot-card').forEach(card => {
        const costInr = parseFloat(card.getAttribute('data-cost-inr')) || 3000;
        const costEl = card.querySelector('.hotspot-cost-val');
        if (costEl) {
          if (activeRegionKey === 'INR') {
            costEl.innerText = `💰 ~₹${costInr.toLocaleString()} / day`;
          } else {
            const inUsd = costInr / 80;
            const converted = Math.round(inUsd * reg.multiplier);
            costEl.innerText = `💰 ~${reg.sym}${converted.toLocaleString()} / day`;
          }
        }
      });
    }

    function toggleTag(el, tag) {
      if (selectedInterests.includes(tag)) {
        selectedInterests = selectedInterests.filter(t => t !== tag);
        el.classList.remove('active');
      } else {
        selectedInterests.push(tag);
        el.classList.add('active');
      }
      savePlannerDraft();
    }

    function startQuickTrip() {
      const dest = document.getElementById('heroDestInput').value.trim();
      if (dest) {
        document.getElementById('plannerDest').value = dest;
        savePlannerDraft();
      }
      switchPage('planner');
    }

    function quickPlanHotspot(dest, days, tier, tags) {
      document.getElementById('plannerDest').value = dest;
      document.getElementById('plannerDays').value = days;
      document.getElementById('daysDisp').innerText = days + ' Days';
      document.getElementById('plannerTier').value = tier;
      selectedInterests = tags;
      savePlannerDraft();
      switchPage('planner');
      planTrip();
    }

    async function planTrip() {
      const destination = document.getElementById('plannerDest').value.trim();
      if (!destination) {
        showToast('Please enter a destination to generate an itinerary.', 'warning');
        return;
      }

      savePlannerDraft();

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
        try { sessionStorage.setItem('roamai_active_trip', JSON.stringify(data)); } catch (e) {}

        // Render Map
        renderMap(data.destination_coords, data.markers);

        // Render Markdown
        document.getElementById('itineraryView').innerHTML = marked.parse(data.itinerary);
        document.getElementById('mapHeading').innerText = `📍 Exploring ${destination}`;

        document.getElementById('plannerLoading').classList.add('hidden');
        document.getElementById('plannerResults').classList.remove('hidden');
        showToast(`Itinerary for ${destination} generated successfully!`, 'success');
        setTimeout(() => {
          const resultsEl = document.getElementById('plannerResults');
          if (resultsEl) resultsEl.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }, 150);
      } catch (err) {
        document.getElementById('plannerLoading').classList.add('hidden');
        const errBox = document.getElementById('plannerErr');
        errBox.innerText = `Error: ${err.message}`;
        errBox.classList.remove('hidden');
        showToast(err.message || 'AI Generation failed. Please try again.', 'error');
      }
    }

    function renderMap(center, markers = []) {
      const placeholder = document.getElementById('mapPlaceholder');
      const mapEl = document.getElementById('map');
      if (placeholder) placeholder.classList.add('hidden');
      if (mapEl) mapEl.classList.remove('hidden');

      const badge = document.getElementById('mapStatusBadge');
      if (badge) {
        badge.innerText = 'Live GPS Pins';
        badge.className = 'text-xs text-cyanAccent font-semibold px-2.5 py-0.5 rounded-full bg-cyanAccent/10 border border-cyanAccent/20';
      }

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

    function resetMapPlaceholder() {
      const placeholder = document.getElementById('mapPlaceholder');
      const mapEl = document.getElementById('map');
      if (placeholder) placeholder.classList.remove('hidden');
      if (mapEl) mapEl.classList.add('hidden');

      const badge = document.getElementById('mapStatusBadge');
      if (badge) {
        badge.innerText = 'Awaiting Destination';
        badge.className = 'text-xs text-amberAccent font-semibold px-2.5 py-0.5 rounded-full bg-amberAccent/10 border border-amberAccent/20';
      }
    }

    function copyTrip() {
      if (currentTrip) {
        navigator.clipboard.writeText(currentTrip.itinerary);
        showToast('Itinerary copied to clipboard!', 'success');
      }
    }

    function downloadTripPDF() {
      if (!currentTrip) return;
      showToast('Generating and downloading your PDF itinerary...', 'info');
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

    // --- Robust Saved Trips Storage & Management ---
    function getSavedTrips() {
      try {
        const raw = localStorage.getItem('roamai_saved_trips') || localStorage.getItem('saved_trips');
        const parsed = raw ? JSON.parse(raw) : [];
        return Array.isArray(parsed) ? parsed : [];
      } catch (e) {
        console.error('Failed to parse saved trips', e);
        return [];
      }
    }

    function persistSavedTrips(trips) {
      try {
        const jsonStr = JSON.stringify(trips);
        localStorage.setItem('roamai_saved_trips', jsonStr);
        localStorage.setItem('saved_trips', jsonStr);
        updateSavedCount();
      } catch (e) {
        console.error('Failed to persist saved trips', e);
      }
    }

    function updateSavedCount() {
      try {
        const trips = getSavedTrips();
        const countEl = document.getElementById('savedCount');
        if (countEl) countEl.innerText = trips.length;
      } catch (e) {
        console.error('Error updating saved count', e);
      }
    }

    function saveTrip() {
      if (!currentTrip) {
        showToast('No active trip to save. Plan a trip first!', 'warning');
        return;
      }

      const trips = getSavedTrips();
      const dest = currentTrip.trip_summary?.destination || document.getElementById('plannerDest')?.value || 'Trip';
      const days = currentTrip.trip_summary?.days || document.getElementById('plannerDays')?.value || 3;

      // Prevent exact duplicate saves within same session
      const existingIdx = trips.findIndex(t => t.destination.toLowerCase() === dest.toLowerCase() && t.itinerary === currentTrip.itinerary);
      if (existingIdx !== -1) {
        showToast(`Trip to ${dest} is already saved in your vault!`, 'info');
        return;
      }

      const newTrip = {
        id: 'trip_' + Date.now(),
        destination: dest,
        days: days,
        itinerary: currentTrip.itinerary,
        markers: currentTrip.markers || [],
        destination_coords: currentTrip.destination_coords || null,
        date: new Date().toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
      };

      trips.unshift(newTrip);
      persistSavedTrips(trips);

      const countEl = document.getElementById('savedCount');
      if (countEl) countEl.innerText = trips.length;

      showToast(`Trip to ${dest} saved to offline vault!`, 'success');
      renderSaved();
    }

    function renderSaved() {
      const trips = getSavedTrips();
      const countEl = document.getElementById('savedCount');
      if (countEl) countEl.innerText = trips.length;

      const grid = document.getElementById('savedGrid');
      const empty = document.getElementById('savedEmpty');
      if (!grid || !empty) return;

      if (trips.length === 0) {
        grid.innerHTML = '';
        empty.classList.remove('hidden');
        return;
      }

      empty.classList.add('hidden');
      grid.innerHTML = trips.map(t => `
        <div class="glass-card p-6 rounded-3xl border border-white/10 space-y-4 shadow-xl flex flex-col justify-between group hover:border-coralPrimary/40 transition">
          <div class="space-y-3">
            <div class="flex items-start justify-between gap-2">
              <h4 class="text-base font-extrabold text-white group-hover:text-coralPrimary transition">${t.destination}</h4>
              <span class="text-xs text-coralPrimary font-bold px-2.5 py-0.5 rounded-full bg-coralPrimary/10 border border-coralPrimary/20 whitespace-nowrap">${t.days} Days</span>
            </div>
            <p class="text-xs text-gray-400 flex items-center gap-1.5">
              <span>📅</span> Saved: ${t.date}
            </p>
          </div>

          <div class="space-y-2 pt-2 border-t border-white/10">
            <button onclick="loadSavedTrip('${t.id}')" class="w-full btn-gradient py-2.5 rounded-xl text-xs font-bold flex items-center justify-center gap-1.5 shadow-md">
              <span>🚀 View Itinerary & Map</span>
            </button>
            <div class="flex items-center gap-2">
              <button onclick="downloadSavedTripPDF('${t.id}')" class="flex-grow btn-secondary py-2 rounded-xl text-xs font-semibold flex items-center justify-center gap-1 text-gray-300 hover:text-white">
                <span>⬇️ PDF</span>
              </button>
              <button onclick="deleteSavedTrip('${t.id}')" class="p-2 rounded-xl text-xs text-gray-400 hover:text-red-400 hover:bg-white/5 border border-white/5 transition" title="Delete Saved Trip">
                🗑️
              </button>
            </div>
          </div>
        </div>
      `).join('');
    }

    function loadSavedTrip(id) {
      const trips = getSavedTrips();
      const trip = trips.find(t => String(t.id) === String(id));
      if (!trip) {
        showToast('Could not find saved trip details.', 'error');
        return;
      }

      currentTrip = {
        trip_summary: { destination: trip.destination, days: trip.days },
        itinerary: trip.itinerary,
        markers: trip.markers || [],
        destination_coords: trip.destination_coords || null
      };

      try {
        sessionStorage.setItem('roamai_active_trip', JSON.stringify(currentTrip));
      } catch (e) {}

      document.getElementById('plannerDest').value = trip.destination;
      document.getElementById('plannerDays').value = trip.days || 3;
      const daysDisp = document.getElementById('daysDisp');
      if (daysDisp) daysDisp.innerText = (trip.days || 3) + ' Days';
      savePlannerDraft();

      switchPage('planner');

      document.getElementById('plannerPlaceholder').classList.add('hidden');
      document.getElementById('plannerLoading').classList.add('hidden');
      document.getElementById('plannerResults').classList.remove('hidden');

      document.getElementById('itineraryView').innerHTML = marked.parse(trip.itinerary);
      document.getElementById('mapHeading').innerText = `📍 Exploring ${trip.destination}`;

      if (trip.destination_coords || (trip.markers && trip.markers.length > 0)) {
        renderMap(trip.destination_coords, trip.markers);
      }

      showToast(`Loaded saved itinerary for ${trip.destination}`, 'info');
    }

    function downloadSavedTripPDF(id) {
      const trips = getSavedTrips();
      const trip = trips.find(t => String(t.id) === String(id));
      if (!trip) return;

      showToast('Preparing PDF export...', 'info');
      const tempDiv = document.createElement('div');
      tempDiv.className = 'itinerary-prose p-6 bg-slate-900 text-white rounded-xl';
      tempDiv.innerHTML = marked.parse(trip.itinerary);

      const opt = {
        margin: [10, 10, 10, 10],
        filename: `Trip_to_${trip.destination.replace(/[^a-zA-Z0-9]/g, '_')}.pdf`,
        image: { type: 'jpeg', quality: 0.98 },
        html2canvas: { scale: 2, useCORS: true },
        jsPDF: { unit: 'mm', format: 'a4', orientation: 'portrait' }
      };

      html2pdf().set(opt).from(tempDiv).save();
    }

    function deleteSavedTrip(id) {
      let trips = getSavedTrips();
      const target = trips.find(t => String(t.id) === String(id));
      const destName = target ? target.destination : 'trip';

      showConfirmModal({
        title: 'Delete Saved Itinerary?',
        message: `Are you sure you want to remove your saved itinerary for "${destName}"?`,
        icon: '🗑️',
        confirmText: 'Yes, Delete',
        onConfirm: () => {
          trips = trips.filter(t => String(t.id) !== String(id));
          persistSavedTrips(trips);
          renderSaved();
          showToast(`Deleted trip for ${destName}.`, 'info');
        }
      });
    }

    function clearTrips() {
      const trips = getSavedTrips();
      if (trips.length === 0) {
        showToast('No saved trips to clear.', 'info');
        return;
      }

      showConfirmModal({
        title: 'Clear All Saved Trips?',
        message: 'Are you sure you want to remove all saved itineraries from your device? This action cannot be undone.',
        icon: '🗑️',
        confirmText: 'Yes, Clear All',
        onConfirm: () => {
          localStorage.removeItem('roamai_saved_trips');
          localStorage.removeItem('saved_trips');
          renderSaved();
          showToast('All saved trips have been cleared.', 'info');
        }
      });
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

    // ========================================================
    // SMART PACKING CHECKLIST SYSTEM
    // ========================================================
    const PACK_CATEGORIES = {
      docs: { name: "Documents & Travel Finance", icon: "📄", color: "text-amberAccent" },
      tech: { name: "Tech, Gadgets & Gear", icon: "🔌", color: "text-cyanAccent" },
      clothing: { name: "Clothing & Footwear", icon: "👕", color: "text-coralPrimary" },
      health: { name: "Toiletries & Health Care", icon: "💊", color: "text-emeraldAccent" },
      dest: { name: "Destination & Itinerary Essentials", icon: "📍", color: "text-purpleAccent" },
      custom: { name: "Custom Personal Items", icon: "✨", color: "text-amberAccent" }
    };

    const DEFAULT_BASE_ITEMS = [
      // Documents & Finance
      { id: 'b_doc_1', cat: 'docs', name: 'Passport & Student ID Card (or ISIC Card)', defaultChecked: false },
      { id: 'b_doc_2', cat: 'docs', name: 'Zero-Forex Travel Card & Emergency Local Cash', defaultChecked: false },
      { id: 'b_doc_3', cat: 'docs', name: 'Travel Insurance Certificate & Visa Copies', defaultChecked: false },
      { id: 'b_doc_4', cat: 'docs', name: 'Offline / Printed Flight & Hostel Booking PDFs', defaultChecked: false },

      // Tech & Gadgets
      { id: 'b_tech_1', cat: 'tech', name: 'Universal Travel Power Adapter (All-in-One)', defaultChecked: false },
      { id: 'b_tech_2', cat: 'tech', name: 'High-Capacity Power Bank (10,000mAh+)', defaultChecked: false },
      { id: 'b_tech_3', cat: 'tech', name: 'Noise-Cancelling Earbuds / Headphones', defaultChecked: false },
      { id: 'b_tech_4', cat: 'tech', name: 'Extra Long USB-C / Lightning Cables', defaultChecked: false },

      // Clothing & Footwear
      { id: 'b_cloth_1', cat: 'clothing', name: 'Comfortable Walking Sneakers (15k+ daily steps)', defaultChecked: false },
      { id: 'b_cloth_2', cat: 'clothing', name: 'Quick-dry Microfiber Hostel Towel', defaultChecked: false },
      { id: 'b_cloth_3', cat: 'clothing', name: 'Lightweight Packable Rain Jacket / Windbreaker', defaultChecked: false },
      { id: 'b_cloth_4', cat: 'clothing', name: 'Breathable Day Outfits + 1 Evening Look', defaultChecked: false },
      { id: 'b_cloth_5', cat: 'clothing', name: 'Flip-Flops / Slides for Hostel Showers', defaultChecked: false },

      // Toiletries & Health
      { id: 'b_hlth_1', cat: 'health', name: 'First Aid Kit, Pain Relievers & Band-Aids', defaultChecked: false },
      { id: 'b_hlth_2', cat: 'health', name: 'Personal Prescription Medications + Motion Pills', defaultChecked: false },
      { id: 'b_hlth_3', cat: 'health', name: 'Travel-size Sunscreen SPF 50+ & Deodorant', defaultChecked: false },
      { id: 'b_hlth_4', cat: 'health', name: 'Sleep Eye Mask & Noise-Blocking Earplugs', defaultChecked: false }
    ];

    const DESTINATION_VIBE_ITEMS = {
      beach: [
        { id: 'v_beach_1', cat: 'dest', name: 'Quick-dry Swimwear & Beach Boardshorts', defaultChecked: false },
        { id: 'v_beach_2', cat: 'dest', name: 'Waterproof Dry Bag / Underwater Phone Pouch', defaultChecked: false },
        { id: 'v_beach_3', cat: 'dest', name: 'Polarized UV Sunglasses & Wide-Brim Sun Hat', defaultChecked: false },
        { id: 'v_beach_4', cat: 'dest', name: 'Reef-Safe Sunscreen SPF 50+ & Aloe Vera Gel', defaultChecked: false },
        { id: 'v_beach_5', cat: 'dest', name: 'Lightweight Sand-Free Microfiber Beach Mat', defaultChecked: false }
      ],
      mountain: [
        { id: 'v_mount_1', cat: 'dest', name: 'Trekking / Trail Grip Shoes with Ankle Support', defaultChecked: false },
        { id: 'v_mount_2', cat: 'dest', name: 'Thermal Base Layers & Breathable Fleece Jacket', defaultChecked: false },
        { id: 'v_mount_3', cat: 'dest', name: 'Heavy-Duty Insect & Mosquito Repellent Spray', defaultChecked: false },
        { id: 'v_mount_4', cat: 'dest', name: 'Reusable Insulated Hydration Flask (1L)', defaultChecked: false },
        { id: 'v_mount_5', cat: 'dest', name: 'Mini LED Headlamp or Pocket Flashlight', defaultChecked: false }
      ],
      culture: [
        { id: 'v_cult_1', cat: 'dest', name: 'Comfortable Slip-On Shoes (for Temples / Shrines)', defaultChecked: false },
        { id: 'v_cult_2', cat: 'dest', name: 'Modest Cover-Up Scarf / Shoulder Wrap', defaultChecked: false },
        { id: 'v_cult_3', cat: 'dest', name: 'Coin Pouch (for Temple Donations & Vending)', defaultChecked: false },
        { id: 'v_cult_4', cat: 'dest', name: 'Local Transit / IC Metro Card & Pass Holder', defaultChecked: false },
        { id: 'v_cult_5', cat: 'dest', name: 'Foldable Rain Umbrella / UV Sun Parasol', defaultChecked: false }
      ],
      city: [
        { id: 'v_city_1', cat: 'dest', name: 'Compact Anti-Theft Daypack (15-20L)', defaultChecked: false },
        { id: 'v_city_2', cat: 'dest', name: 'RFID-Blocking Transit / Metro Card Holder', defaultChecked: false },
        { id: 'v_city_3', cat: 'dest', name: 'Comfortable Breathable Walking Socks (3+ pairs)', defaultChecked: false },
        { id: 'v_city_4', cat: 'dest', name: 'International eSIM / Local SIM Card Ejector Pin', defaultChecked: false },
        { id: 'v_city_5', cat: 'dest', name: 'Foldable Reusable Shopping Tote Bag', defaultChecked: false }
      ],
      winter: [
        { id: 'v_win_1', cat: 'dest', name: 'Heavy Insulated Winter Parka / Down Jacket', defaultChecked: false },
        { id: 'v_win_2', cat: 'dest', name: 'Thermal Woolen Socks, Touchscreen Gloves & Beanie', defaultChecked: false },
        { id: 'v_win_3', cat: 'dest', name: 'Intense Moisturizing Cold Cream & Lip Balm', defaultChecked: false },
        { id: 'v_win_4', cat: 'dest', name: 'Waterproof Snow / Winter Grip Boots', defaultChecked: false },
        { id: 'v_win_5', cat: 'dest', name: 'Self-Heating Hand / Foot Warmer Packs', defaultChecked: false }
      ],
      hostel: [
        { id: 'v_host_1', cat: 'dest', name: 'TSA 3-Dial Combination Padlock (for Lockers)', defaultChecked: false },
        { id: 'v_host_2', cat: 'dest', name: 'Multi-Outlet Compact Power Extension Strip', defaultChecked: false },
        { id: 'v_host_3', cat: 'dest', name: 'Hanging Mesh Shower / Toiletries Caddy', defaultChecked: false },
        { id: 'v_host_4', cat: 'dest', name: 'Collapsible Breathable Laundry Bag', defaultChecked: false },
        { id: 'v_host_5', cat: 'dest', name: 'Quick-Drying Shower Slides / Flip-Flops', defaultChecked: false }
      ]
    };

    let activePackFilter = 'all';
    let selectedPackVibe = 'auto';

    function getStoredCustomItems() {
      try {
        return JSON.parse(localStorage.getItem('roamai_custom_pack_items') || '[]');
      } catch (e) {
        return [];
      }
    }

    function saveCustomItems(items) {
      try {
        localStorage.setItem('roamai_custom_pack_items', JSON.stringify(items));
      } catch (e) {}
    }

    function getStoredCheckedState() {
      try {
        return JSON.parse(localStorage.getItem('roamai_pack_checked_state') || '{}');
      } catch (e) {
        return {};
      }
    }

    function saveCheckedState(state) {
      try {
        localStorage.setItem('roamai_pack_checked_state', JSON.stringify(state));
      } catch (e) {}
    }

    function detectItineraryVibe(customText = null) {
      let destStr = '';
      if (customText) {
        destStr = customText.toLowerCase();
      } else if (currentTrip && currentTrip.trip_summary && currentTrip.trip_summary.destination) {
        destStr = (currentTrip.trip_summary.destination + ' ' + (currentTrip.itinerary || '')).toLowerCase();
      } else {
        destStr = (document.getElementById('plannerDest')?.value || '').toLowerCase();
      }

      if (!destStr || destStr.trim() === '') {
        return null;
      }

      if (destStr.includes('goa') || destStr.includes('bali') || destStr.includes('beach') || destStr.includes('phuket') || destStr.includes('maldives') || destStr.includes('cancun') || destStr.includes('island') || destStr.includes('coastal') || destStr.includes('surf') || destStr.includes('scuba')) {
        return 'beach';
      }
      if (destStr.includes('manali') || destStr.includes('leh') || destStr.includes('ladakh') || destStr.includes('himalaya') || destStr.includes('alps') || destStr.includes('banff') || destStr.includes('trek') || destStr.includes('hiking') || destStr.includes('mountain') || destStr.includes('camp')) {
        return 'mountain';
      }
      if (destStr.includes('sapporo') || destStr.includes('snow') || destStr.includes('kashmir') || destStr.includes('winter') || destStr.includes('iceland') || destStr.includes('ski')) {
        return 'winter';
      }
      if (destStr.includes('kyoto') || destStr.includes('temple') || destStr.includes('shrine') || destStr.includes('museum') || destStr.includes('history') || destStr.includes('heritage') || destStr.includes('culture') || destStr.includes('rome') || destStr.includes('monument')) {
        return 'culture';
      }
      if (destStr.includes('hostel') || destStr.includes('backpack') || destStr.includes('dorm')) {
        return 'hostel';
      }
      return 'city';
    }

    function getAllCurrentPackItems() {
      const base = [...DEFAULT_BASE_ITEMS];
      const vibeKey = getActiveVibeKey();
      const vibeItems = vibeKey ? (DESTINATION_VIBE_ITEMS[vibeKey] || []) : [];
      const customItems = getStoredCustomItems();

      // Dynamic trip-specific landmark & student pass items
      const dynamicTripItems = [];
      let targetTrip = null;
      if (selectedPackVibe && selectedPackVibe.startsWith('saved:')) {
        const tripId = selectedPackVibe.replace('saved:', '');
        const savedTrips = getSavedTrips();
        targetTrip = savedTrips.find(t => String(t.id) === String(tripId));
      } else if (currentTrip && currentTrip.trip_summary && currentTrip.trip_summary.destination) {
        targetTrip = {
          destination: currentTrip.trip_summary.destination,
          days: currentTrip.trip_summary.days
        };
      }

      if (targetTrip && targetTrip.destination && targetTrip.destination.trim() !== '') {
        const destName = targetTrip.destination.split(',')[0].trim();
        dynamicTripItems.push({
          id: `dyn_dest_${targetTrip.id || 'curr'}_1`,
          cat: 'dest',
          name: `${destName} Offline Map & Metro Transit App Bookmarked`,
          defaultChecked: false
        });
        dynamicTripItems.push({
          id: `dyn_dest_${targetTrip.id || 'curr'}_2`,
          cat: 'dest',
          name: `${destName} Student Discounts & Local Currency Cash`,
          defaultChecked: false
        });
      }

      return [...base, ...vibeItems, ...dynamicTripItems, ...customItems];
    }

    function renderPackingVibeDropdown() {
      const select = document.getElementById('packVibeSelector');
      if (!select) return;

      const savedTrips = getSavedTrips();
      const currentVal = selectedPackVibe || 'auto';

      let html = `
        <option value="auto" ${currentVal === 'auto' ? 'selected' : ''}>📍 Auto-detect from Current Planner</option>
      `;

      if (savedTrips && savedTrips.length > 0) {
        html += `<optgroup label="📂 My Saved Itineraries">`;
        savedTrips.forEach(t => {
          const optVal = `saved:${t.id}`;
          const isSelected = currentVal === optVal ? 'selected' : '';
          html += `<option value="${optVal}" ${isSelected}>📂 Saved: ${t.destination} (${t.days} Days)</option>`;
        });
        html += `</optgroup>`;
      }

      html += `
        <optgroup label="✨ Preset Travel Styles & Vibes">
          <option value="beach" ${currentVal === 'beach' ? 'selected' : ''}>🏖️ Beach, Island & Coastal (Goa, Bali, Phuket)</option>
          <option value="mountain" ${currentVal === 'mountain' ? 'selected' : ''}>🏔️ Mountains, Hiking & Trekking (Manali, Alps)</option>
          <option value="culture" ${currentVal === 'culture' ? 'selected' : ''}>🏯 Culture, Temples & Shrines (Kyoto, Rome, Varanasi)</option>
          <option value="city" ${currentVal === 'city' ? 'selected' : ''}>🏙️ City Sightseeing & Tech (Tokyo, London, NYC)</option>
          <option value="winter" ${currentVal === 'winter' ? 'selected' : ''}>❄️ Cold Weather & Snow (Alps, Sapporo, Kashmir)</option>
          <option value="hostel" ${currentVal === 'hostel' ? 'selected' : ''}>🎒 Classic Backpacker & Hostel Dorm</option>
        </optgroup>
      `;

      select.innerHTML = html;
    }

    function getActiveVibeKey() {
      if (!selectedPackVibe || selectedPackVibe === 'auto') {
        return detectItineraryVibe();
      }
      if (selectedPackVibe.startsWith('saved:')) {
        const tripId = selectedPackVibe.replace('saved:', '');
        const savedTrips = getSavedTrips();
        const trip = savedTrips.find(t => String(t.id) === String(tripId));
        if (trip) {
          return detectItineraryVibe(trip.destination + ' ' + (trip.itinerary || '')) || 'city';
        }
        return 'city';
      }
      return selectedPackVibe;
    }

    function onPackVibeChange(vibeVal) {
      selectedPackVibe = vibeVal;
      try { localStorage.setItem('roamai_pack_selected_vibe', vibeVal); } catch (e) {}
      
      const badge = document.getElementById('packVibeBadge');
      if (badge) {
        if (vibeVal === 'auto') {
          const detected = detectItineraryVibe();
          if (detected) {
            badge.innerText = `Auto: ${detected.toUpperCase()}`;
            badge.className = 'text-xs text-emeraldAccent font-semibold px-2.5 py-0.5 rounded-full bg-emeraldAccent/10 border border-emeraldAccent/20';
            showToast(`Checklist adapted to current planner (${detected.toUpperCase()})`, 'info');
          } else {
            badge.innerText = `Auto: Standard Essentials`;
            badge.className = 'text-xs text-gray-400 font-semibold px-2.5 py-0.5 rounded-full bg-white/5 border border-white/10';
          }
        } else if (vibeVal.startsWith('saved:')) {
          const tripId = vibeVal.replace('saved:', '');
          const savedTrips = getSavedTrips();
          const trip = savedTrips.find(t => String(t.id) === String(tripId));
          const tripName = trip ? trip.destination : 'Saved Trip';
          const detected = trip ? (detectItineraryVibe(trip.destination + ' ' + (trip.itinerary || '')) || 'city') : 'city';
          badge.innerText = `Saved: ${tripName}`;
          badge.className = 'text-xs text-cyanAccent font-semibold px-2.5 py-0.5 rounded-full bg-cyanAccent/10 border border-cyanAccent/20';
          showToast(`Checklist adapted for saved itinerary "${tripName}" (${detected.toUpperCase()})!`, 'success');
        } else {
          badge.innerText = `Manual: ${vibeVal.toUpperCase()}`;
          badge.className = 'text-xs text-amberAccent font-semibold px-2.5 py-0.5 rounded-full bg-amberAccent/10 border border-amberAccent/20';
          showToast(`Checklist vibe set to ${vibeVal.toUpperCase()}`, 'info');
        }
      }
      renderPacking();
    }

    function renderPacking() {
      renderPackingVibeDropdown();
      const allItems = getAllCurrentPackItems();
      const checks = getStoredCheckedState();
      
      // Update badge label for auto-detect
      const badge = document.getElementById('packVibeBadge');
      if (badge && (!selectedPackVibe || selectedPackVibe === 'auto')) {
        const detected = detectItineraryVibe();
        if (detected) {
          badge.innerText = `Auto: ${detected.toUpperCase()}`;
          badge.className = 'text-xs text-emeraldAccent font-semibold px-2.5 py-0.5 rounded-full bg-emeraldAccent/10 border border-emeraldAccent/20';
        } else {
          badge.innerText = `Auto: Standard Essentials`;
          badge.className = 'text-xs text-gray-400 font-semibold px-2.5 py-0.5 rounded-full bg-white/5 border border-white/10';
        }
      }

      // Calculate overall progress
      const totalCount = allItems.length;
      let packedCount = 0;

      allItems.forEach(item => {
        const isChecked = checks[item.id] !== undefined ? checks[item.id] : (item.defaultChecked || false);
        if (isChecked) packedCount++;
      });

      const pct = totalCount > 0 ? Math.round((packedCount / totalCount) * 100) : 0;
      document.getElementById('packProgressText').innerText = `${pct}% Packed (${packedCount}/${totalCount} items)`;
      document.getElementById('packProgressBar').style.width = `${pct}%`;

      // Render Category Filter Pills
      renderPackFilterPills(allItems, checks);

      // Group items by category
      const grouped = {};
      Object.keys(PACK_CATEGORIES).forEach(k => { grouped[k] = []; });

      allItems.forEach(item => {
        const c = item.cat || 'custom';
        if (!grouped[c]) grouped[c] = [];
        grouped[c].push(item);
      });

      // Render Category Cards Grid
      const container = document.getElementById('packingListContainer');
      const catsToDisplay = activePackFilter === 'all' 
        ? Object.keys(PACK_CATEGORIES).filter(k => (grouped[k] || []).length > 0)
        : [activePackFilter];

      if (catsToDisplay.length === 0) {
        container.innerHTML = `
          <div class="col-span-full glass-card p-10 rounded-3xl border border-dashed border-white/15 text-center space-y-3 shadow-lg">
            <span class="text-3xl">🎒</span>
            <h4 class="text-base font-bold text-white">No Items in this Category</h4>
            <p class="text-xs text-gray-400">Select another category filter or add custom items above!</p>
          </div>
        `;
        return;
      }

      container.innerHTML = catsToDisplay.map(catKey => {
        const catInfo = PACK_CATEGORIES[catKey];
        const items = grouped[catKey] || [];
        if (items.length === 0) return '';

        const catPacked = items.filter(it => (checks[it.id] !== undefined ? checks[it.id] : (it.defaultChecked || false))).length;
        const catTotal = items.length;
        const catPct = catTotal > 0 ? Math.round((catPacked / catTotal) * 100) : 0;

        return `
          <div class="glass-card p-6 rounded-3xl border border-white/10 space-y-4 shadow-xl flex flex-col justify-between">
            <div class="space-y-3">
              <div class="flex items-center justify-between pb-3 border-b border-white/10">
                <div class="flex items-center gap-2">
                  <span class="text-xl">${catInfo.icon}</span>
                  <h4 class="text-sm font-extrabold text-white">${catInfo.name}</h4>
                </div>
                <span class="text-[11px] font-bold px-2.5 py-0.5 rounded-full ${catPacked === catTotal && catTotal > 0 ? 'bg-emeraldAccent/20 text-emeraldAccent border border-emeraldAccent/30' : 'bg-white/5 text-gray-400 border border-white/10'}">
                  ${catPacked}/${catTotal} (${catPct}%)
                </span>
              </div>

              <div class="space-y-1.5">
                ${items.map(item => {
                  const isChecked = checks[item.id] !== undefined ? checks[item.id] : (item.defaultChecked || false);
                  const isCustom = item.isCustom || String(item.id).startsWith('c_');
                  return `
                    <div class="flex items-center justify-between p-2.5 rounded-xl hover:bg-white/5 cursor-pointer transition select-none group">
                      <label class="flex items-center gap-3 flex-grow cursor-pointer" onclick="togglePack('${item.id}')">
                        <input
                          type="checkbox"
                          ${isChecked ? 'checked' : ''}
                          class="w-4 h-4 rounded accent-coralPrimary bg-gray-900 border-gray-700 cursor-pointer"
                          onclick="event.stopPropagation(); togglePack('${item.id}')"
                        />
                        <span class="text-xs ${isChecked ? 'line-through text-gray-500' : 'text-gray-200 font-medium'}">
                          ${item.name}
                        </span>
                      </label>
                      ${isCustom ? `
                        <button onclick="deleteCustomPackingItem('${item.id}')" class="text-xs text-gray-500 hover:text-red-400 opacity-0 group-hover:opacity-100 transition p-1" title="Delete Item">
                          🗑️
                        </button>
                      ` : ''}
                    </div>
                  `;
                }).join('')}
              </div>
            </div>

            <div class="pt-2 text-[10px] text-gray-500 flex justify-between border-t border-white/5">
              <span>RoamAI Smart Checklist</span>
              <span class="text-emeraldAccent font-semibold">${catPacked === catTotal && catTotal > 0 ? 'All Packed!' : `${catTotal - catPacked} left`}</span>
            </div>
          </div>
        `;
      }).join('');
    }

    function renderPackFilterPills(allItems, checks) {
      const pillContainer = document.getElementById('packCategoryFilterPills');
      if (!pillContainer) return;

      const pills = [
        { key: 'all', label: 'All Items', icon: '🎒', count: allItems.length },
        ...Object.keys(PACK_CATEGORIES).map(k => {
          const count = allItems.filter(i => (i.cat || 'custom') === k).length;
          return { key: k, label: PACK_CATEGORIES[k].name.split(' ')[0], icon: PACK_CATEGORIES[k].icon, count };
        }).filter(p => p.count > 0)
      ];

      pillContainer.innerHTML = pills.map(p => `
        <button
          onclick="filterPackingCategory('${p.key}')"
          class="text-xs px-3.5 py-1.5 rounded-full border transition flex items-center gap-1.5 ${activePackFilter === p.key ? 'bg-gradient-to-r from-coralPrimary to-amberAccent text-white font-bold border-transparent shadow-md' : 'bg-white/5 border-white/10 text-gray-400 hover:text-white hover:border-white/20'}"
        >
          <span>${p.icon}</span>
          <span>${p.label}</span>
          <span class="text-[10px] opacity-75">(${p.count})</span>
        </button>
      `).join('');
    }

    function filterPackingCategory(catKey) {
      activePackFilter = catKey;
      renderPacking();
    }

    function togglePack(id) {
      const checks = getStoredCheckedState();
      const allItems = getAllCurrentPackItems();
      const it = allItems.find(i => i.id === id);
      
      const current = checks[id] !== undefined ? checks[id] : (it ? it.defaultChecked : false);
      checks[id] = !current;
      saveCheckedState(checks);
      renderPacking();
    }

    function addCustomPackingItem() {
      const input = document.getElementById('customPackInput');
      const catSelect = document.getElementById('customPackCategory');
      const val = input.value.trim();
      if (!val) return;

      const cat = catSelect.value || 'custom';
      const customItems = getStoredCustomItems();

      const newItem = {
        id: 'c_' + Date.now(),
        cat: cat,
        name: val,
        isCustom: true,
        defaultChecked: false
      };

      customItems.push(newItem);
      saveCustomItems(customItems);

      input.value = '';
      renderPacking();
      showToast(`Added "${val}" to packing checklist!`, 'success');
    }

    function deleteCustomPackingItem(id) {
      let customItems = getStoredCustomItems();
      const target = customItems.find(i => i.id === id);
      const itemName = target ? target.name : 'Item';
      customItems = customItems.filter(i => i.id !== id);
      saveCustomItems(customItems);

      const checks = getStoredCheckedState();
      delete checks[id];
      saveCheckedState(checks);

      renderPacking();
      showToast(`Removed "${itemName}" from checklist.`, 'info');
    }

    function checkAllPacking(checkBool) {
      const allItems = getAllCurrentPackItems();
      const checks = getStoredCheckedState();
      allItems.forEach(i => { checks[i.id] = checkBool; });
      saveCheckedState(checks);
      renderPacking();
      showToast(checkBool ? 'All items marked as packed!' : 'All items unchecked.', 'info');
    }

    function resetPackingDefaults() {
      showConfirmModal({
        title: 'Reset Packing Checklist?',
        message: 'Are you sure you want to reset all checked items and custom entries back to defaults?',
        icon: '🔄',
        confirmText: 'Reset to Defaults',
        onConfirm: () => {
          localStorage.removeItem('roamai_pack_checked_state');
          localStorage.removeItem('roamai_custom_pack_items');
          renderPacking();
          showToast('Packing checklist reset to defaults.', 'info');
        }
      });
    }

    // --- Dynamic Moving Interactive Canvas Background ---
    // --- Authentic Wanderlust Travel Sky & Radar Flight Background ---
    function initBackgroundCanvas() {
      const canvas = document.getElementById('bgParticleCanvas');
      if (!canvas) return;
      const ctx = canvas.getContext('2d');
      if (!ctx) return;

      let width = (canvas.width = window.innerWidth);
      let height = (canvas.height = window.innerHeight);

      window.addEventListener('resize', () => {
        width = canvas.width = window.innerWidth;
        height = canvas.height = window.innerHeight;
      });

      // 1. Cruising Airplanes with Contrails
      const planeCount = 8;
      const planes = [];
      for (let i = 0; i < planeCount; i++) {
        planes.push({
          x: Math.random() * width,
          y: Math.random() * height,
          speed: Math.random() * 0.8 + 0.6,
          angle: (Math.random() * Math.PI * 0.6) - 0.3,
          size: Math.random() * 4 + 12,
          history: [],
          color: i % 2 === 0 ? '#FF5E36' : '#06B6D4'
        });
      }

      // 2. Floating Hot Air Balloons
      const balloons = [
        { x: width * 0.12, y: height * 0.40, vy: -0.25, vx: 0.12, radius: 13, hue: '#FFA000', phase: 0 },
        { x: width * 0.85, y: height * 0.70, vy: -0.20, vx: -0.08, radius: 15, hue: '#FF5E36', phase: 1.5 },
        { x: width * 0.50, y: height * 0.82, vy: -0.28, vx: 0.10, radius: 12, hue: '#8B5CF6', phase: 3 },
        { x: width * 0.28, y: height * 0.90, vy: -0.22, vx: -0.12, radius: 14, hue: '#06B6D4', phase: 4.5 }
      ];

      // 3. Shimmering Compass Stars & Firefly Embers
      const starCount = 55;
      const stars = [];
      for (let i = 0; i < starCount; i++) {
        stars.push({
          x: Math.random() * width,
          y: Math.random() * height,
          vx: (Math.random() - 0.5) * 0.3,
          vy: (Math.random() - 0.5) * 0.3,
          size: Math.random() * 3 + 1.5,
          isCompass: Math.random() > 0.6,
          color: Math.random() > 0.5 ? 'rgba(255, 160, 0, ' : 'rgba(6, 182, 212, ',
          alpha: Math.random() * 0.6 + 0.3,
          pulse: Math.random() * 0.03 + 0.015
        });
      }

      // 4. Destination Waypoint Radars
      const waypoints = [
        { x: width * 0.20, y: height * 0.25, name: "Tokyo", pulseRadius: 0 },
        { x: width * 0.78, y: height * 0.32, name: "Rome", pulseRadius: 15 },
        { x: width * 0.45, y: height * 0.65, name: "Goa", pulseRadius: 30 }
      ];

      let mouse = { x: null, y: null, ripple: 0 };
      window.addEventListener('mousemove', (e) => {
        mouse.x = e.clientX;
        mouse.y = e.clientY;
        mouse.ripple = (mouse.ripple + 1) % 50;
      });
      window.addEventListener('mouseleave', () => {
        mouse.x = null;
        mouse.y = null;
      });

      function drawPlane(p, isLight) {
        ctx.save();
        ctx.translate(p.x, p.y);
        ctx.rotate(p.angle);

        const planeColor = isLight ? (p.color === '#06B6D4' ? '#0284C7' : '#EA580C') : p.color;
        ctx.fillStyle = planeColor;
        ctx.shadowColor = isLight ? 'rgba(2, 132, 199, 0.4)' : planeColor;
        ctx.shadowBlur = isLight ? 6 : 10;
        ctx.beginPath();
        // Nose
        ctx.moveTo(p.size * 1.1, 0);
        // Right wing
        ctx.lineTo(-p.size * 0.4, p.size * 0.9);
        // Right body indent
        ctx.lineTo(-p.size * 0.2, p.size * 0.2);
        // Tail wing right
        ctx.lineTo(-p.size * 0.85, p.size * 0.5);
        // Tail tip
        ctx.lineTo(-p.size * 0.7, 0);
        // Tail wing left
        ctx.lineTo(-p.size * 0.85, -p.size * 0.5);
        // Left body indent
        ctx.lineTo(-p.size * 0.2, -p.size * 0.2);
        // Left wing
        ctx.lineTo(-p.size * 0.4, -p.size * 0.9);
        ctx.closePath();
        ctx.fill();

        ctx.restore();
      }

      function drawBalloon(b, isLight) {
        ctx.save();
        ctx.translate(b.x, b.y);

        // Balloon envelope
        ctx.fillStyle = b.hue;
        ctx.shadowColor = isLight ? 'rgba(0,0,0,0.2)' : b.hue;
        ctx.shadowBlur = 10;
        ctx.beginPath();
        ctx.arc(0, 0, b.radius, 0, Math.PI, true);
        ctx.quadraticCurveTo(-b.radius * 0.9, b.radius * 1.1, 0, b.radius * 1.4);
        ctx.quadraticCurveTo(b.radius * 0.9, b.radius * 1.1, b.radius, 0);
        ctx.fill();

        // Basket
        ctx.fillStyle = isLight ? '#334155' : 'rgba(255, 255, 255, 0.8)';
        ctx.fillRect(-b.radius * 0.25, b.radius * 1.65, b.radius * 0.5, b.radius * 0.35);

        // Strings
        ctx.strokeStyle = isLight ? 'rgba(15, 23, 42, 0.55)' : 'rgba(255, 255, 255, 0.4)';
        ctx.lineWidth = 0.9;
        ctx.beginPath();
        ctx.moveTo(-b.radius * 0.3, b.radius * 1.4);
        ctx.lineTo(-b.radius * 0.2, b.radius * 1.65);
        ctx.moveTo(b.radius * 0.3, b.radius * 1.4);
        ctx.lineTo(b.radius * 0.2, b.radius * 1.65);
        ctx.stroke();

        ctx.restore();
      }

      function drawCompassStar(s, alpha, isLight) {
        ctx.save();
        ctx.translate(s.x, s.y);
        const starColor = isLight 
          ? (s.color.includes('255, 160') ? 'rgba(217, 119, 6, ' : 'rgba(2, 132, 199, ')
          : s.color;
        ctx.fillStyle = starColor + alpha + ')';
        ctx.shadowColor = isLight ? 'rgba(217, 119, 6, 0.7)' : starColor + '0.8)';
        ctx.shadowBlur = 8;

        ctx.beginPath();
        const rOuter = s.size * 2.3;
        const rInner = s.size * 0.55;
        for (let i = 0; i < 4; i++) {
          const a = (i * Math.PI) / 2;
          ctx.lineTo(Math.cos(a) * rOuter, Math.sin(a) * rOuter);
          const aMid = a + Math.PI / 4;
          ctx.lineTo(Math.cos(aMid) * rInner, Math.sin(aMid) * rInner);
        }
        ctx.closePath();
        ctx.fill();
        ctx.restore();
      }

      function animate() {
        ctx.clearRect(0, 0, width, height);
        const isLight = document.documentElement.classList.contains('light-theme') || document.body.classList.contains('light-theme');

        // 1. Draw Global Great-Circle Flight Arcs
        ctx.save();
        ctx.setLineDash([8, 14]);
        ctx.lineWidth = isLight ? 2 : 1;
        ctx.strokeStyle = isLight ? 'rgba(234, 88, 12, 0.45)' : 'rgba(255, 160, 0, 0.15)';
        ctx.beginPath();
        ctx.moveTo(0, height * 0.3);
        ctx.quadraticCurveTo(width * 0.5, height * 0.1, width, height * 0.45);
        ctx.stroke();

        ctx.strokeStyle = isLight ? 'rgba(2, 132, 199, 0.45)' : 'rgba(6, 182, 212, 0.12)';
        ctx.beginPath();
        ctx.moveTo(0, height * 0.7);
        ctx.quadraticCurveTo(width * 0.4, height * 0.85, width, height * 0.6);
        ctx.stroke();
        ctx.restore();

        // 2. Draw Destination Waypoint Pulses
        waypoints.forEach(wp => {
          wp.pulseRadius = (wp.pulseRadius + 0.35) % 50;
          const pAlpha = (1 - wp.pulseRadius / 50) * (isLight ? 0.7 : 0.4);
          ctx.beginPath();
          ctx.arc(wp.x, wp.y, wp.pulseRadius, 0, Math.PI * 2);
          ctx.strokeStyle = isLight ? `rgba(2, 132, 199, ${pAlpha})` : `rgba(6, 182, 212, ${pAlpha})`;
          ctx.lineWidth = isLight ? 1.8 : 1;
          ctx.stroke();

          ctx.beginPath();
          ctx.arc(wp.x, wp.y, 3.5, 0, Math.PI * 2);
          ctx.fillStyle = isLight ? '#0284C7' : '#06B6D4';
          ctx.fill();
        });

        // 3. Update & Draw Stars / Compass Points
        stars.forEach(s => {
          s.x += s.vx;
          s.y += s.vy;
          if (s.x < 0) s.x = width;
          if (s.x > width) s.x = 0;
          if (s.y < 0) s.y = height;
          if (s.y > height) s.y = 0;

          s.alpha += Math.sin(Date.now() * s.pulse) * 0.007;
          const curAlpha = Math.max(0.3, Math.min(0.95, s.alpha));

          if (s.isCompass) {
            drawCompassStar(s, curAlpha, isLight);
          } else {
            const dotColor = isLight 
              ? (s.color.includes('255, 160') ? 'rgba(217, 119, 6, ' : 'rgba(2, 132, 199, ')
              : s.color;
            ctx.beginPath();
            ctx.arc(s.x, s.y, s.size, 0, Math.PI * 2);
            ctx.fillStyle = dotColor + curAlpha + ')';
            ctx.fill();
          }
        });

        // 4. Update & Draw Hot Air Balloons
        balloons.forEach(b => {
          b.phase += 0.02;
          b.y += b.vy;
          b.x += b.vx + Math.sin(b.phase) * 0.15;
          if (b.y < -40) {
            b.y = height + 40;
            b.x = Math.random() * width;
          }
          drawBalloon(b, isLight);
        });

        // 5. Update & Draw Cruising Planes with Contrails
        planes.forEach(p => {
          p.x += Math.cos(p.angle) * p.speed;
          p.y += Math.sin(p.angle) * p.speed;

          // Record contrail point
          p.history.push({ x: p.x, y: p.y });
          if (p.history.length > 40) p.history.shift();

          // Draw jet contrail
          if (p.history.length > 2) {
            ctx.save();
            ctx.setLineDash([4, 6]);
            ctx.lineWidth = isLight ? 2 : 1.2;
            for (let i = 0; i < p.history.length - 1; i++) {
              const trailAlpha = (i / p.history.length) * (isLight ? 0.7 : 0.4);
              ctx.strokeStyle = isLight 
                ? `rgba(2, 132, 199, ${trailAlpha})`
                : `rgba(255, 255, 255, ${trailAlpha})`;
              ctx.beginPath();
              ctx.moveTo(p.history[i].x, p.history[i].y);
              ctx.lineTo(p.history[i + 1].x, p.history[i + 1].y);
              ctx.stroke();
            }
            ctx.restore();
          }

          // Screen wrapping
          if (p.x > width + 60) {
            p.x = -60;
            p.y = Math.random() * height;
            p.history = [];
          }
          if (p.y > height + 60) {
            p.y = -60;
            p.history = [];
          }
          if (p.y < -60) {
            p.y = height + 60;
            p.history = [];
          }

          drawPlane(p, isLight);
        });

        // 6. Interactive Mouse Compass Radar Ring
        if (mouse.x !== null && mouse.y !== null) {
          ctx.save();
          ctx.beginPath();
          ctx.arc(mouse.x, mouse.y, 45, 0, Math.PI * 2);
          ctx.strokeStyle = isLight ? 'rgba(225, 29, 72, 0.45)' : 'rgba(255, 94, 54, 0.25)';
          ctx.lineWidth = 1.2;
          ctx.setLineDash([4, 4]);
          ctx.stroke();

          ctx.beginPath();
          ctx.arc(mouse.x, mouse.y, 20, 0, Math.PI * 2);
          ctx.strokeStyle = 'rgba(255, 160, 0, 0.35)';
          ctx.lineWidth = 1;
          ctx.stroke();
          ctx.restore();
        }

        requestAnimationFrame(animate);
      }

      animate();
    }

    document.addEventListener('DOMContentLoaded', () => {
      // 1. Immediately update saved trips count badge in navbar
      updateSavedCount();

      // 2. Initialize Theme Mood (Detects user device preference first)
      initThemeMood();

      // 3. Initialize animated moving travel sky canvas background
      initBackgroundCanvas();

      // 4. Restore saved region (prevent resetting to INR on reload)
      const savedRegion = localStorage.getItem('roamai_selected_region') || 'INR';
      onRegionChange(savedRegion, false);

      // 5. Restore saved active page (prevent automatically resetting to home on reload)
      const hashPage = window.location.hash.replace('#', '');
      const savedPage = hashPage || localStorage.getItem('roamai_active_page') || 'home';
      switchPage(savedPage, false);

      // 6. Restore Trip Architect Form Draft & Active Itinerary (prevents info loss on reload)
      initPlannerDraft();

      // 7. Render packing checklist
      renderPacking();

      // 8. Render saved itineraries from persistent vault
      renderSaved();
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