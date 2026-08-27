# 🧭 RoamAI — Next-Gen AI Travel Architect & Student Budget Optimizer

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688.svg?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Groq LPU](https://img.shields.io/badge/AI-Groq%20LPU%20Ultra--Fast-F55036.svg)](https://groq.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> **RoamAI** is an ultra-fast, intelligent travel architect engineered specifically for students, backpackers, and budget-conscious explorers. Powered by high-speed **Groq LPUs**, RoamAI generates comprehensive, day-by-day hour-by-hour itineraries with live GPS maps, tailored packing checklists, multi-currency budget breakdowns, and offline PDF exports in sub-seconds.

---

## ✨ Key Features & Capabilities

### ⚡ 1. Sub-Second AI Trip Architect
- **Lightning Fast**: Powered by Groq LPUs (Llama 3.3 70B / DeepSeek / GPT OSS) delivering structured plans in under 1.5 seconds.
- **Student-Tailored Constraints**: Select between *Student (Low)*, *Backpacker Moderate*, or *Comfort Luxury* tiers with custom budget caps.
- **Personalized Vibes**: Customize with tags (e.g., *Street Food*, *Anime & Pop Culture*, *Temple Culture*, *Trekking*, *Nightlife*).
- **Auto-Save Drafts & Reset All**: Inputs and generated blueprints persist across browser reloads, with a one-click `🔄 Reset All` option.

### 📍 2. Interactive Live GPS Mapping
- **OpenStreetMap & Leaflet.js**: Automatic geocoding of destination coordinates, student hostels, landmarks, and transit hubs.
- **Awaiting Destination State**: Clean interactive template placeholder before trip generation seamlessly morphing into interactive GPS pinpoints.
- **Split & Fullscreen View Modes**: Switch effortlessly between Side-by-Side, Itinerary Only, and Fullscreen Map views.

### 🎒 3. Smart Vibe-Adaptive Packing Checklist
- **Dynamic Vibe Adaptation**: Checklist automatically configures gear based on destination style:
  - 🏖️ *Beach, Island & Coastal* (Swimwear, reef-safe sunscreen, waterproof pouches)
  - 🏔️ *Mountains & Trekking* (Trail grip shoes, thermal base layers, headlamps)
  - 🏯 *Culture & Shrines* (Slip-on footwear, modest wraps, IC metro passes)
  - 🏙️ *City Sightseeing* (Anti-theft daypacks, RFID sleeves, walking socks)
  - ❄️ *Cold Weather & Snow* (Heavy parkas, touch-gloves, self-heating packs)
  - 🎒 *Classic Backpacker Dorm* (TSA padlocks, power strips, mesh caddies)
- **Fresh 0% Unchecked Defaults**: Starts clean and tracks packing progress in real time with custom item addition and local persistence.

### 💱 4. Multi-Currency Global Budget Calculator
- **9 Auto-Converting World Currencies**: Full support for `₹ INR`, `$ USD`, `€ EUR`, `£ GBP`, `¥ JPY`, `A$ AUD`, `C$ CAD`, `AED`, and `฿ THB`.
- **Granular Expense Sliders**: Customize Transit, Lodging/Hostel, Street Food, Activities, and Emergency Buffer.
- **Student Regional Hacks**: In-app tips for student rail concessions (IRCTC, Eurail, Amtrak, JR Pass), free museum days, and food co-ops.

### 📂 5. Offline Vault & High-Definition PDF Export
- **Local Trip Vault**: Save favorite generated itineraries to browser memory for offline access during flights or train journeys.
- **Single-Click PDF Downloader**: Clean, formatted print-ready PDF export preserving emojis, markdown tables, and daily schedules.

### 🔥 6. 16 Curated Trending Student Hotspots
- **Classified Scope Filters**: Toggle between **`🌍 All (16)`**, **`🇮🇳 National (8)`**, and **`✈️ International (8)`** hotspots.
  - **🇮🇳 National**: *Goa, Manali & Kasol, Jaipur & Udaipur, Rishikesh, Varanasi, Munnar & Kochi, Leh-Ladakh, Shillong & Meghalaya*.
  - **✈️ International**: *Tokyo, Bali, Bangkok & Phuket, Rome, Amsterdam, Kyoto, Paris, Dubai*.
- **Live Currency Costs**: Hotspot daily estimates automatically adjust to your active region currency.

### 🌓 7. Premium Adaptive UI & Animations
- **Zero-Flicker Page Router**: Pre-paint synchronous routing preventing page jumps or theme flashes on reload.
- **Glassmorphic Navbar**: Translucent backdrop with spring auto-hide on scroll-down and reveal on scroll-up.
- **Constellation Canvas**: Animated background starfield and particle sky dynamics.

---

## 🛠️ Technology Stack

| Layer | Technology |
|---|---|
| **Backend Framework** | [FastAPI](https://fastapi.tiangolo.com/) (Asynchronous Python Web Framework) |
| **ASGI Server** | [Uvicorn](https://www.uvicorn.org/) |
| **AI Inference** | [Groq Cloud API](https://groq.com/) (Llama-3.3-70b-versatile) |
| **Geocoding** | [Geopy](https://geopy.readthedocs.io/) (Nominatim OpenStreetMap API) |
| **Validation** | [Pydantic v2](https://docs.pydantic.dev/) |
| **Frontend Architecture**| Vanilla JS Single-Page Application (SPA) |
| **Styling & Theme** | [Tailwind CSS v3](https://tailwindcss.com/) + Custom Glassmorphism & Light/Dark themes |
| **Maps & Tiles** | [Leaflet.js](https://leafletjs.com/) & OpenStreetMap CartoDB tiles |
| **Markdown & PDF** | [Marked.js](https://marked.js.org/) & [html2pdf.js](https://github.com/eKoopmans/html2pdf.js) |

---

## 📂 Project Structure

```text
AI-Travel-Planner/
├── .devcontainer/
│   └── devcontainer.json    # VS Code / GitHub Codespaces environment
├── .gitignore               # Clean git exclusion rules
├── LICENSE                  # MIT Open Source License
├── README.md                # Comprehensive Project Documentation
├── app.py                   # Complete Application (FastAPI backend + Modern SPA Frontend)
└── requirements.txt         # Production Python dependencies
```

---

## 🚀 Quickstart & Installation

Follow these steps to run RoamAI locally on your machine:

### 1. Clone the Repository
```bash
git clone https://github.com/eleshkapri/AI-Travel-Planner.git
cd AI-Travel-Planner
```

### 2. Create and Activate a Virtual Environment
**On Windows (PowerShell):**
```powershell
python -m venv venv
.\venv\Scripts\activate
```

**On macOS / Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Set Your Groq API Key
Obtain a free API key from [Groq Cloud Console](https://console.groq.com/keys).

**On Windows (PowerShell):**
```powershell
$env:GROQ_API_KEY="gsk_your_actual_api_key_here"
```

**On macOS / Linux:**
```bash
export GROQ_API_KEY="gsk_your_actual_api_key_here"
```

*(Alternatively, you can create a `.env` file in the root directory containing `GROQ_API_KEY=gsk_your_key_here`)*

### 5. Launch the Server
```bash
uvicorn app:app --host 0.0.0.0 --port 8000 --reload
```

Open your browser and navigate to **`http://localhost:8000`** to start planning your next journey!

---

## 🌐 API Reference

### `POST /api/generate`
Generates a structured itinerary, budget breakdown, and landmark coordinates.

**Request Body:**
```json
{
  "destination": "Kyoto, Japan",
  "days": 4,
  "budget_level": "Student (Low)",
  "budget_amount": "50000",
  "currency": "INR",
  "region": "India",
  "interests": ["History & Shrines", "Street Food"],
  "must_visit": "Fushimi Inari, Arashiyama",
  "travel_pace": "Balanced"
}
```

**Response:**
```json
{
  "itinerary": "# 4-Day Kyoto Student Adventure...",
  "destination_coords": [35.0116, 135.7681],
  "markers": [
    { "name": "Fushimi Inari Taisha", "lat": 34.9671, "lon": 135.7727, "desc": "Iconic thousand red torii gates" },
    { "name": "Arashiyama Bamboo Grove", "lat": 35.0170, "lon": 135.6713, "desc": "Scenic towering bamboo paths" }
  ],
  "budget_breakdown": {
    "transit": "₹8,000",
    "stay": "₹12,000",
    "food": "₹9,000",
    "activities": "₹6,000",
    "buffer": "₹5,000",
    "total": "₹40,000"
  },
  "trip_summary": {
    "destination": "Kyoto, Japan",
    "days": 4
  }
}
```

---

## 📄 License

This project is distributed under the **MIT License**. See the [LICENSE](LICENSE) file for more information.

---

<div align="center">
  <sub>Built with ❤️ for student travelers & budget adventurers worldwide.</sub>
</div>
