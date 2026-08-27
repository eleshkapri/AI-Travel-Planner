# 🧭 RoamAI — Next-Gen AI Travel Architect & Student Budget Optimizer

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688.svg?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Groq LPU](https://img.shields.io/badge/AI-Groq%20LPU%20Ultra--Fast-F55036.svg)](https://groq.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**RoamAI** is an ultra-fast, intelligent travel architect engineered specifically for students, backpackers, and budget-conscious explorers. Built with high-speed **Groq LPUs**, RoamAI delivers complete day-by-day itineraries, interactive GPS maps, adaptive packing checklists, regional currency budgeting, and offline PDF exports in seconds.

---

## 🎯 Why RoamAI?

Planning student trips often comes with unique challenges: strict financial limits, scattered recommendations, packing uncertainty, and disconnected transit routes. **RoamAI solves this end-to-end**:

- **Zero Overspending**: Realistic student budgets with smart regional hacks and multi-currency conversion.
- **No Planning Fatigue**: Instant hour-by-hour schedules with real coordinates and landmark descriptions.
- **Smart Gear Planning**: Checklist automatically aligns with your trip style (beach, mountain, temples, or hostel dorms).
- **Travel Anywhere Offline**: Save your trips to an offline browser vault or download formatted print-ready PDFs.

---

## ✨ Core Features & Highlights

### ⚡ 1. Sub-Second AI Trip Architect
- **Lightning-Fast Generation**: Powered by Groq LPUs for rapid, structured itinerary generation.
- **Budget Tiers**: Choose between *Student (Low)*, *Backpacker Moderate*, or *Comfort Luxury* with custom budget caps.
- **Custom Vibes & Tags**: Filter by *Street Food*, *Anime & Pop Culture*, *Temple Culture*, *Trekking*, *Nightlife*, and more.
- **Draft Auto-Save & Reset**: Form inputs and generated plans persist across tab reloads, with a 1-click `🔄 Reset All` button.

### 📍 2. Interactive GPS Mapping
- **Dynamic Leaflet & OpenStreetMap**: Automatic geocoding of landmarks, transit stations, and backpacker hostels.
- **Awaiting Destination State**: Clean guidance template that transitions into live GPS markers upon generation.
- **Flexible View Modes**: Switch between Split Screen, Itinerary Only, and Fullscreen Map.

### 🎒 3. Vibe-Adaptive Smart Packing Checklist
- **Dynamic Style Alignment**: Auto-configures gear tailored to your destination:
  - 🏖️ **Beach & Coastal**: Quick-dry swimwear, reef-safe sunscreen, waterproof pouches
  - 🏔️ **Mountains & Trekking**: Trail grip footwear, thermal layers, LED headlamps
  - 🏯 **Culture & Shrines**: Modest wraps, slip-on shoes, coin pouches
  - 🏙️ **City Sightseeing**: Anti-theft daypacks, RFID transit sleeves, walking socks
  - ❄️ **Winter & Snow**: Insulated parkas, touchscreen gloves, thermal warmers
  - 🎒 **Hostel Backpacker**: TSA locker padlocks, power strips, mesh shower caddies
- **Clean 0% Unchecked Defaults**: Starts fresh and tracks progress in real time with custom item support.

### 💱 4. Multi-Currency Budget Optimizer
- **9 Global Currencies**: Real-time conversion across `₹ INR`, `$ USD`, `€ EUR`, `£ GBP`, `¥ JPY`, `A$ AUD`, `C$ CAD`, `AED`, and `฿ THB`.
- **Granular Category Breakdown**: Interactive sliders for Transit, Hostels, Street Food, Activities, and Emergency Buffers.
- **Student Regional Hacks**: In-app tips for student rail passes (IRCTC, Eurail, Amtrak, JR Pass), free museum days, and affordable food stalls.

### 📂 5. Offline Vault & High-Definition PDF Downloader
- **Persistent Offline Vault**: Save itineraries directly to your device for offline reference during transit.
- **Formatted PDF Export**: Clean, print-ready document downloads preserving emojis, schedules, and budgets.

### 🔥 6. 16 Curated Trending Student Destinations
- **Classified Scope Filters**: Toggle between **`🌍 All (16)`**, **`🇮🇳 National (8)`**, and **`✈️ International (8)`** hotspots:
  - **🇮🇳 National**: *Goa, Manali & Kasol, Jaipur & Udaipur, Rishikesh, Varanasi, Munnar & Kochi, Leh-Ladakh, Shillong & Meghalaya*.
  - **✈️ International**: *Tokyo, Bali, Bangkok & Phuket, Rome, Amsterdam, Kyoto, Paris, Dubai*.
- **Live Localized Costs**: Estimated daily costs automatically recalculate in your active currency.

### 🌓 7. Zero-Flicker Pre-Paint UI & Glassmorphism
- **Seamless Page Router**: Pre-paint theme & page detection eliminates layout shifts or tab flashes on reload.
- **Frosted Glass Navbar**: Translucent backdrop with directional auto-hide on scroll-down and spring reveal on scroll-up.

---

## 🛠️ Tech Stack

- **Backend**: FastAPI (Python 3.10+), Uvicorn ASGI, Pydantic v2
- **AI Engine**: Groq Cloud API (Llama 3.3 70B / Fast LPUs)
- **Geocoding & Maps**: Geopy (Nominatim API), Leaflet.js, OpenStreetMap
- **Frontend**: Single-Page Application (SPA), Tailwind CSS, Marked.js, html2pdf.js

---

## 🚀 Quickstart & Installation

### 1. Clone & Setup
```bash
git clone https://github.com/eleshkapri/AI-Travel-Planner.git
cd AI-Travel-Planner
python -m venv venv
```

### 2. Activate Virtual Environment
- **Windows**: `.\venv\Scripts\activate`
- **macOS / Linux**: `source venv/bin/activate`

### 3. Install Dependencies & Set Key
```bash
pip install -r requirements.txt
```
Set your free API key from [Groq Console](https://console.groq.com/keys):
- **Windows**: `$env:GROQ_API_KEY="your_api_key_here"`
- **macOS / Linux**: `export GROQ_API_KEY="your_api_key_here"`

### 4. Run Application
```bash
uvicorn app:app --host 0.0.0.0 --port 8000 --reload
```
Navigate to **`http://localhost:8000`** in your browser.

---

## 📄 License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.

---

<div align="center">
  <sub>Built with ❤️ for student travelers & budget adventurers worldwide.</sub>
</div>
