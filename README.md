# 🧭 RoamAI — Next-Gen AI Travel Architect & Student Budget Optimizer

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688.svg?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Groq LPU](https://img.shields.io/badge/AI-Groq%20LPU%20Ultra--Fast-F55036.svg)](https://groq.com)
[![OOP Architecture](https://img.shields.io/badge/Architecture-Modular%20OOP-purple.svg)](core/)
[![License: Custom](https://img.shields.io/badge/License-Source--Available%20(Anti--Rebrand)-red.svg)](LICENSE)

**RoamAI** is an ultra-fast, intelligent travel architect engineered specifically for students, backpackers, and curious explorers. Built with high-speed **Groq LPUs** and hardened with a clean **Object-Oriented Programming (OOP)** architecture, RoamAI delivers day-by-day itineraries, interactive Leaflet GPS pins, adaptive packing checklists, multi-currency budgeting, and offline PDF exports in seconds.

---

## 🎯 Why RoamAI?

Planning student and budget trips often presents unique challenges: strict financial limits, scattered recommendations, packing uncertainty, and disconnected transit routes. **RoamAI solves this end-to-end**:

- **Zero Overspending**: Realistic student budgets with smart regional hacks and multi-currency conversion across 9 global regions.
- **No Planning Fatigue**: Instant day-by-day schedules with live GPS coordinates, authentic regional food spots, and hidden gems.
- **Instant Student/Traveler Mode Toggle**: Switch seamlessly between Student Explorer mode (hostels, concession hacks) and Curated Traveler mode (boutique stays, gastronomy) in real time without regenerating.
- **Smart Gear Planning**: Dynamic checklists automatically aligned with your trip style (beach, mountain, cultural temples, or hostel dorms).
- **Travel Anywhere Offline**: Save your trips to an offline browser vault or download print-ready formatted PDFs.

---

## ✨ Core Features & Highlights

### ⚡ 1. Sub-Second AI Trip Architect
- **Groq LPU Acceleration**: Ultra-fast responses leveraging `llama-3.3-70b-versatile`, `llama-3.1-8b-instant`, and `gemma2-9b-it` with automatic failover cascades.
- **Budget Tiers**: Choose between *Student (Low)*, *Backpacker Moderate*, or *Comfort Luxury* with custom budget ceilings.
- **Custom Vibes & Tags**: Filter by *Street Food*, *Anime & Pop Culture*, *Temple Culture*, *Trekking*, *Nightlife*, and more.
- **Draft Auto-Save & Reset**: Form inputs and generated plans persist across reloads with a 1-click `🔄 Reset All` button.

### 🎭 2. Theatrical 2.4s Curtain-Raiser & Expedition HUD
- **Drama Curtain-Raiser Preloader**: Theatrical 2.4-second welcome transition with parting left and right stage curtain wings.
- **Floating Expedition Dock (`#expeditionHud`)**: Live telemetry bar showing current time, active currency, student mode status, and interactive `"Ready to Roam ✈️"` coordinate status.

### 📍 3. Interactive GPS Mapping & Collision Prevention
- **Dynamic Leaflet & OpenStreetMap**: Automatic geocoding of landmarks, transit stations, and hostels.
- **Landmark Coordinate Placer**: Mathematical spiral dispersion algorithm prevents overlapping map pins.
- **Pre-Cached Knowledge Base**: Instant offline coordinates for 127+ curated attractions across India and global destinations.

### 🎒 4. Vibe-Adaptive Smart Packing Checklist
- **Dynamic Style Alignment**: Auto-configures gear tailored to your destination:
  - 🏖️ **Beach & Coastal**: Quick-dry swimwear, reef-safe sunscreen, waterproof pouches
  - 🏔️ **Mountains & Trekking**: Trail grip footwear, thermal layers, LED headlamps
  - 🏯 **Culture & Shrines**: Modest wraps, slip-on shoes, coin pouches
  - 🏙️ **City Sightseeing**: Anti-theft daypacks, RFID transit sleeves, walking socks
  - ❄️ **Winter & Snow**: Insulated parkas, touchscreen gloves, thermal warmers
  - 🎒 **Hostel Backpacker**: TSA locker padlocks, universal power adapters, mesh shower caddies
- **Interactive Checklists**: Start clean, add custom items, and track completion percentages in real time.

### 💱 5. Multi-Currency Budget Optimizer
- **9 Global Currencies**: Real-time conversion across `₹ INR`, `$ USD`, `€ EUR`, `£ GBP`, `¥ JPY`, `A$ AUD`, `C$ CAD`, `AED`, and `฿ THB`.
- **Granular Category Breakdown**: Sliders for Transit, Hostels, Street Food, Activities, and Emergency Buffers.
- **Student Regional Hacks**: In-app tips for student rail concessions (IRCTC, Eurail, Amtrak, JR Pass), free museum days, and affordable family-run kitchens.

### 📂 6. Offline Vault & High-Definition PDF Downloader
- **Persistent Offline Vault**: Save itineraries directly to localStorage for offline reference on trains or flights.
- **Formatted PDF Export**: Clean, print-ready document downloads preserving emojis, schedules, budgets, and formatted typography.

### 🌓 7. Zero-Flicker Pre-Paint UI & Modern Golden Stars
- **Polished Typography**: Inline markdown engine converts all bold/italic markers into clean typography with zero raw asterisks leaking into the interface.
- **Sleek Golden Star Vectors**: Crisp SVG star ratings and review badges replacing cartoon system emojis.
- **Day & Night Themes**: Ultra-smooth dark theme and warm parchment light theme with high-contrast text.

---

## 🏛️ Architecture & OOP Design

The codebase is built on **Object-Oriented Programming (OOP)** principles, ensuring encapsulation, data hiding, type safety, and defensive security:

```
AI-Travel-Planner/
├── api/
│   ├── __init__.py
│   └── index.py               # Vercel serverless entrypoint
├── core/
│   ├── __init__.py
│   ├── config.py              # Settings Singleton with read-only @properties & masked credentials
│   └── security.py            # InputSanitizer, memory-safe RateLimiter & SecurityHeadersMiddleware
├── services/
│   ├── __init__.py
│   ├── itinerary_service.py   # BasePlannerService ABC, TravelPlannerService & LandmarkCoordinatePlacer
│   └── knowledge_base.py      # GeoLocationService (127+ cached landmarks, Nominatim & fallback engine)
├── ui/
│   ├── __init__.py
│   ├── layout.py              # 100% Python-served semantic HTML structure & SVG vector assets
│   ├── styles.py              # Responsive CSS tokens, curtain-raiser animations & theme rules
│   └── scripts.py             # Frontend client logic, inline markdown engine & Leaflet controllers
├── .env                       # Environment credentials (gitignored)
├── app.py                     # RoamAIApplication ASGI factory & route controllers
├── requirements.txt           # Minimal dependencies
└── README.md
```

### Key OOP Patterns:
- **`Settings` Singleton**: Thread-safe configuration manager with encapsulated properties and `.env` parsing.
- **`InputSanitizer`**: Class with compiled regex patterns stripping dangerous `<script>`/`<style>` blocks and XSS payloads.
- **`RateLimiter`**: Sliding window rate limiter featuring **active stale-IP eviction** to protect against memory exhaustion (DoS) attacks.
- **`GeoLocationService`**: Encapsulates coordinate resolution, in-memory caches, and offline fallback trip blueprints.
- **`BasePlannerService` (ABC)**: Abstract base class defining the planner interface implemented by `TravelPlannerService`.
- **`RoamAIApplication`**: Application factory encapsulating FastAPI lifecycle, middleware, and defensive exception handling that prevents internal server traceback leaks.

---

## 🛠️ Tech Stack

- **Backend**: Python 3.10+, FastAPI, Uvicorn ASGI, Pydantic v2
- **AI Engine**: Groq Cloud API (Llama 3.3 70B, Llama 3.1 8B, Gemma 2 9B)
- **Geocoding & Maps**: Geopy (OSM Nominatim API), Leaflet.js, OpenStreetMap
- **Frontend**: Single-Page Application (SPA), Tailwind CSS, Marked.js, html2pdf.js
- **Deployment**: Local Uvicorn daemon / Vercel Serverless (`api/index.py`)

---

## 🚀 Quickstart & Installation

### 1. Clone the Repository
```bash
git clone https://github.com/eleshkapri/AI-Travel-Planner.git
cd AI-Travel-Planner
```

### 2. Set Up Virtual Environment
```bash
python -m venv venv
```
- **Windows**: `.\venv\Scripts\activate`
- **macOS / Linux**: `source venv/bin/activate`

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables
Create a `.env` file in the root directory:
```env
GROQ_API_KEY=your_groq_api_key_here
PORT=8000
HOST=0.0.0.0
```
> *(Get a free API key at [Groq Console](https://console.groq.com/keys))*

### 5. Launch the Application
```bash
uvicorn app:app --host 0.0.0.0 --port 8000 --reload
```
Open **`http://localhost:8000`** in your browser.

---

## 📡 REST API Reference

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/` | Serves the single-page application with security and no-cache headers |
| `GET` | `/api/health` | Health status, version, masked Groq key status, and cached destinations count |
| `GET` | `/api/geocode?q={destination}` | Fast cache-first geocoding lookup |
| `POST` | `/api/generate` | Generates a complete AI travel itinerary with rate limiting and GPS markers |

---

## 📄 License & Intellectual Property

Copyright (c) 2026 **Elesh Kapri**. All rights reserved.

This project is licensed under the **RoamAI Source-Available & Anti-Rebranding License**:
- ✅ **Permitted**: Viewing source code, local self-hosting, academic study, research, and personal non-commercial trip planning.
- ❌ **Strictly Prohibited**: Cloning or forking to rebrand, rename, remove original author credits, resell, redistribute, or release as a separate product/service under another name without prior express written permission from Elesh Kapri.

See the full [LICENSE](LICENSE) file for complete legal terms.

---

<div align="center">
  <sub>Built with ❤️ for student travelers & budget adventurers worldwide by Elesh Kapri.</sub>
</div>
