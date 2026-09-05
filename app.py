import os
import re
import math
from typing import List, Optional
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from pydantic import BaseModel, Field
from groq import Groq
from geopy.geocoders import Nominatim

# Top-level FastAPI application instance required by Vercel
app = FastAPI(
    title="RoamAI • AI Student Travel Planner",
    description="Next-Gen 3D Modern Student Travel Planner powered by Groq AI",
    version="2.2.0"
)

# GZip Compression Middleware (Reduces HTML/JSON payload size by up to 80% on mobile)
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Security Response Headers Middleware
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response: Response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "SAMEORIGIN"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Permissions-Policy"] = "geolocation=(), camera=(), microphone=()"
        return response

app.add_middleware(SecurityHeadersMiddleware)

# Enable CORS with explicit safe settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

# In-memory coordinate cache to optimize performance & reduce external OSM lookups
COORD_CACHE = {
    # Goa
    "goa": [15.2993, 74.1240],
    "goa, india": [15.2993, 74.1240],
    "calangute beach": [15.5425, 73.7556],
    "calangute beach, goa": [15.5425, 73.7556],
    "baga beach & tito's lane": [15.5574, 73.7510],
    "baga beach, goa": [15.5574, 73.7510],
    "fort aguada & 17th-century lighthouse": [15.4924, 73.7736],
    "fort aguada, goa": [15.4924, 73.7736],
    "anjuna flea market & curties cliff": [15.5764, 73.7440],
    "anjuna flea market, goa": [15.5764, 73.7440],
    "chapora fort & vagator bluff": [15.6060, 73.7353],
    "chapora fort, goa": [15.6060, 73.7353],
    "fontainhas latin quarter (panaji)": [15.4967, 73.8311],
    "fontainhas, panaji, goa": [15.4967, 73.8311],
    "panaji": [15.4989, 73.8278],
    "panaji, goa": [15.4989, 73.8278],
    "basilica of bom jesus (old goa)": [15.5007, 73.9117],
    "basilica of bom jesus, goa": [15.5007, 73.9117],
    "se cathedral (old goa)": [15.5034, 73.9126],
    "se cathedral, goa": [15.5034, 73.9126],
    "miramar beach & dona paula viewpoint": [15.4767, 73.8067],
    "miramar beach, goa": [15.4767, 73.8067],
    "reis magos fort & cultural center": [15.4965, 73.8091],
    "reis magos fort, goa": [15.4965, 73.8091],
    "divar island village ferry": [15.5251, 73.9078],
    "divar island, goa": [15.5251, 73.9078],
    "dudhsagar waterfalls trek": [15.3156, 74.3143],
    "dudhsagar falls, goa": [15.3156, 74.3143],
    "sahakari spice farm & plantations": [15.4167, 74.0167],
    "sahakari spice farm, goa": [15.4167, 74.0167],
    "colva beach & coastal promenade": [15.2858, 73.9105],
    "colva beach, goa": [15.2858, 73.9105],
    "benaulim beach & artisan crafts": [15.2570, 73.9160],
    "benaulim beach, goa": [15.2570, 73.9160],
    "cabo de rama fort & cliff": [15.0874, 73.9199],
    "cabo de rama fort, goa": [15.0874, 73.9199],
    "agonda beach & turtle sanctuary": [15.0423, 73.9865],
    "agonda beach, goa": [15.0423, 73.9865],
    "palolem beach & crescent bay": [15.0093, 74.0242],
    "palolem beach, goa": [15.0093, 74.0242],
    "butterfly beach & secret marine cove": [15.0195, 74.0016],
    "butterfly beach, goa": [15.0195, 74.0016],
    "arambol sweet water lake": [15.6790, 73.7050],
    "arambol beach, goa": [15.6790, 73.7050],
    "morjim beach (turtle nesting shore)": [15.6225, 73.7299],
    "morjim beach, goa": [15.6225, 73.7299],
    "chorao island & salim ali bird sanctuary": [15.5186, 73.8647],
    "chorao island, goa": [15.5186, 73.8647],

    # Manali & Kasol
    "manali": [32.2396, 77.1887],
    "manali, himachal pradesh, india": [32.2396, 77.1887],
    "old manali village & cafes": [32.2530, 77.1764],
    "hadimba devi temple & cedar woods": [32.2483, 77.1804],
    "vashisht hot water sulfur springs": [32.2612, 77.1912],
    "jogini waterfall trek": [32.2678, 77.1978],
    "solang valley adventure hub": [32.3167, 77.1583],
    "rohtang pass & snow plateau": [32.3716, 77.2466],
    "sethan igloo village & hampta trail": [32.2030, 77.2280],
    "kasol backpacker market & parvati river": [32.0100, 77.3150],
    "chalal pine forest trail": [32.0150, 77.3250],
    "manikaran sahib gurudwara & springs": [32.0270, 77.3480],
    "tosh village & glacier viewpoints": [32.0180, 77.4490],
    "kheerganga hot springs trek": [31.9890, 77.5140],
    "naggar castle & roerich gallery": [32.1150, 77.1680],
    "jana waterfall & local dhaba": [32.1350, 77.1920],

    # Jaipur & Udaipur
    "jaipur": [26.9124, 75.7873],
    "jaipur, rajasthan, india": [26.9124, 75.7873],
    "hawa mahal (palace of winds)": [26.9239, 75.8267],
    "amer fort & elephant ramparts": [26.9855, 75.8513],
    "city palace & courtyards": [26.9258, 75.8237],
    "jantar mantar unesco observatory": [26.9248, 75.8246],
    "nahargarh fort sunset bastion": [26.9372, 75.8156],
    "jal mahal (water palace)": [26.9535, 75.8462],
    "bapu bazaar & johari jewels": [26.9198, 75.8231],
    "albert hall state museum": [26.9117, 75.8194],
    "udaipur": [24.5854, 73.7125],
    "lake pichola & boat jetty (udaipur)": [24.5765, 73.6800],
    "city palace of udaipur": [24.5764, 73.6835],
    "jag mandir island palace": [24.5681, 73.6780],
    "monsoon palace (sajjangarh)": [24.5950, 73.6370],
    "saheliyon-ki-bari fountains": [24.6015, 73.6854],
    "fatehsagar lake promenade": [24.5986, 73.6740],

    # Rishikesh
    "rishikesh": [30.0869, 78.2676],
    "rishikesh, uttarakhand, india": [30.0869, 78.2676],
    "laxman jhula & suspension bridge": [30.1264, 78.3262],
    "ram jhula & riverside ghats": [30.1189, 78.3144],
    "triveni ghat (maha ganga aarti)": [30.1040, 78.2936],
    "the beatles ashram (chaurasi kutia)": [30.1147, 78.3128],
    "neer garh waterfall hike": [30.1444, 78.3378],
    "shivpuri white-water rafting camp": [30.1420, 78.3890],
    "vashistha meditative cave": [30.1580, 78.4120],
    "kunjapuri devi sunrise temple": [30.1650, 78.3050],
    "parmarth niketan ashram": [30.1170, 78.3130],

    # Varanasi
    "varanasi": [25.3176, 82.9739],
    "varanasi, uttar pradesh, india": [25.3176, 82.9739],
    "dashashwamedh ghat (grand evening aarti)": [25.3078, 83.0106],
    "assi ghat (sunrise subah-e-banaras)": [25.2917, 83.0069],
    "kashi vishwanath golden corridor": [25.3109, 83.0107],
    "manikarnika sacred cremation ghat": [25.3108, 83.0142],
    "sarnath dhamek stupa & deer park": [25.3811, 83.0214],
    "banaras hindu university (bhu campus)": [25.2677, 82.9913],
    "ramnagar fort & antique museum": [25.2688, 83.0289],
    "godowlia market & chaat alleys": [25.3100, 83.0080],

    # Munnar & Kochi
    "munnar": [10.0889, 77.0595],
    "munnar, kerala, india": [10.0889, 77.0595],
    "fort kochi chinese fishing nets": [9.9657, 76.2422],
    "mattancherry jew town & palace": [9.9575, 76.2592],
    "eravikulam national park (nilgiri tahr)": [10.1500, 77.0500],
    "tata tea museum & gardens": [10.0910, 77.0600],
    "mattupetty dam & lake speedboating": [10.1060, 77.1240],
    "top station western ghats vista": [10.1250, 77.2450],
    "attukad misty waterfall": [10.0530, 77.0420],

    # Leh Ladakh
    "leh ladakh": [34.1526, 77.5771],
    "leh ladakh, india": [34.1526, 77.5771],
    "shanti stupa sunrise dome": [34.1680, 77.5810],
    "leh royal palace": [34.1650, 77.5860],
    "khardung la (high altitude pass)": [34.2789, 77.6044],
    "nubra valley & hunder sand dunes": [34.5800, 77.4700],
    "diskit monastery & maitreya buddha": [34.5420, 77.5600],
    "pangong tso turquoise alpine lake": [33.7595, 78.6674],
    "magnetic hill & gravity illusion": [34.1900, 77.3500],
    "thiksey monastery gompa": [34.0580, 77.6670],

    # Shillong & Meghalaya
    "shillong": [25.5788, 91.8933],
    "shillong, meghalaya, india": [25.5788, 91.8933],
    "police bazar & live music cafes": [25.5760, 91.8840],
    "ward's lake & cherry blossoms": [25.5740, 91.8880],
    "elephant falls three-tier cascade": [25.5360, 91.8240],
    "umiam lake (barapani watersports)": [25.6600, 91.9000],
    "laitlum grand canyons": [25.4500, 91.9000],
    "nohkalikai falls & cherrapunji": [25.2750, 91.7000],
    "double decker living root bridge": [25.2500, 91.6700],
    "dawki umngot crystal river": [25.1850, 92.0190],
    "mawlynnong cleanest village": [25.2010, 91.9160],

    # Tokyo
    "tokyo": [35.6762, 139.6503],
    "tokyo, japan": [35.6762, 139.6503],
    "shibuya crossing & hachiko": [35.6595, 139.7005],
    "senso-ji temple & asakusa street": [35.7148, 139.7967],
    "akihabara anime & gaming district": [35.6984, 139.7731],
    "shinjuku gyoen national garden": [35.6852, 139.7101],
    "tokyo skytree panorama deck": [35.7101, 139.8107],
    "meiji shrine & yoyogi forest": [35.6764, 139.6993],
    "harajuku takeshita street fashion": [35.6716, 139.7032],
    "tsukiji outer fish & seafood market": [35.6655, 139.7708],

    # Bali
    "bali": [-8.4095, 115.1889],
    "bali, indonesia": [-8.4095, 115.1889],
    "ubud monkey forest sanctuary": [-8.5194, 115.2606],
    "tegallalang emerald rice terraces": [-8.4312, 115.2778],
    "tanah lot sea temple & waves": [-8.6212, 115.0868],
    "uluwatu cliff temple & kecak dance": [-8.8291, 115.0849],
    "canggu echo beach surf breaks": [-8.6500, 115.1300],
    "mount batur volcano sunrise trek": [-8.2421, 115.3753],
    "nusa penida kelingking cliff bay": [-8.7500, 115.4700],

    # Bangkok & Phuket
    "bangkok": [13.7563, 100.5018],
    "bangkok, thailand": [13.7563, 100.5018],
    "grand palace & emerald buddha": [13.7500, 100.4914],
    "wat arun (temple of dawn)": [13.7437, 100.4889],
    "chatuchak weekend market": [13.7999, 100.5508],
    "khao san road backpacker alley": [13.7589, 100.4974],
    "patong beach & bangla nightlife": [7.8960, 98.2970],
    "old phuket town sino-portuguese lanes": [7.8840, 98.3880],
    "phi phi islands & maya bay": [7.7407, 98.7784]
}

def sanitize_str(val: Optional[str], max_len: int = 120) -> str:
    if not val:
        return ""
    cleaned = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', str(val)).strip()
    return cleaned[:max_len]

class TripRequest(BaseModel):
    destination: str = Field(..., min_length=1, max_length=120)
    days: int = Field(default=3, ge=1, le=90)
    budget_level: str = Field(default="Student (Low)", max_length=50)
    budget_amount: Optional[str] = Field(default="", max_length=40)
    currency: Optional[str] = Field(default="USD", max_length=10)
    region: Optional[str] = Field(default="Global / USD", max_length=80)
    interests: List[str] = Field(default=[], max_length=25)
    must_visit: Optional[str] = Field(default="", max_length=120)
    travel_pace: Optional[str] = Field(default="Balanced", max_length=40)
    accommodation_style: Optional[str] = Field(default="Hostel / Backpacker", max_length=60)
    student_mode: Optional[bool] = Field(default=True)

def get_destination_key(dest_str: Optional[str]) -> Optional[str]:
    if not dest_str:
        return None
    dest_lower = dest_str.lower()
    aliases = {
        "goa": ["goa"],
        "manali": ["manali", "kasol", "kullu"],
        "jaipur": ["jaipur", "udaipur", "jodhpur", "rajasthan"],
        "rishikesh": ["rishikesh", "haridwar", "dehradun"],
        "varanasi": ["varanasi", "kashi", "banaras"],
        "leh": ["leh", "ladakh"],
        "tokyo": ["tokyo", "japan", "kyoto", "osaka"]
    }
    for k, words in aliases.items():
        if any(w in dest_lower for w in words):
            return k
    return None

def get_coordinates(location_name: str, destination_context: Optional[str] = None):
    if not location_name:
        return None
    raw = location_name.strip()
    cleaned = raw.lower()
    cleaned = re.sub(r'^(destination:\s*|must visit:\s*)', '', cleaned).strip()
    
    # 1. Exact match on cleaned full query
    if cleaned in COORD_CACHE:
        return COORD_CACHE[cleaned]
    
    # 2. Extract primary landmark name if comma-separated
    parts = [p.strip() for p in cleaned.split(",") if p.strip()]
    primary = parts[0] if parts else cleaned
    
    # 3. Check within DESTINATION_DB for the given destination if available
    dest_ctx = destination_context or (parts[1] if len(parts) > 1 else None)
    dest_key = get_destination_key(dest_ctx) if dest_ctx else None
    if dest_key and "DESTINATION_DB" in globals() and dest_key in DESTINATION_DB:
        db_info = DESTINATION_DB[dest_key]
        for lm in db_info.get("landmarks", []):
            lm_name = lm[0].lower()
            if primary in lm_name or lm_name in primary:
                return lm[1]
            p_tokens = set(re.findall(r'\b[a-z]{3,}\b', primary))
            l_tokens = set(re.findall(r'\b[a-z]{3,}\b', lm_name))
            if len(p_tokens & l_tokens) >= 2:
                return lm[1]

    # 4. Direct exact match on primary landmark
    if primary in COORD_CACHE:
        return COORD_CACHE[primary]
        
    # 5. Safe substring match against COORD_CACHE
    for k, v in COORD_CACHE.items():
        if len(k) < 4 or len(primary) < 4:
            continue
        # Primary landmark inside cached key (e.g. "shanti stupa" in "shanti stupa sunrise dome")
        if primary in k:
            return v
        # Cached key inside primary only if it's a specific landmark (not a short city name)
        if (len(k) >= 10 or " " in k) and k in primary:
            return v

    # 6. Geocoding via Nominatim fallback
    try:
        geolocator = Nominatim(user_agent="roamai_travel_architect_v4_secure")
        location = geolocator.geocode(location_name, timeout=5)
        if not location and len(parts) > 1:
            location = geolocator.geocode(parts[0], timeout=5)
        if location:
            coords = [round(location.latitude, 5), round(location.longitude, 5)]
            COORD_CACHE[cleaned] = coords
            COORD_CACHE[primary] = coords
            return coords
    except Exception:
        pass

    return None

DESTINATION_DB = {
    "goa": {
        "title": "Sun-Kissed Coastlines, Portuguese Forts & Tropical Shacks",
        "default_coords": [15.2993, 74.1240],
        "dishes": ["Goan Fish Curry Thali", "Poi with Ros Omelette", "Chorizo Pao", "Bebinca Dessert", "Kingfish Rava Fry"],
        "savings_tip": "Rent an automatic scooter (~₹350/day) to slash transit costs by 70% compared to local taxis. Eat at authentic local bhojanalayas for ₹150 hearty fish thalis.",
        "transit_tip": "Use Kadamba state shuttle buses for budget inter-city travel between Panaji, Mapusa, and Margao (₹20-40 per ticket).",
        "landmarks": [
            ("Calangute Beach", [15.5425, 73.7556], "North Beach Strip", "Sunbathing, beach volleyball, and watersports along Goa's most famous coastal strip."),
            ("Baga Beach & Tito's Lane", [15.5574, 73.7510], "North Nightlife Hub", "Beach shacks, live music, and evening student social gatherings."),
            ("Fort Aguada & 17th-Century Lighthouse", [15.4924, 73.7736], "Historic North Coast", "Portuguese coastal fortification with panoramic Arabian Sea views."),
            ("Anjuna Flea Market & Curties Cliff", [15.5764, 73.7440], "Bohemian North", "Handmade crafts, hippie clothing, and cliffside sunset acoustic sessions."),
            ("Chapora Fort & Vagator Bluff", [15.6060, 73.7353], "North Hilltop", "Iconic Dil Chahta Hai ramparts overlooking red cliffs and Ozran Beach."),
            ("Fontainhas Latin Quarter (Panaji)", [15.4967, 73.8311], "Central Heritage", "Pastel Portuguese colonial villas, quaint bakeries, and art galleries."),
            ("Basilica of Bom Jesus (Old Goa)", [15.5007, 73.9117], "UNESCO Heritage Center", "16th-century baroque architecture and resting place of St. Francis Xavier."),
            ("Se Cathedral (Old Goa)", [15.5034, 73.9126], "UNESCO Heritage Center", "Historic grand cathedral housing the legendary Golden Bell."),
            ("Miramar Beach & Dona Paula Viewpoint", [15.4767, 73.8067], "Central Coast", "Breezy promenade where the Mandovi river merges into the Arabian Sea."),
            ("Reis Magos Fort & Cultural Center", [15.4965, 73.8091], "Mandovi Riverfront", "Restored bastion showcasing Mario Miranda cartoons and harbor vistas."),
            ("Divar Island Village Ferry", [15.5251, 73.9078], "River Island Escape", "Scenic hop-on car ferry across Mandovi river to tranquil heritage villages."),
            ("Dudhsagar Waterfalls Trek", [15.3156, 74.3143], "Western Ghats Frontier", "Four-tiered majestic 310m waterfall enveloped in lush biodiversity jungle."),
            ("Sahakari Spice Farm & Plantations", [15.4167, 74.0167], "Ponda Hinterland", "Guided organic spice walking tour with traditional Goan buffet lunch."),
            ("Colva Beach & Coastal Promenade", [15.2858, 73.9105], "South Goa Shore", "Endless white sand shorelines, traditional fishing boats, and calm shacks."),
            ("Benaulim Beach & Artisan Crafts", [15.2570, 73.9160], "South Coast Village", "Calm swimming waters, dolphin-spotting boat trips, and seaside dinners."),
            ("Cabo de Rama Fort & Cliff", [15.0874, 73.9199], "Dramatic South Bastion", "Ancient cliffside citadel with breathtaking 270-degree turquoise sea vistas."),
            ("Agonda Beach & Turtle Sanctuary", [15.0423, 73.9865], "Quiet South Shore", "Pristine, peaceful shores known for Olive Ridley turtle nesting and sunset tranquility."),
            ("Palolem Beach & Crescent Bay", [15.0093, 74.0242], "Iconic South Paradise", "Gentle shallow turquoise bay, kayak rentals, and colorful beach cottages."),
            ("Butterfly Beach & Secret Marine Cove", [15.0195, 74.0016], "Hidden South Enclave", "Secluded semicircular bay accessible by boat or jungle hike, famous for dolphins."),
            ("Arambol Sweet Water Lake", [15.6790, 73.7050], "Far North Bohemian Haven", "Freshwater lagoon meeting the ocean, drum circles, and jungle trails."),
            ("Morjim Beach (Turtle Nesting Shore)", [15.6225, 73.7299], "North Wildlife Sanctuary", "Protected serene beach known as Little Russia, perfect for quiet reading and sunset."),
            ("Chorao Island & Salim Ali Bird Sanctuary", [15.5186, 73.8647], "Mangrove Estuary", "Serene canoe rides through estuarine mangrove swamps spotting kingfishers.")
        ]
    },
    "manali": {
        "title": "Himalayan Alpine Passes, Pine Valleys & Backpacker Trails",
        "default_coords": [32.2396, 77.1887],
        "dishes": ["Siddu with Ghee & Chutney", "Kullu Trout Fish", "Tibetan Thukpa & Momos", "Dham Feast", "Mittha Sweet Rice"],
        "savings_tip": "Stay in backpacker hostels in Old Manali or Vashisht for ₹400-600/night with mountain views. Use shared HRTC local buses to Solang and Naggar for ₹25 instead of expensive cabs.",
        "transit_tip": "Local Himachal Road Transport Corporation (HRTC) green buses connect Manali, Kullu, and Naggar every 30 minutes at budget student fares.",
        "landmarks": [
            ("Old Manali Village & Cafes", [32.2530, 77.1764], "Old Manali", "Cobblestone alleys, indie bakeries, apple orchards, and acoustic rooftop jams."),
            ("Hadimba Devi Temple & Cedar Woods", [32.2483, 77.1804], "Cedar Forest", "Ancient 16th-century pagoda-style timber shrine surrounded by giant deodars."),
            ("Vashisht Hot Water Sulfur Springs", [32.2612, 77.1912], "Thermal Springs", "Natural therapeutic hot sulfur baths and scenic rooftop cafes."),
            ("Jogini Waterfall Trek", [32.2678, 77.1978], "Nature Trail", "Cascading multi-tiered alpine waterfall hike through pine forests and orchards."),
            ("Solang Valley Adventure Hub", [32.3167, 77.1583], "Alpine Valley", "Paragliding, zorbing, ropeways, and stunning snowcapped Pir Panjal views."),
            ("Rohtang Pass & Snow Plateau", [32.3716, 77.2466], "High Altitude Pass", "High-altitude 3,978m gateway with breathtaking 360-degree Himalayan vistas."),
            ("Sethan Igloo Village & Hampta Trail", [32.2030, 77.2280], "Offbeat Enclave", "Traditional Buddhist horse-riding hamlet overlooking the Dhauladhar range."),
            ("Kasol Backpacker Market & Parvati River", [32.0100, 77.3150], "Parvati Valley", "Riverside Israeli bakeries, psychedelic art cafes, and pine woods."),
            ("Chalal Pine Forest Trail", [32.0150, 77.3250], "Parvati Valley", "Tranquil hiking trail along the crystal turquoise Parvati river."),
            ("Manikaran Sahib Gurudwara & Springs", [32.0270, 77.3480], "Sacred Valley", "Famous geothermal hot springs, free community langar, and sacred river ghats."),
            ("Tosh Village & Glacier Viewpoints", [32.0180, 77.4490], "Upper Parvati", "Cliff-hanging village with dramatic views of snow peaks and glacier streams."),
            ("Kheerganga Hot Springs Trek", [31.9890, 77.5140], "Alpine Summit", "Rewarding 12km forest trek culminating in natural hot sulfur springs atop the mountain."),
            ("Naggar Castle & Roerich Gallery", [32.1150, 77.1680], "Heritage Valley", "15th-century wood-and-stone royal fortress overlooking the Beas valley."),
            ("Jana Waterfall & Local Dhaba", [32.1350, 77.1920], "Hidden Falls", "Scenic waterfall setting serving authentic traditional Himachali food on leaf plates.")
        ]
    },
    "jaipur": {
        "title": "Royal Fortresses, Grand Palaces & Vibrant Bazaars",
        "default_coords": [26.9124, 75.7873],
        "dishes": ["Pyaaz Kachori & Lassi", "Dal Baati Churma", "Laal Maas", "Ghewar Sweet", "Mirchi Vada"],
        "savings_tip": "Buy the Rajasthan Tourism composite student ticket (~₹100) which grants entry to Amer Fort, Hawa Mahal, Jantar Mantar, Nahargarh, and Albert Hall.",
        "transit_tip": "Use the Jaipur Metro from Mansarovar to Badi Chaupar (₹15) to reach Old Pink City monuments instantly without traffic.",
        "landmarks": [
            ("Hawa Mahal (Palace of Winds)", [26.9239, 75.8267], "Pink City Core", "Iconic five-story pink sandstone honeycomb facade with 953 jharokhas."),
            ("Amer Fort & Elephant Ramparts", [26.9855, 75.8513], "Amber Hills", "Massive hilltop Rajput fortress featuring Sheesh Mahal mirror mosaics."),
            ("City Palace & Courtyards", [26.9258, 75.8237], "Royal Quarter", "Royal residence blending Mughal and Rajput architecture with Peacock Gate."),
            ("Jantar Mantar UNESCO Observatory", [26.9248, 75.8246], "Historic Science", "World's largest stone sundial and 18th-century astronomical instruments."),
            ("Nahargarh Fort Sunset Bastion", [26.9372, 75.8156], "Aravalli Ridge", "Edge-of-the-cliff ramparts with the best sunset panorama over Jaipur city."),
            ("Jal Mahal (Water Palace)", [26.9535, 75.8462], "Man Sagar Lake", "Serene floating red sandstone palace in the center of Man Sagar Lake."),
            ("Bapu Bazaar & Johari Jewels", [26.9198, 75.8231], "Pink City Bazaar", "Bustling traditional market for jaipuri quilts, mojris, and street snacks."),
            ("Albert Hall State Museum", [26.9117, 75.8194], "Ram Niwas Garden", "Indo-Saracenic museum housing royal artifacts and lit up brilliantly at night."),
            ("Lake Pichola & Boat Jetty (Udaipur)", [24.5765, 73.6800], "Lakeside Udaipur", "Romantic boat cruises past floating marble palaces on tranquil waters."),
            ("City Palace of Udaipur", [24.5764, 73.6835], "Lakeside Citadel", "Sprawling lakeside palace complex with ornate balconies and mirror domes."),
            ("Jag Mandir Island Palace", [24.5681, 73.6780], "Lake Island", "Garden palace on Lake Pichola surrounded by stone elephants and arches."),
            ("Monsoon Palace (Sajjangarh)", [24.5950, 73.6370], "Hilltop Peak", "Hilltop palace built to track monsoon clouds, offering stunning sunset views.")
        ]
    },
    "rishikesh": {
        "title": "Yoga Capitals, Sacred Ganga Rapids & Beatles Trails",
        "default_coords": [30.0869, 78.2676],
        "dishes": ["Aloo Puri by the Ghats", "Ayurvedic Thali", "Wood-fired Pizza & Chai", "Garhwali Kafuli", "Fresh Fruit Smoothie Bowls"],
        "savings_tip": "Stay in riverside backpacker camps or ashrams in Tapovan for ₹300-500/night. Rent a bicycle to navigate between Laxman Jhula and Ram Jhula.",
        "transit_tip": "Shared Vikram three-wheelers ferry travelers between Rishikesh Bus Stand, Triveni Ghat, and Tapovan for just ₹15-20.",
        "landmarks": [
            ("Laxman Jhula & Suspension Bridge", [30.1264, 78.3262], "River Crossing", "Iconic iron suspension bridge across the emerald Ganga with views of riverside temples."),
            ("Ram Jhula & Riverside Ghats", [30.1189, 78.3144], "Spiritual Hub", "Spiritual pedestrian bridge surrounded by Vedic ashrams, bookstores, and tea stalls."),
            ("Triveni Ghat (Maha Ganga Aarti)", [30.1040, 78.2936], "Sacred Ghat", "Dusk ritual with synchronized brass lamps, Vedic chanting, and floating leaf diyas."),
            ("The Beatles Ashram (Chaurasi Kutia)", [30.1147, 78.3128], "Rajaji Forest Edge", "Graffiti-covered meditation domes where The Beatles wrote the White Album in 1968."),
            ("Neer Garh Waterfall Hike", [30.1444, 78.3378], "Jungle Trail", "Multi-tiered turquoise mountain spring waterfall with natural swimming pools."),
            ("Shivpuri White-Water Rafting Camp", [30.1420, 78.3890], "Rapid Zone", "Grade III/IV adrenaline rapids through roller-coaster and golf-course gorges."),
            ("Vashistha Meditative Cave", [30.1580, 78.4120], "Ganga Riverside", "Ancient peaceful meditation cave located right on a quiet white-sand river beach."),
            ("Kunjapuri Devi Sunrise Temple", [30.1650, 78.3050], "Himalayan Ridge", "Ridge-top temple offering unforgettable sunrise panoramas of high Himalayan snow peaks."),
            ("Parmarth Niketan Ashram", [30.1170, 78.3130], "Ghat Promenade", "Sprawling spiritual haven with clean gardens, yoga halls, and iconic Shiva statue.")
        ]
    },
    "tokyo": {
        "title": "Neon Metropolises, Ancient Shrines & Pop Culture",
        "default_coords": [35.6762, 139.6503],
        "dishes": ["Tonkotsu Ramen (Ichiran)", "Tsukiji Fresh Sushi", "Crispy Takoyaki", "Matcha Soft Serve", "Yakitori Skewers"],
        "savings_tip": "Buy the 72-hour Tokyo Subway Ticket (~¥1,500) for unlimited rides on all Tokyo Metro and Toei Subway lines. Eat budget meals at 7-Eleven and Lawson.",
        "transit_tip": "Use a digital Suica or Pasmo card on your smartphone for tap-and-go rides across all trains, buses, and convenience stores.",
        "landmarks": [
            ("Shibuya Crossing & Hachiko", [35.6595, 139.7005], "Shibuya", "World's busiest pedestrian intersection illuminated by giant neon screens."),
            ("Senso-ji Temple & Asakusa Street", [35.7148, 139.7967], "Asakusa", "Tokyo's oldest Buddhist temple fronted by vibrant traditional food stalls."),
            ("Akihabara Anime & Gaming District", [35.6984, 139.7731], "Akihabara", "Mecca of anime culture, retro arcade halls, manga stores, and electronics."),
            ("Shinjuku Gyoen National Garden", [35.6852, 139.7101], "Shinjuku", "Lush sprawling oasis blending traditional Japanese, English, and French gardens."),
            ("Tokyo Skytree Panorama Deck", [35.7101, 139.8107], "Sumida", "Tallest tower in the world offering views spanning Mount Fuji to Tokyo Bay."),
            ("Meiji Shrine & Yoyogi Forest", [35.6764, 139.6993], "Harajuku", "Tranquil Shinto shrine enveloped in an evergreen forest of over 120,000 trees."),
            ("Harajuku Takeshita Street Fashion", [35.6716, 139.7032], "Harajuku", "Bustling youth fashion alley famous for crepe stands, kawaii boutiques, and vintage shops."),
            ("Tsukiji Outer Fish & Seafood Market", [35.6655, 139.7708], "Chuo", "Historic food market serving fresh sashimi, tamagoyaki, and grilled seafood.")
        ]
    },
    "leh": {
        "title": "Himalayan Moonscapes, High Mountain Passes & Buddhist Monasteries",
        "default_coords": [34.1526, 77.5771],
        "dishes": ["Ladakhi Thukpa & Skyu", "Butter Tea (Gur Gur Chai)", "Tingmo with Veggie Stew", "Chhurpi Yak Cheese", "Apricot Jam with Khambir Bread"],
        "savings_tip": "Rent an Enfield or scooter in Leh Main Market for ₹800-1200/day to explore Sham Valley and Thiksey. Stay in traditional family homestays in Changspa for ₹500/night.",
        "transit_tip": "Shared local JKSRTC buses and shared taxis run from Leh Bus Stand to Nubra, Pangong, and Thiksey at a fraction of private taxi union rates.",
        "phases": [
            ("Phase 1: Acclimatization & Central Indus Valley Monasteries", "Central Leh & Upper Indus", "Focus on gentle altitude acclimatization, royal palaces, Tibetan heritage bazaars, and hillside gompas."),
            ("Phase 2: Ancient Silk Route & Sham Valley Moonland Circuit", "Sham Valley & Lower Ladakh", "Dramatic moonland canyons, magnetic anomalies, Basgo mud fortress, and millennium-old Alchi frescoes."),
            ("Phase 3: Crossing Khardung La into Nubra Valley & Karakoram Frontiers", "Nubra & Shyok Valleys", "High passes at 5,359m, Bactrian camel safaris in Hunder dunes, Colossal Maitreya, and Balti villages."),
            ("Phase 4: Changthang High Plateau, Alpine Lakes & Hanle Dark Sky Reserve", "Changthang & High Lakes", "134km turquoise Pangong Tso, high wetlands of Tso Moriri, white salt flats of Tso Kar, and Hanle astrophotography."),
            ("Phase 5: The Great Zanskar Trans-Himalayan & Suru Valley Expedition", "Zanskar & Suru Valley", "Deep glacial valleys under 7,135m Nun-Kun peaks, cliffside Phuktal cave monastery, and ancient Padum capital.")
        ],
        "landmarks": [
            ('Leh Main Market & Heritage Bazaar', [34.1642, 77.5848], 'Leh Center', 'Vibrant pedestrian market with Tibetan jewelry, pashmina shawls, and apricot stalls.'),
            ('Leh Royal Palace & Tsemo Ridge', [34.1656, 77.5862], 'Old Town Ridge', 'Historic 17th-century nine-story Tibetan royal palace overlooking Leh city.'),
            ('Shanti Stupa Sunrise Dome', [34.1685, 77.5815], 'Changspa Hill', 'White-domed Buddhist stupa offering spectacular 360-degree views of the Indus Valley.'),
            ('Hall of Fame Military Museum', [34.1415, 77.545], 'Airport Road', 'Memorial museum built by Indian Army honoring Himalayan soldiers and Ladakhi culture.'),
            ('Spituk Gompa Monastery', [34.1298, 77.5255], 'Spituk', '11th-century hilltop monastery overlooking the Indus river and airstrip.'),
            ('Shey Palace & Monastic Sanctuary', [34.072, 77.634], 'Shey Valley', 'Former summer capital of Ladakh housing a giant copper-gilt Shakyamuni Buddha.'),
            ('Thiksey Monastery (Mini Potala)', [34.0585, 77.6672], 'Indus Valley', "Twelve-story architectural wonder resembling Lhasa's Potala Palace."),
            ('Hemis Monastery & Antique Museum', [33.9125, 77.707], 'Hemis Gorge', 'Largest and richest Buddhist monastery in Ladakh, famous for its annual masked dance festival.'),
            ("Stakna Monastery (Tiger's Nose)", [34.004, 77.685], 'Indus Bank', 'Picturesque monastery perched dramatically on a rock resembling a tiger leaping.'),
            ('Matho Monastery & Oracle Sanctuary', [33.998, 77.645], 'Matho Village', '500-year-old Sakya sect monastery renowned for its mysterious trance-oracle festivals.'),
            ('Stok Royal Palace & Museum', [34.0025, 77.567], 'Stok Valley', 'Ancestral residence of the Ladakh royal family housing royal crowns and ancient thangkas.'),
            ('Saboo Village & Nature Trails', [34.138, 77.625], 'Saboo Oasis', 'Tranquil green oasis village with traditional Ladakhi mud homes and medicinal springs.'),
            ('Magnetic Hill Gravity Anomaly', [34.1912, 77.3524], 'Srinagar-Leh Highway', 'Famous optical illusion spot where parked vehicles appear to roll uphill.'),
            ('Gurudwara Pathar Sahib', [34.185, 77.382], 'Highway Fortress', "Historic 16th-century Sikh shrine built to commemorate Guru Nanak's visit."),
            ('Sangam (Indus & Zanskar Confluence)', [34.166, 77.334], 'Nimmu', 'Breathtaking meeting point of the brown Indus and emerald Zanskar rivers.'),
            ('Basgo Fortress Ruins & Frescoes', [34.221, 77.284], 'Basgo Citadel', 'Dramatic medieval clay mud-brick fortress and UNESCO-recognized ancient Buddha temple.'),
            ('Likir Monastery & Giant Maitreya', [34.293, 77.215], 'Likir Valley', 'Majestic monastery housing a 75-foot open-air golden Buddha amidst apricot orchards.'),
            ('Alchi Choskor 11th-Century Murals', [34.223, 77.175], 'Alchi Oasis', 'World-renowned Kashmiri-Buddhist painted murals and woodcarvings on the Indus river bank.'),
            ('Mangyu Hidden Monastic Hermitage', [34.246, 77.112], 'Hidden Canyon', 'Secluded 11th-century temple complex tucked away in a scenic mountain gorge.'),
            ('Lamayuru Moonland & Ancient Gompa', [34.283, 76.774], 'Moonland Canyon', "Extraterrestrial lunar landscape cliffs and Ladakh's oldest Yungdrung Bon-Buddhist monastery."),
            ('Wanla Historic Fortress & Temple', [34.254, 76.832], 'Wanla Gorge', 'Picturesque cliff-perched 14th-century monastery and royal defense ruins.'),
            ('Tingmosgang Royal Fortress & Nunnery', [34.312, 77.015], 'Tingmosgang', '15th-century historical capital with royal fortress ruins and lush apple orchards.'),
            ('Khardung La Pass (5,359m Summit)', [34.2789, 77.6044], 'High Altitude Pass', 'World-famous 5,359m high-altitude pass connecting Leh to the Nubra Valley.'),
            ('Diskit Monastery & Colossal Buddha', [34.5422, 77.5615], 'Nubra Valley', '14th-century cliff monastery crowned with a colossal 32-meter golden Buddha.'),
            ('Hunder Sand Dunes & Bactrian Camels', [34.583, 77.472], 'Nubra Desert', 'High-altitude cold desert sand dunes featuring double-humped Bactrian camel safaris.'),
            ('Sumur Samstanling Monastery Oasis', [34.625, 77.628], 'Nubra Riverside', 'Peaceful 19th-century Gelugpa monastery surrounded by prayer flags and berry groves.'),
            ('Panamik Sulfur Hot Springs', [34.789, 77.534], 'Upper Nubra', 'Natural therapeutic hot mineral sulfur pools near the Siachen glacier base.'),
            ('Turtuk Balti Heritage Village', [34.889, 76.828], 'Shyok Valley', 'Picturesque border village rich in Balti Muslim heritage, stone houses, and apricots.'),
            ('Tyakshi Indo-Pak Border Outpost', [34.845, 76.762], 'Northern Frontier', 'Northernmost point accessible to travelers with sweeping views of the Line of Control.'),
            ('Ensa Gompa Hermitage', [34.72, 77.58], 'Karakoram Cliff', 'Solitary ancient hermitage perched high on a sheer rock overlooking the Nubra river.'),
            ('Chang La Pass (5,360m Snow Summit)', [34.048, 77.93], 'Mountain Pass', 'Dramatic 5,360m snowy mountain pass en route to Pangong Lake.'),
            ('Tangtse Caravan Serai & Valley', [34.027, 78.188], 'Tangtse Hub', 'Traditional trading outpost village with ancient petroglyphs and Changthang yak pastures.'),
            ('Pangong Tso Alpine Lake (Spangmik)', [33.918, 78.657], 'Changthang Shore', 'Iconic 134km-long turquoise blue salt-water lake extending from India to Tibet.'),
            ('Man & Merak Remote Shoreline', [33.824, 78.785], 'Far Pangong', 'Quiet traditional lakefront hamlets offering intimate homestays and crystal-clear star views.'),
            ('Chushul War Memorial & Plains', [33.593, 78.658], 'Border Plateau', 'Historic 1962 battle memorial situated on a vast highland grassland plain.'),
            ('Nyoma Indus Bend & Monastery', [33.2, 78.667], 'Nyoma Plains', 'Riverside township with high-altitude air strip and ancient Buddhist hermitage.'),
            ('Hanle Dark Sky Reserve & Observatory', [32.78, 78.96], 'Hanle Basin', "India's premier certified International Dark Sky Reserve housing the Himalayan Chandra Telescope."),
            ('Umling La Pass (19,024 ft World Highest)', [32.695, 79.28], 'Highest Motor Road', "World's highest motorable pass crossing 19,024 feet over the Karakoram range."),
            ('Tso Moriri High Wetland (Korzok)', [32.967, 78.256], 'Rupshu Valley', 'Serene, remote Ramsar wetland lake inhabited by nomadic Changpa tribes and bar-headed geese.'),
            ('Tso Kar Salt Lake & Wildlife Basin', [33.31, 78.005], 'Tso Kar Plains', 'White salt-crusted lake basin teeming with rare black-necked cranes and Tibetan wild asses (Kiang).'),
            ('Puga Geothermal Sulfur Valley', [33.22, 78.33], 'Geothermal Basin', 'Eerily beautiful geothermal valley with bubbling mud springs, sulfur geysers, and steam vents.'),
            ('Kargil Heritage Town & Riverwalk', [34.5539, 76.1349], 'Suru Riverfront', 'Historic Silk Route crossroads bustling with Balti brass bazaars and dry fruit markets.'),
            ('Drass Kargil War Memorial & Tololing', [34.428, 75.76], 'Drass Valley', 'Second coldest inhabited place in the world and revered memorial honoring 1999 heroes.'),
            ('Suru Valley & Nun-Kun Glacier Peaks', [34.11, 75.98], 'Suru Valley', 'Lush emerald mountain valley framed by the colossal 7,135m twin peaks of Nun and Kun.'),
            ('Rangdum Fortress Monastery', [34.02, 76.32], 'Isolated Plateau', '18th-century Tibetan fortress monastery rising like an island in a vast windswept plain.'),
            ('Pensi La Pass (Gateway to Zanskar)', [33.85, 76.37], 'Glacial Pass', '4,400m pass overlooking the colossal hanging tongue of the Drang-Drung Glacier.'),
            ('Padum Ancient Zanskar Capital', [33.468, 76.879], 'Zanskar Center', 'Historic heart of Zanskar valley with traditional stupas, tea stalls, and apricot orchards.'),
            ('Karsha Monastic City on Cliff', [33.525, 76.905], 'Karsha Ridge', "Zanskar's largest Gelugpa monastery complex cascading dramatically down a sheer mountain cliff."),
            ('Phuktal Cliffside Cave Monastery', [33.272, 77.182], 'Tsarap Gorge', 'Legendary monastery constructed inside a massive natural cave over a limestone canyon.'),
            ('Zangla Royal Palace & Nunnery', [33.665, 76.985], 'Zangla Valley', 'Cliffside ruins of the former Zangla kings where Hungarian scholar Csoma de Kőrös lived in 1823.'),
            ('Shinku La Pass & Gombo Rangjon', [32.98, 77.2], 'Zanskar Frontier', 'Dramatic high pass guarded by the sacred monolithic rock tower of Gombo Rangjon.')
        ]
    },
    "varanasi": {
        "title": "Eternal Sacred Ghats, Spiritual Boat Rides & Ancient Lanes",
        "default_coords": [25.3176, 82.9739],
        "dishes": ["Banarasi Tamatar Chaat", "Malaiyo Saffron Froth", "Blue Lassi & Rabdi", "Kachori Jalebi Breakfast", "Baati Chokha"],
        "savings_tip": "Take budget shared wooden rowboats at Assi Ghat for ₹100 per person at sunrise instead of expensive private motorboats.",
        "transit_tip": "Explore the historic riverfront alleys on foot, and use e-rickshaws for ₹20-30 between Godowlia and Lanka (BHU).",
        "landmarks": [
            ("Dashashwamedh Ghat (Grand Evening Aarti)", [25.3078, 83.0106], "Main Riverfront", "Spectacular synchronized Maha Aarti with brass lamps and devotional hymns."),
            ("Assi Ghat (Sunrise Subah-e-Banaras)", [25.2917, 83.0069], "Southern Ghat", "Serene dawn classical music, morning yoga, and boat embarkation point."),
            ("Kashi Vishwanath Golden Corridor", [25.3109, 83.0107], "Sacred Core", "Revered golden-spire Jyotirlinga temple connecting directly to the Ganga."),
            ("Manikarnika Sacred Cremation Ghat", [25.3108, 83.0142], "Historic Riverfront", "Ancient holy cremation ghat steeped in Hindu philosophy of Moksha."),
            ("Sarnath Dhamek Stupa & Deer Park", [25.3811, 83.0214], "Buddhist Pilgrimage", "Sacred site where Lord Buddha delivered his first sermon post-enlightenment."),
            ("Banaras Hindu University (BHU Campus)", [25.2677, 82.9913], "Lanka", "Sprawling heritage university campus housing the New Vishwanath Temple."),
            ("Ramnagar Fort & Antique Museum", [25.2688, 83.0289], "Eastern Bank", "18th-century sandstone fortress of the Kashi Naresh with royal vintage car collections."),
            ("Godowlia Market & Chaat Alleys", [25.3100, 83.0080], "Old City", "Bustling foodie haven famous for spicy tamatar chaat and silk sari weaving shops.")
        ]
    }
}

# Auto-populate COORD_CACHE with all default coords and landmarks from DESTINATION_DB
for dest_k, dest_val in DESTINATION_DB.items():
    if "default_coords" in dest_val:
        COORD_CACHE[dest_k.lower()] = dest_val["default_coords"]
    for lm in dest_val.get("landmarks", []):
        if len(lm) > 1 and lm[1]:
            COORD_CACHE[lm[0].lower().strip()] = lm[1]

def generate_fallback_itinerary(
    destination: str,
    days: int,
    curr: str,
    region_info: str,
    budget_level: str,
    accom_style: str,
    interests: list,
    must_visit: str,
    pace: str,
    student_mode: bool = True
) -> str:
    multipliers = {
        "INR": 1.0, "USD": 0.012, "EUR": 0.011, "GBP": 0.0095, "JPY": 1.8,
        "AUD": 0.018, "CAD": 0.016, "AED": 0.044, "THB": 0.44
    }
    m = multipliers.get(curr, 0.012)
    tier_mult = 1.8 if ("Moderate" in budget_level or "Comfort" in budget_level) else (3.5 if ("Luxury" in budget_level or "Executive" in budget_level) else 1.0)

    if student_mode:
        base_stay = int(800 * m * tier_mult)
        base_food = int(500 * m * tier_mult)
        base_trans = int(300 * m * tier_mult)
        base_act = int(400 * m * tier_mult)
        if not accom_style or accom_style == "Hostel":
            accom_style = "Hostel / Backpacker"
    else:
        base_stay = int(2200 * m * tier_mult)
        base_food = int(1000 * m * tier_mult)
        base_trans = int(600 * m * tier_mult)
        base_act = int(800 * m * tier_mult)
        if not accom_style or accom_style == "Hostel":
            accom_style = "Boutique Hotel / Comfort Stay"

    total_stay = base_stay * days
    total_food = base_food * days
    total_trans = base_trans * days
    total_act = base_act * days
    est_total = total_stay + total_food + total_trans + total_act

    dest_lower = destination.lower()
    dest_key = None
    aliases = {
        "goa": ["goa"],
        "manali": ["manali", "kasol", "kullu"],
        "jaipur": ["jaipur", "udaipur", "jodhpur", "rajasthan"],
        "rishikesh": ["rishikesh", "haridwar", "dehradun"],
        "varanasi": ["varanasi", "kashi", "banaras"],
        "leh": ["leh", "ladakh"],
        "tokyo": ["tokyo", "japan", "kyoto", "osaka"]
    }
    for main_key, words in aliases.items():
        if any(w in dest_lower for w in words):
            dest_key = main_key
            break

    dest_info = DESTINATION_DB.get(dest_key)

    if dest_info:
        raw_pool = dest_info["landmarks"]
        title = dest_info["title"]
        savings_hack = dest_info["savings_tip"] if student_mode else "Pre-book signature sightseeing entries and regional rail passes online in advance for priority skip-the-line access."
        transit_hack = dest_info["transit_tip"] if student_mode else "Book express rail or trusted private vehicle hire for comfortable point-to-point transfers."
        dishes = dest_info["dishes"]
        dest_phases = dest_info.get("phases")
    else:
        clean_city = destination.split(",")[0].strip()
        title = f"Cultural Discovery & Student Exploration in {clean_city}" if student_mode else f"Cultural Discovery & Curated Journey in {clean_city}"
        savings_hack = "Carry a valid student identity card (ISIC) to unlock 20% to 50% concession discounts on transit passes, museums, and historical landmarks." if student_mode else "Purchase regional all-inclusive museum and transit passes to optimize entry costs and skip ticketing queues."
        transit_hack = "Download local transit apps and offline map data to travel like a local on subways and buses."
        dishes = ["Local Street Delicacies", "Regional Special Thali", "Artisan Bakery Pastries", "Famous Night Market Eats", "Street Noodle Bowls"]
        dest_phases = None
        raw_pool = [
            ("Historic Old Town Quarter", None, "Heritage Quarter", f"Explore the historic old town center of {clean_city}, cobblestone alleys, and iconic central plazas."),
            ("Waterfront Promenade & Marina", None, "Waterfront", "Stroll along scenic waterfront promenades and relax at bustling cafes."),
            ("Panoramic Hilltop Viewpoint", None, "Panoramic Vista", "Hike or ride up to the top panoramic vantage point overlooking the entire cityscape."),
            ("Grand Citadel & Fortress Ramparts", None, "Historic Bastion", "Explore centuries-old defensive walls, royal ramparts, and museum exhibits."),
            ("Artisan Food Street & Night Market", None, "Market District", "Browse handmade local crafts, vintage clothing stalls, and authentic street food snacks."),
            ("Botanical Gardens & Eco Trail", None, "Nature Sanctuary", "Unwind in lush gardens, scenic water bodies, and tranquil walking trails."),
            ("Cultural Arts & National Museum", None, "Cultural District", "Tour premier art galleries, exhibitions, and creative workshops."),
            ("Sunset Ridge & Acoustic Lounge", None, "Sunset Point", "Meet fellow travelers for golden-hour views followed by live music sessions."),
            ("Mountain Valley & Waterfalls Trail", None, "Excursion", "Short scenic ride to surrounding countryside, lush valleys, and scenic rivers."),
            ("Student Backpacker District" if student_mode else "Charming Bohemian Arts Quarter", None, "Youth Quarter" if student_mode else "Arts District", "Lively cafes, boutique shops, artisan bakeries, and vibrant street life."),
            ("Ancient Sacred Temple & Shrines", None, "Sacred Architecture", "Visit prominent architectural landmarks steeped in centuries of heritage."),
            ("Riverside Boardwalk & Pier", None, "Waterway", "Evening stroll along harbor docks, boat watching, and seafood restaurants."),
            ("Pine Ridge Nature Sanctuary", None, "Eco Trail", "Quiet morning bird-watching trail and lush native flora exploration."),
            ("Clocktower Plaza & Heritage Bazaar", None, "Commercial Core", "Discover antique treasures, spice traders, and energetic street bustle."),
            ("Lakeside Promenade & Boat Jetty", None, "Lakeside", "Tranquil water breezes, rental boats, and waterside cafes."),
            ("Royal Palace Courtyards", None, "Palace Grounds", "Historic royal palace courtyards, ornamental arches, and scenic grounds."),
            ("Highland Panoramic Vista Point", None, "High Ridge", "Spectacular mountain ridge overlook with refreshing breezes and photo spots."),
            ("Local Crafts & Flea Market", None, "Artisan Market", "Handmade souvenirs, jewelry stalls, and friendly local street traders."),
            ("Hidden Emerald Springs & Falls", None, "Secret Spot", "Secluded natural freshwater swimming springs tucked in lush greenery."),
            ("Sculpture Park & Open-Air Theatre", None, "Artistic Hub", "Modern sculpture exhibits, open-air performances, and park benches."),
            ("Old Fisherman Wharf & Lighthouse", None, "Maritime Haven", "Historic coastal wooden piers, salty sea breezes, and fresh seafood stalls."),
            ("Subterranean Historical Crypts", None, "Ancient Crypts", "Underground stone chambers and medieval archeological preservation tours."),
            ("Sunken Gardens & Lotus Basin", None, "Lakeside Oasis", "Peaceful reflection pavilions surrounded by blooming lotus and weeping willows."),
            ("Indie Bookshop Alley & Cafe Row", None, "Literary Quarter", "Secondhand bookstalls, vintage travel zines, and pour-over filter coffee."),
            ("Alpine Foothills Pine Ridge Trail", None, "Highland Trail", "Crisp mountain air, aromatic pine needle trails, and dramatic valley views."),
            ("Bustling Spice Merchant Alleys", None, "Old Bazaar", "Aromatic cinnamon, saffron, and tea vendors in centuries-old stone vaulted arcades."),
            ("Highland Monastery & Bell Tower", None, "Hilltop Sanctuary", "Panoramic spiritual retreat featuring morning prayer bell chimes and tea gardens."),
            ("Riverside Eco-Park & Kayak Pier", None, "Adventure Bank", "Low-cost kayak rentals, scenic river paddling, and green riverside lawns."),
            ("Vintage Tramway Heritage Route", None, "Historic Transit", "Wooden antique streetcars winding through heritage neighborhoods and cafes."),
            ("Astronomical Ridge & Observatory", None, "Star Plateau", "High-altitude clear sky pavilion for night astrophotography and stargazing gatherings."),
            ("Cliffside Fortress & Watchtower", None, "Defensive Ridge", "Commanding views of ancient trade routes and royal defensive architecture."),
            ("Riverside Artisan Village & Kilns", None, "Craft Hamlet", "Traditional ceramic potter workshops, stone carvers, and local textile weavers.")
        ]

    # Dynamically scale landmark pool with duration
    if days <= 7:
        target_count = min(max(days + 2, 5), len(raw_pool))
    elif days <= 15:
        target_count = min(max(days + 2, 14), len(raw_pool))
    elif days <= 30:
        target_count = min(max(days + 2, 28), len(raw_pool))
    elif days <= 60:
        target_count = min(max(int(days * 0.8) + 2, 45), len(raw_pool))
    else:
        target_count = min(max(int(days * 0.75) + 3, 65), len(raw_pool))
    chosen_lms = raw_pool[:target_count]

    lm_names = [re.sub(r'[\r\n,]+', '', item[0]).strip() for item in chosen_lms]
    if must_visit:
        mv_clean = re.sub(r'[\r\n,]+', '', must_visit).strip()
        if mv_clean and mv_clean not in lm_names:
            lm_names.insert(0, mv_clean)

    if not dest_phases:
        clean_city = destination.split(",")[0].strip()
        dest_phases = [
            (f"Phase 1: Historic Core & Iconic Landmarks", f"{clean_city} Old Town", f"Explore iconic central plazas, historic monuments, and orientation walking trails in {clean_city}."),
            (f"Phase 2: Cultural Districts & Artisan Food Alleys", f"{clean_city} Cultural Quarter", "Immerse in local neighborhoods, vibrant street markets, and authentic regional culinary spots."),
            (f"Phase 3: Panoramic Ridges & Waterfront Sanctuaries", "Scenic Vistas", "Hike scenic viewpoint trails, relax along tranquil waterside promenades, and explore lush parks."),
            (f"Phase 4: Surrounding Valleys & Countryside Citadels", "Regional Excursions", "Explore surrounding countryside, historic valleys, ancient ruins, and heritage villages."),
            (f"Phase 5: Off-the-Beaten-Path Secrets & Farewell Celebrations", "Hidden Gems", "Discover hidden viewpoints, quiet artisan cafes, and celebrate the journey's finale.")
        ]

    # Structure into thematic phases based on trip duration
    if days >= 30:
        num_phases = min(5, len(dest_phases))
    elif days >= 18:
        num_phases = min(4, len(dest_phases))
    elif days >= 10:
        num_phases = min(3, len(dest_phases))
    elif days >= 5:
        num_phases = min(2, len(dest_phases))
    else:
        num_phases = 1

    phase_len = max(1, days // num_phases)
    pool_size = max(1, len(chosen_lms) // num_phases)

    if student_mode:
        doc_header = f"# 🌍 {days}-Day Grand Explorer: {destination} — {title}"
        budget_header = f"## 💰 Estimated Student Budget Breakdown ({curr})"
        savings_tip_line = f"- 💡 **Region-Specific Student Savings Tip:** {savings_hack}"
        tips_header = f"## 🎒 Essential Student Tips for {destination}"
        transit_tip_line = f"- 🛵 **Local Transit:** {transit_hack}"
        discount_tip_line = "- 💳 **Student Discounts:** Flash your student ID at transit ticketing booths and heritage sites for instant concessions."
        stay_tip_line = "- 🛡️ **Safety & Social:** Stay in highly-rated youth hostels with social common areas to meet fellow backpackers and share rides/costs."
    else:
        doc_header = f"# 🌍 {days}-Day Curated Journey: {destination} — {title}"
        budget_header = f"## 💰 Estimated Travel Budget Breakdown ({curr})"
        savings_tip_line = f"- 💡 **Curated Traveler Secret:** {savings_hack}"
        tips_header = f"## 🗺️ Essential Travel Tips & Guidance for {destination}"
        transit_tip_line = f"- 🚆 **Local Transit:** {transit_hack}"
        discount_tip_line = "- 💳 **Smart Booking & Payments:** Contactless cards and mobile payments are standard; carry minor local cash for artisan street vendors."
        stay_tip_line = "- 🛡️ **Safety & Comfort:** Reserve central boutique hotels or premium guesthouses with concierge support."

    lines = [
        doc_header,
        "",
        budget_header,
        f"- 🏨 **Accommodation ({accom_style}):** ~{base_stay:,} {curr} / night (~{total_stay:,} {curr} total for {days} days)",
        f"- 🍜 **Food & Regional Dining:** ~{base_food:,} {curr} / day (~{total_food:,} {curr} total)",
        f"- 🚇 **Local Transport:** ~{base_trans:,} {curr} / day (~{total_trans:,} {curr} total)",
        f"- 🎟️ **Activities & Sightseeing:** ~{base_act:,} {curr} / day (~{total_act:,} {curr} total)",
        f"- 💡 **Estimated Total:** **~{est_total:,} {curr}** ({budget_level} Tier for {region_info})",
        savings_tip_line,
        "",
        f"## 🗓️ Day-by-Day Itinerary ({pace} Pace)",
        ""
    ]

    evening_vibes = [
        "Hike up to a scenic ridge viewpoint for an unforgettable golden-hour sunset over the horizon, followed by relaxing at a rooftop cafe.",
        "Stroll through the bustling night market square, pick up fresh local dried fruits and pastries, and enjoy acoustic music sessions.",
        "Unwind under crystal-clear night skies. Join a rooftop stargazing session or telescope gathering spotting constellations.",
        "Gather around a warm communal hearth with fellow travelers, sharing trekking stories and route advice over hot local tea.",
        "Quiet evening stroll along serene water promenades and historic stone alleys, soaking in centuries of cultural heritage and street lamps."
    ]

    student_hacks = [
        "Take shared local transit or split a shared cab from the main stand for a fraction of private taxi rates. Keep local small change handy for vendors.",
        "Carry a refillable water bottle and flash your student ID card at ticket counters for instant 30% to 50% concession discounts.",
        "Check local transit timetables with your hostel reception the night before to catch early morning departures and beat tour crowds.",
        "Eat where local university students eat; follow the crowds to backstreet family-run kitchens for 50% cheaper authentic regional meals.",
        "Recharge all power banks and download offline map data; cellular reception can drop in remote mountain and rural valleys."
    ]

    pro_hacks = [
        "Reserve priority entry time-slots online 48 hours in advance to bypass general admission ticketing queues.",
        "Hire a certified local heritage docent at the ticket pavilion for deep cultural context and hidden architectural details.",
        "Ask your hotel concierge for trusted private vehicle hire recommendations for full-day circuit excursions.",
        "Book dinner reservations at least 24 hours in advance at celebrated heritage restaurants for scenic terrace seating.",
        "Download offline map navigation and regional audio guide tracks before departing your accommodation each morning."
    ]

    for d in range(1, days + 1):
        if num_phases > 1:
            p_idx = min((d - 1) // phase_len, num_phases - 1)
            p_title, p_zone, p_desc = dest_phases[p_idx]

            if d == 1 or (d - 1) % phase_len == 0:
                phase_start = p_idx * phase_len + 1
                phase_end = min((p_idx + 1) * phase_len, days)
                lines.append(f"### 📍 {p_title} (Days {phase_start}–{phase_end})")
                lines.append(f"*{p_desc}*")
                lines.append("")

            phase_pool = chosen_lms[p_idx * pool_size : (p_idx + 1) * pool_size]
            if not phase_pool:
                phase_pool = chosen_lms
            lm = phase_pool[(d - 1) % len(phase_pool)]
        else:
            lm = chosen_lms[(d - 1) % len(chosen_lms)]

        lm_name, coords, zone, desc = lm
        dish = dishes[(d - 1) % len(dishes)]
        eve = evening_vibes[(d - 1) % len(evening_vibes)]

        if student_mode:
            hack = student_hacks[(d - 1) % len(student_hacks)]
            hack_label = "Student Insider Hack"
            m_concession = "Flash your student ID card at the entry gate for 30% to 50% concession tickets." if d % 2 == 0 else "Arrive early around 8:00 AM for stunning golden morning light and zero tourist crowds."
        else:
            hack = pro_hacks[(d - 1) % len(pro_hacks)]
            hack_label = "Traveler Pro Tip"
            m_concession = "Pre-book skip-the-line admissions online for effortless entry." if d % 2 == 0 else "Arrive early around 8:30 AM for serene morning light and unhurried photography."

        if must_visit and d == 1:
            desc = f"Dedicated priority visit to **{must_visit}** — explore signature sights, snap iconic photos, and take in the atmosphere."

        lines.append(f"#### Day {d}: {lm_name} ({zone})")
        lines.append(f"- ☀️ **Morning Exploration:** {desc} {m_concession} Spend 2.5 hours exploring the inner halls, panoramic viewpoints, and photography spots.")
        lines.append(f"- 🌤️ **Afternoon Local Vibe & Eatery:** Head down to a celebrated local kitchen in {zone}. Savor authentic **{dish}** and explore surrounding artisan handicraft lanes.")
        lines.append(f"- 🌙 **Evening Social & Sunset:** {eve}")
        lines.append(f"- 💡 **{hack_label}:** {hack}")
        lines.append(f"- 💰 **Daily Target Budget:** ~{base_stay + base_food + base_trans:,} {curr} (Stay: ~{base_stay:,} {curr} • Food: ~{base_food:,} {curr} • Transit: ~{base_trans:,} {curr})")
        lines.append("")

    lines.append(tips_header)
    lines.append(transit_tip_line)
    lines.append(discount_tip_line)
    lines.append(stay_tip_line)
    lines.append("")
    lines.append(f"LANDMARKS: {' | '.join(lm_names)}")

    return "\n".join(lines)

@app.get("/api/health")
def health_check():
    return {
        "status": "ok",
        "service": "RoamAI FastAPI Backend",
        "version": "2.3.0",
        "models": ["llama-3.1-8b-instant", "llama3-70b-8192", "llama3-8b-8192", "llama-3.2-3b-preview"]
    }

@app.post("/api/generate")
def generate_itinerary(req: TripRequest):
    # Sanitize inputs
    destination_clean = sanitize_str(req.destination, 100)
    if not destination_clean:
        raise HTTPException(status_code=400, detail="Invalid destination provided.")

    must_visit_clean = sanitize_str(req.must_visit, 100)
    budget_amount_clean = sanitize_str(req.budget_amount, 30)
    curr = sanitize_str(req.currency, 10) or "USD"
    region_info = sanitize_str(req.region, 50) or "Global"
    budget_level_clean = sanitize_str(req.budget_level, 40) or "Student (Low)"
    pace_clean = sanitize_str(req.travel_pace, 30) or "Balanced"
    accom_clean = sanitize_str(req.accommodation_style, 40) or "Hostel"

    sanitized_interests = [sanitize_str(i, 40) for i in req.interests if i][:15]
    interests_string = ", ".join(sanitized_interests) if sanitized_interests else "Local street food, culture, secret budget spots"

    if req.days <= 7:
        target_lm_count = max(req.days + 1, 5)
    elif req.days <= 15:
        target_lm_count = min(req.days + 2, 16)
    elif req.days <= 30:
        target_lm_count = min(req.days + 2, 30)
    elif req.days <= 60:
        target_lm_count = min(int(req.days * 0.8) + 2, 48)
    else:
        target_lm_count = min(int(req.days * 0.75) + 3, 65)

    is_student = bool(req.student_mode if req.student_mode is not None else True)
    api_key = os.environ.get("GROQ_API_KEY")
    response_text = None

    if api_key:
        try:
            client = Groq(api_key=api_key)

            budget_text = f"{budget_level_clean} Tier ({curr}) for {region_info} traveler"
            if budget_amount_clean:
                budget_text += f" with strict limit of {budget_amount_clean} {curr}"

            must_visit_instruction = ""
            if must_visit_clean:
                must_visit_instruction = f"CRITICAL: You MUST feature a dedicated visit to '{must_visit_clean}' in the itinerary."

            pace_text = f"Pace: {pace_clean}. Accommodation: {accom_clean}."

            if is_student:
                persona_text = "You are an award-winning local travel architect specializing in epic, student-friendly, budget adventures."
                budget_hdr = f"## 💰 Estimated Student Budget Breakdown ({curr})"
                savings_hdr = f"- 💡 **Region-Specific Student Savings Tip:** [1 high-impact money-saving hack tailored for students]"
                tips_hdr = f"## 🎒 Essential Student Tips for {destination_clean}"
            else:
                persona_text = "You are an award-winning travel architect and cultural concierge specializing in refined, curated, immersive travel journeys."
                budget_hdr = f"## 💰 Estimated Travel Budget Breakdown ({curr})"
                savings_hdr = f"- 💡 **Curated Traveler Tip:** [1 high-impact local secret or priority booking tip for travelers]"
                tips_hdr = f"## 🗺️ Essential Travel Tips & Guidance for {destination_clean}"

            prompt = f"""
            {persona_text}
            Create a detailed {req.days}-day trip itinerary to {destination_clean}.

            Travel Parameters:
            - Destination: {destination_clean}
            - Duration: {req.days} Days
            - Traveler Region/Currency: {region_info} ({curr})
            - Budget Level: {budget_text}
            - Specific Interests: {interests_string}
            - {pace_text}
            - {must_visit_instruction}

            CRITICAL DURATION & LANDMARK RULES:
            - For a {req.days}-day trip, do NOT keep the visited places the same as a short trip. Scale the places to visit realistically across the entire region.
            - Provide a comprehensive, non-repetitive Day-by-Day itinerary that covers different neighborhoods, zones, day trips, and hidden gems.
            - At the very end of your response, list at least {target_lm_count} real, specific places/landmarks visited in this itinerary, separated by pipe symbols | on a single line starting with LANDMARKS:.

            Structure your response strictly in clean Markdown as follows:
            # 🌍 [Catchy Trip Title & Emoji]

            {budget_hdr}
            - 🏨 **Accommodation ({accom_clean}):** [Estimated cost per night & total in {curr}]
            - 🍜 **Food & Dining:** [Daily & total food estimate in {curr}]
            - 🚇 **Local Transport:** [Passes/Transit estimates in {curr}]
            - 🎟️ **Activities & Entry Fees:** [Cost estimates for attractions in {curr}]
            {savings_hdr}

            ## 🗓️ Day-by-Day Itinerary

            ### Day 1: [Day 1 Theme & Specific Area/Landmark]
            - ☀️ **Morning:** [Actionable morning activity at a specific location]
            - 🌤️ **Afternoon:** [Actionable afternoon activity + authentic food spot recommendation]
            - 🌙 **Evening:** [Evening vibes, sunset spot, or social spots]

            (Continue detailed ### Day X format for all {req.days} days, exploring new areas and landmarks)

            {tips_hdr}
            - 3 practical tips for safety, local transit apps, SIM cards, or local booking advice.

            LANDMARKS: Place 1 | Place 2 | Place 3 | ... (list at least {target_lm_count} real places separated by |)
            """

            models_to_try = [
                "llama-3.3-70b-versatile",
                "llama-3.1-8b-instant",
                "llama3-70b-8192",
                "gemma2-9b-it"
            ]

            for model_name in models_to_try:
                try:
                    completion = client.chat.completions.create(
                        messages=[{"role": "user", "content": prompt}],
                        model=model_name,
                    )
                    response_text = completion.choices[0].message.content
                    if response_text and len(response_text.strip()) > 50:
                        break
                except Exception:
                    continue
        except Exception:
            pass

    # Seamless Intelligent Fallback if API key is missing, rate-limited, or Groq is unavailable
    if not response_text:
        response_text = generate_fallback_itinerary(
            destination=destination_clean,
            days=req.days,
            curr=curr,
            region_info=region_info,
            budget_level=budget_level_clean,
            accom_style=accom_clean,
            interests=sanitized_interests,
            must_visit=must_visit_clean,
            pace=pace_clean,
            student_mode=is_student
        )

    raw_landmarks = []
    if "LANDMARKS:" in response_text:
        parts = response_text.split("LANDMARKS:")
        itinerary = parts[0].strip()
        lm_str = parts[1].strip()
        if "|" in lm_str:
            tokens = lm_str.split("|")
        else:
            tokens = lm_str.split(",")
        raw_landmarks = [re.sub(r'[\r\n]+', '', l).strip().rstrip('.') for l in tokens if l.strip()][:target_lm_count]
    else:
        itinerary = response_text.strip()
        raw_landmarks = [destination_clean]

    dest_coords = get_coordinates(destination_clean)
    markers = []

    if dest_coords:
        markers.append({
            "name": f"Destination: {destination_clean}",
            "type": "destination",
            "coords": dest_coords
        })

    mv_coords = None
    if must_visit_clean:
        mv_coords = get_coordinates(must_visit_clean, destination_clean)
        if mv_coords:
            markers.append({
                "name": f"Must Visit: {must_visit_clean}",
                "type": "must_visit",
                "coords": mv_coords
            })

    placed_coords = []
    if dest_coords:
        placed_coords.append(dest_coords)
    if mv_coords:
        placed_coords.append(mv_coords)

    def is_too_close(c1, c2, threshold=0.0035):
        return abs(c1[0] - c2[0]) < threshold and abs(c1[1] - c2[1]) < threshold

    for idx, landmark in enumerate(raw_landmarks):
        l_coords = get_coordinates(landmark, destination_clean)
        
        # If coordinates are missing or if it resolved to the generic destination city center,
        # spread it out geographically around the destination using a golden-angle spiral
        need_spread = False
        if not l_coords:
            need_spread = True
        elif dest_coords and is_too_close(l_coords, dest_coords, threshold=0.002):
            need_spread = True

        if need_spread and dest_coords:
            angle = idx * 2.39996323  # Golden angle ~137.5 degrees in radians
            radius = 0.015 + (idx * 0.007)  # Expanding radius from 1.5km to 15km
            cos_lat = max(0.2, math.cos(math.radians(dest_coords[0])))
            lat_offset = radius * math.cos(angle)
            lng_offset = (radius * math.sin(angle)) / cos_lat
            l_coords = [round(dest_coords[0] + lat_offset, 5), round(dest_coords[1] + lng_offset, 5)]

        if l_coords:
            # Prevent collision with any existing marker
            collision_count = 0
            while any(is_too_close(l_coords, p, threshold=0.0035) for p in placed_coords) and collision_count < 16:
                collision_count += 1
                bump_angle = (idx * 1.7 + collision_count * 0.85)
                bump_radius = 0.005 * collision_count
                cos_lat = max(0.2, math.cos(math.radians(l_coords[0])))
                l_coords = [
                    round(l_coords[0] + bump_radius * math.cos(bump_angle), 5),
                    round(l_coords[1] + (bump_radius * math.sin(bump_angle)) / cos_lat, 5)
                ]

            placed_coords.append(l_coords)
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
            "destination": destination_clean,
            "days": req.days,
            "budget_level": budget_level_clean,
            "currency": curr,
            "region": region_info,
            "interests": sanitized_interests,
            "travel_pace": pace_clean,
            "student_mode": is_student
        }
    }

# ========================================================
# 3D MODERN MULTI-PAGE FRONTEND EMBEDDED IN PYTHON
# ========================================================
HTML_CONTENT = r"""<!DOCTYPE html>
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


  <!-- Vercel Web Analytics -->
  <script>
    window.va = window.va || function () { (window.vaq = window.vaq || []).push(arguments); };
  </script>
  <script defer src="https://cdn.vercel-insights.com/v1/script.js"></script>
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

  <!-- Leaflet MarkerCluster for High-Density Multi-Day Pin Grouping -->
  <link rel="stylesheet" href="https://unpkg.com/leaflet.markercluster@1.5.3/dist/MarkerCluster.css" />
  <link rel="stylesheet" href="https://unpkg.com/leaflet.markercluster@1.5.3/dist/MarkerCluster.Default.css" />
  <script src="https://unpkg.com/leaflet.markercluster@1.5.3/dist/leaflet.markercluster.js"></script>

  <!-- Marked.js & DOMPurify (Deferred parser & sanitizer) -->
  <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js" defer></script>
  <script src="https://cdnjs.cloudflare.com/ajax/libs/dompurify/3.0.9/purify.min.js" defer></script>

  <!-- Vanilla Tilt (3D Card Physics - Desktop Only to guarantee 60fps buttery smooth touch on mobile) -->
  <script>
    if (window.innerWidth >= 1024 && !('ontouchstart' in window)) {
      const tiltScript = document.createElement('script');
      tiltScript.src = 'https://cdnjs.cloudflare.com/ajax/libs/vanilla-tilt/1.8.1/vanilla-tilt.min.js';
      tiltScript.defer = true;
      document.head.appendChild(tiltScript);
    }
  </script>

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

    /* Responsive Mobile Layout & Touch Rules (Applied ONLY on Mobile/Tablet <=768px) */
    @media (max-width: 768px) {
      #bgParticleCanvas {
        transform: translate3d(0, 0, 0) !important;
        -webkit-transform: translate3d(0, 0, 0) !important;
        will-change: transform !important;
      }
      .glass-card {
        padding: 1.15rem !important;
        background-color: rgba(18, 24, 38, 0.92) !important;
        backdrop-filter: none !important;
        -webkit-backdrop-filter: none !important;
        transform: translateZ(0) !important;
        -webkit-transform: translateZ(0) !important;
        transition: border-color 0.2s ease !important;
      }
      .light-theme .glass-card {
        background-color: rgba(255, 255, 255, 0.95) !important;
        backdrop-filter: none !important;
        -webkit-backdrop-filter: none !important;
      }
      .glass-card:hover {
        transform: none !important;
      }
      .orb-1, .orb-2, .orb-3 {
        animation: none !important;
        filter: blur(35px) !important;
        opacity: 0.25 !important;
        transform: none !important;
      }
      #map {
        min-height: 300px !important;
      }
      #plannerTopGrids {
        gap: 1rem !important;
      }
      #plannerMapCard {
        min-height: 360px !important;
      }
      .itinerary-prose h1 {
        font-size: 1.35rem !important;
      }
      .itinerary-prose h2 {
        font-size: 1.15rem !important;
      }
    }
    @media (max-width: 480px) {
      .brand-logo-title {
        font-size: 1.05rem !important;
      }
      #heroDestInput {
        padding-left: 0.85rem !important;
        padding-right: 0.85rem !important;
      }
    }
    .no-scrollbar::-webkit-scrollbar {
      display: none !important;
    }
    .no-scrollbar {
      -ms-overflow-style: none !important;
      scrollbar-width: none !important;
    }
    * {
      -webkit-tap-highlight-color: transparent;
    }
    button, a, select, input, .chip-tag, .hotspot-card {
      touch-action: manipulation;
      -webkit-tap-highlight-color: transparent;
      cursor: pointer;
    }

    /* ========== PREMIUM MAP MARKERS & POPUPS ========== */
    /* Dark mode: invert OSM tiles to create sleek dark map look */
    .leaflet-tile-pane {
      filter: invert(1) hue-rotate(180deg) brightness(0.95) contrast(0.9) saturate(0.8);
    }
    .light-theme .leaflet-tile-pane {
      filter: none;
    }
    /* Prevent filter from affecting markers and popups */
    .leaflet-marker-pane,
    .leaflet-popup-pane,
    .leaflet-tooltip-pane,
    .leaflet-shadow-pane {
      filter: none !important;
    }

    @keyframes roamPinDrop {
      0% { opacity: 0; transform: rotate(-45deg) translateY(-30px) scale(0.4); }
      60% { opacity: 1; transform: rotate(-45deg) translateY(4px) scale(1.08); }
      100% { opacity: 1; transform: rotate(-45deg) translateY(0) scale(1); }
    }
    .roam-marker {
      background: transparent !important;
      border: none !important;
    }
    .roam-pin {
      transition: transform 0.2s ease, box-shadow 0.2s ease;
      cursor: pointer;
    }
    .roam-pin:hover {
      transform: rotate(-45deg) scale(1.18) !important;
      filter: brightness(1.15);
    }

    /* Popup container override */
    .roam-popup-container .leaflet-popup-content-wrapper {
      background: rgba(12, 17, 30, 0.92);
      backdrop-filter: blur(16px) saturate(160%);
      -webkit-backdrop-filter: blur(16px) saturate(160%);
      border: 1px solid rgba(255, 255, 255, 0.12);
      border-radius: 16px;
      box-shadow: 0 8px 32px rgba(0, 0, 0, 0.5), 0 0 0 1px rgba(255, 255, 255, 0.06);
      padding: 0;
      color: #fff;
    }
    .roam-popup-container .leaflet-popup-content {
      margin: 0;
      line-height: 1.4;
    }
    .roam-popup-container .leaflet-popup-tip {
      background: rgba(12, 17, 30, 0.92);
      border: 1px solid rgba(255, 255, 255, 0.1);
      box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
    }
    .roam-popup-container .leaflet-popup-close-button {
      color: rgba(255, 255, 255, 0.5) !important;
      font-size: 18px !important;
      top: 8px !important;
      right: 10px !important;
      transition: color 0.2s;
    }
    .roam-popup-container .leaflet-popup-close-button:hover {
      color: #FF6B4A !important;
    }

    /* Popup inner content */
    .roam-popup {
      padding: 14px 16px;
    }
    .roam-popup-badge {
      display: inline-flex;
      align-items: center;
      gap: 5px;
      font-size: 11px;
      font-weight: 700;
      padding: 3px 10px;
      border-radius: 20px;
      text-transform: uppercase;
      letter-spacing: 0.5px;
      margin-bottom: 8px;
    }
    .roam-popup-name {
      font-size: 15px;
      font-weight: 800;
      color: #fff;
      line-height: 1.3;
      margin-bottom: 4px;
    }
    .roam-popup-coords {
      font-size: 11px;
      color: rgba(255, 255, 255, 0.45);
      font-family: 'SF Mono', 'Fira Code', monospace;
      letter-spacing: 0.3px;
    }

    /* Tooltip styling */
    .roam-tooltip {
      background: rgba(12, 17, 30, 0.88) !important;
      backdrop-filter: blur(10px);
      -webkit-backdrop-filter: blur(10px);
      border: 1px solid rgba(255, 255, 255, 0.12) !important;
      border-radius: 10px !important;
      padding: 6px 12px !important;
      font-size: 12px !important;
      font-weight: 700 !important;
      color: #fff !important;
      box-shadow: 0 4px 16px rgba(0, 0, 0, 0.4) !important;
      white-space: nowrap;
    }
    .roam-tooltip::before {
      border-top-color: rgba(12, 17, 30, 0.88) !important;
    }

    /* Leaflet zoom controls styling */
    .leaflet-control-zoom {
      border: 1px solid rgba(255, 255, 255, 0.12) !important;
      border-radius: 12px !important;
      overflow: hidden;
      box-shadow: 0 4px 16px rgba(0, 0, 0, 0.4) !important;
    }
    .leaflet-control-zoom a {
      background: rgba(12, 17, 30, 0.85) !important;
      color: rgba(255, 255, 255, 0.8) !important;
      width: 36px !important;
      height: 36px !important;
      line-height: 36px !important;
      font-size: 18px !important;
      border-bottom: 1px solid rgba(255, 255, 255, 0.08) !important;
      transition: background 0.2s, color 0.2s;
    }
    .leaflet-control-zoom a:hover {
      background: rgba(255, 107, 74, 0.2) !important;
      color: #FF6B4A !important;
    }
    .leaflet-control-zoom a:last-child {
      border-bottom: none !important;
    }

    /* Attribution styling */
    .leaflet-control-attribution {
      background: rgba(12, 17, 30, 0.7) !important;
      color: rgba(255, 255, 255, 0.35) !important;
      font-size: 10px !important;
      padding: 2px 8px !important;
      border-radius: 8px 0 0 0 !important;
    }
    .leaflet-control-attribution a {
      color: rgba(74, 234, 255, 0.5) !important;
    }

    /* --- LIGHT THEME MAP OVERRIDES --- */
    .light-theme .roam-popup-container .leaflet-popup-content-wrapper {
      background: rgba(255, 255, 255, 0.95);
      border-color: rgba(0, 0, 0, 0.08);
      box-shadow: 0 8px 32px rgba(0, 0, 0, 0.12), 0 0 0 1px rgba(0, 0, 0, 0.04);
    }
    .light-theme .roam-popup-container .leaflet-popup-tip {
      background: rgba(255, 255, 255, 0.95);
      border-color: rgba(0, 0, 0, 0.06);
    }
    .light-theme .roam-popup-container .leaflet-popup-close-button {
      color: rgba(0, 0, 0, 0.4) !important;
    }
    .light-theme .roam-popup-name {
      color: #0F172A;
    }
    .light-theme .roam-popup-coords {
      color: rgba(15, 23, 42, 0.45);
    }
    .light-theme .roam-tooltip {
      background: rgba(255, 255, 255, 0.92) !important;
      border-color: rgba(0, 0, 0, 0.1) !important;
      color: #0F172A !important;
      box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1) !important;
    }
    .light-theme .leaflet-control-zoom a {
      background: rgba(255, 255, 255, 0.9) !important;
      color: #334155 !important;
      border-bottom-color: rgba(0, 0, 0, 0.06) !important;
    }
    .light-theme .leaflet-control-zoom a:hover {
      background: rgba(255, 107, 74, 0.1) !important;
      color: #FF6B4A !important;
    }
    .light-theme .leaflet-control-zoom {
      border-color: rgba(0, 0, 0, 0.1) !important;
      box-shadow: 0 4px 16px rgba(0, 0, 0, 0.08) !important;
    }
    .light-theme .leaflet-control-attribution {
      background: rgba(255, 255, 255, 0.7) !important;
      color: rgba(0, 0, 0, 0.35) !important;
    }

    /* Map legend overlay */
    .roam-map-legend {
      position: absolute;
      bottom: 12px;
      left: 12px;
      z-index: 1000;
      background: rgba(12, 17, 30, 0.85);
      backdrop-filter: blur(12px);
      -webkit-backdrop-filter: blur(12px);
      border: 1px solid rgba(255, 255, 255, 0.1);
      border-radius: 12px;
      padding: 8px 12px;
      display: flex;
      gap: 10px;
      font-size: 11px;
      font-weight: 600;
      color: rgba(255, 255, 255, 0.75);
    }
    .roam-map-legend .legend-dot {
      width: 10px;
      height: 10px;
      border-radius: 50%;
      display: inline-block;
      margin-right: 4px;
      vertical-align: middle;
      box-shadow: 0 0 6px currentColor;
    }
    .light-theme .roam-map-legend {
      background: rgba(255, 255, 255, 0.88);
      border-color: rgba(0, 0, 0, 0.08);
      color: #334155;
    }

    /* Leaflet MarkerCluster custom sleek styling */
    .roam-cluster-container {
      background: transparent !important;
      border: none !important;
    }
    .roam-cluster-badge {
      width: 40px;
      height: 40px;
      border-radius: 50%;
      background: linear-gradient(135deg, #06B6D4, #3B82F6);
      border: 2.5px solid rgba(255, 255, 255, 0.95);
      box-shadow: 0 0 16px rgba(6, 182, 212, 0.65), 0 4px 12px rgba(0, 0, 0, 0.45);
      display: flex;
      align-items: center;
      justify-content: center;
      color: #ffffff;
      font-weight: 800;
      font-size: 13px;
      cursor: pointer;
      transition: all 0.25s cubic-bezier(0.34, 1.56, 0.64, 1);
    }
    .roam-cluster-badge:hover {
      transform: scale(1.15);
      box-shadow: 0 0 22px rgba(6, 182, 212, 0.9), 0 6px 16px rgba(0, 0, 0, 0.6);
    }


    /* ========================================================
       MODERN SEARCH BAR, ITINERARY CONTROLS & SMOOTH ACCORDIONS
       ======================================================== */
    .day-card {
      transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
      border: 1px solid rgba(255, 255, 255, 0.08);
      background: rgba(15, 23, 42, 0.65);
      border-radius: 1rem;
    }
    .light-theme .day-card {
      border: 1px solid #E2E8F0;
      background: #FFFFFF;
      box-shadow: 0 2px 8px rgba(0, 0, 0, 0.03);
    }
    .day-card:hover {
      border-color: rgba(255, 107, 74, 0.4);
      background: rgba(18, 28, 50, 0.85);
      box-shadow: 0 8px 24px -6px rgba(255, 107, 74, 0.15);
      transform: translateY(-1px);
    }
    .light-theme .day-card:hover {
      border-color: rgba(255, 107, 74, 0.45);
      background: #FFFFFF;
      box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.07);
      transform: translateY(-1px);
    }

    .day-card-body {
      overflow: hidden;
      transition: max-height 0.35s cubic-bezier(0.16, 1, 0.3, 1), opacity 0.25s ease, padding 0.3s ease;
      max-height: 1200px;
      opacity: 1;
      transform: translateZ(0);
    }
    .day-card-body.collapsed {
      max-height: 0 !important;
      opacity: 0 !important;
      padding-top: 0 !important;
      padding-bottom: 0 !important;
      margin-top: 0 !important;
      border-top-color: transparent !important;
      pointer-events: none;
    }

    .chevron-icon {
      display: inline-block;
      transition: transform 0.3s cubic-bezier(0.16, 1, 0.3, 1);
    }

    /* Itinerary Toolbar in Dark Mode */
    #itineraryCardsToolbar {
      background: rgba(15, 23, 42, 0.75);
      border: 1px solid rgba(255, 255, 255, 0.10);
      backdrop-filter: blur(12px);
      -webkit-backdrop-filter: blur(12px);
    }

    #itinerarySearchInput {
      background: rgba(11, 17, 30, 0.85);
      border: 1px solid rgba(255, 255, 255, 0.12);
      color: #F8FAFC;
    }
    #itinerarySearchInput::placeholder {
      color: #94A3B8;
    }
    #itinerarySearchInput:focus {
      background: rgba(11, 17, 30, 0.95);
      border-color: #FF6B4A;
      box-shadow: 0 0 0 3px rgba(255, 107, 74, 0.25);
    }

    /* Itinerary Toolbar in Light Theme */
    .light-theme #itineraryCardsToolbar {
      background: #FFFFFF !important;
      border: 1px solid #E2E8F0 !important;
      box-shadow: 0 4px 18px rgba(0, 0, 0, 0.04) !important;
    }

    .light-theme #itinerarySearchInput {
      background: #F8FAFC !important;
      border: 1.5px solid #CBD5E1 !important;
      color: #0F172A !important;
      box-shadow: inset 0 1px 2px rgba(0, 0, 0, 0.03) !important;
    }
    .light-theme #itinerarySearchInput::placeholder {
      color: #94A3B8 !important;
    }
    .light-theme #itinerarySearchInput:focus {
      background: #FFFFFF !important;
      border-color: #FF5E36 !important;
      box-shadow: 0 0 0 3px rgba(255, 94, 54, 0.18) !important;
    }

    .light-theme #itinerarySearchClear {
      color: #64748B !important;
    }
    .light-theme #itinerarySearchClear:hover {
      color: #0F172A !important;
    }

    .light-theme #itineraryCardsCountBadge {
      background: #F1F5F9 !important;
      border: 1px solid #E2E8F0 !important;
      color: #475569 !important;
    }

    .light-theme #itineraryCardsToolbar button {
      background: #FFFFFF !important;
      border: 1.5px solid #CBD5E1 !important;
      color: #1E293B !important;
      box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04) !important;
    }
    .light-theme #itineraryCardsToolbar button:hover {
      background: #F8FAFC !important;
      border-color: #94A3B8 !important;
      color: #0F172A !important;
    }

    .light-theme .phase-divider-header {
      border-bottom-color: #E2E8F0 !important;
    }

    .light-theme .phase-pill-btn {
      background: #F1F5F9 !important;
      border: 1.5px solid #CBD5E1 !important;
      color: #334155 !important;
    }
    .light-theme .phase-pill-btn:hover {
      background: #E2E8F0 !important;
      color: #0F172A !important;
    }
    .light-theme .phase-pill-btn.active {
      background: linear-gradient(135deg, #FF5E36, #FFA000) !important;
      border-color: transparent !important;
      color: #FFFFFF !important;
      box-shadow: 0 4px 12px rgba(255, 94, 54, 0.3) !important;
    }

    /* Tip Boxes Light Theme High-Contrast Polish */
    .light-theme .tip-box-student {
      background: #FFFBEB !important;
      border: 1.5px solid #FDE68A !important;
      color: #92400E !important;
    }
    .light-theme .tip-box-student strong {
      color: #B45309 !important;
    }
    .light-theme .tip-box-student span {
      color: #78350F !important;
    }

    .light-theme .tip-box-traveler {
      background: #F0F9FF !important;
      border: 1.5px solid #BAE6FD !important;
      color: #0369A1 !important;
    }
    .light-theme .tip-box-traveler strong {
      color: #0284C7 !important;
    }
    .light-theme .tip-box-traveler span {
      color: #0C4A6E !important;
    }

    /* Interactive Day Cards Styling */
    .day-card {
      transition: all 0.25s cubic-bezier(0.2, 0, 0, 1);
      border: 1px solid rgba(255, 255, 255, 0.08);
      background: rgba(15, 23, 42, 0.65);
    }
    .light-theme .day-card {
      border: 1px solid rgba(0, 0, 0, 0.08);
      background: rgba(255, 255, 255, 0.85);
    }
    .day-card:hover {
      border-color: rgba(6, 182, 212, 0.4);
      background: rgba(18, 28, 50, 0.8);
      box-shadow: 0 8px 24px -6px rgba(6, 182, 212, 0.15);
    }
    .light-theme .day-card:hover {
      border-color: rgba(6, 182, 212, 0.4);
      background: rgba(255, 255, 255, 0.98);
      box-shadow: 0 8px 24px -6px rgba(0, 0, 0, 0.08);
    }
    .day-card-highlight {
      animation: dayPulseHighlight 2s ease-in-out;
      border-color: #06B6D4 !important;
      box-shadow: 0 0 25px rgba(6, 182, 212, 0.5) !important;
    }
    @keyframes dayPulseHighlight {
      0%, 100% { transform: scale(1); }
      50% { transform: scale(1.02); }
    }
    .phase-pill-btn {
      transition: all 0.2s ease;
      white-space: nowrap;
    }
    .phase-pill-btn.active {
      background: linear-gradient(135deg, #06B6D4, #3B82F6) !important;
      color: #ffffff !important;
      border-color: rgba(255, 255, 255, 0.4) !important;
      box-shadow: 0 0 12px rgba(6, 182, 212, 0.4) !important;
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
    .light-theme .btn-gradient,
    .light-theme .btn-gradient * {
      color: #FFFFFF !important;
    }
    .light-theme .image-badge-dark {
      background-color: rgba(11, 15, 25, 0.82) !important;
      border-color: rgba(255, 255, 255, 0.20) !important;
      color: #FFFFFF !important;
    }
    .light-theme .image-badge-dark * {
      color: #FFFFFF !important;
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
    #mobileBottomNav {
      background-color: rgba(14, 20, 32, 0.95) !important;
      border-top: 1px solid rgba(255, 255, 255, 0.08) !important;
      backdrop-filter: blur(20px);
      -webkit-backdrop-filter: blur(20px);
      box-shadow: 0 -4px 25px rgba(0, 0, 0, 0.4);
    }
    .light-theme #mobileBottomNav {
      background-color: rgba(255, 255, 255, 0.95) !important;
      border-top: 1px solid rgba(203, 213, 225, 0.8) !important;
      box-shadow: 0 -4px 25px rgba(11, 19, 43, 0.08) !important;
    }
    #mobileBottomNav button {
      color: #9CA3AF;
      transition: all 0.2s ease;
      border-radius: 0.75rem;
    }
    #mobileBottomNav button.active-mob-tab {
      color: #FF5E36 !important;
      font-weight: 800 !important;
      background-color: rgba(255, 255, 255, 0.08);
    }
    .light-theme #mobileBottomNav button {
      color: #64748B !important;
    }
    .light-theme #mobileBottomNav button.active-mob-tab {
      color: #FF5E36 !important;
      font-weight: 800 !important;
      background-color: rgba(255, 94, 54, 0.12) !important;
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
  
    /* ========================================================
       MASTER-GRADE ULTRA-SMOOTH ANIMATIONS & 60/120FPS TRANSITIONS
       ======================================================== */
    html {
      scroll-behavior: smooth !important;
      -webkit-overflow-scrolling: touch;
    }
    
    *, *::before, *::after {
      -webkit-tap-highlight-color: transparent;
    }

    /* Page Smooth Entrance Transition */
    @keyframes pageFadeSlideUp {
      0% {
        opacity: 0;
        transform: translateY(14px) translateZ(0);
      }
      100% {
        opacity: 1;
        transform: translateY(0) translateZ(0);
      }
    }

    .page-enter {
      animation: pageFadeSlideUp 0.35s cubic-bezier(0.16, 1, 0.3, 1) forwards;
      will-change: transform, opacity;
    }

    /* Universal Hardware-Accelerated Micro-Interactions */
    .btn-gradient,
    .btn-secondary,
    .chip-tag,
    .nav-tab,
    .phase-pill-btn,
    .hotspot-scope-btn,
    .hotspot-filter-btn {
      transition: transform 0.25s cubic-bezier(0.16, 1, 0.3, 1), background 0.25s ease, border-color 0.25s ease, box-shadow 0.25s cubic-bezier(0.16, 1, 0.3, 1), color 0.2s ease !important;
      will-change: transform, box-shadow;
      transform: translateZ(0);
    }
    .btn-gradient:hover,
    .btn-secondary:hover {
      transform: translateY(-2px) translateZ(0);
    }
    .btn-gradient:active,
    .btn-secondary:active,
    .chip-tag:active,
    button:active {
      transform: scale(0.96) translateZ(0) !important;
    }

    /* Glass Cards & Hotspots Smooth Elevation */
    .glass-card {
      transition: transform 0.35s cubic-bezier(0.16, 1, 0.3, 1), box-shadow 0.35s cubic-bezier(0.16, 1, 0.3, 1), border-color 0.25s ease, background 0.35s ease !important;
      will-change: transform, box-shadow;
      transform: translateZ(0);
    }
    .glass-card:hover {
      transform: translateY(-4px) translateZ(0);
    }

    .hotspot-card {
      transition: transform 0.35s cubic-bezier(0.16, 1, 0.3, 1), box-shadow 0.35s cubic-bezier(0.16, 1, 0.3, 1), border-color 0.25s ease !important;
      will-change: transform, box-shadow;
      transform: translateZ(0);
    }
    .hotspot-card:hover {
      transform: translateY(-6px) translateZ(0);
    }

    /* Range Sliders Smooth Physics */
    input[type="range"] {
      -webkit-appearance: none;
      appearance: none;
      background: rgba(255, 255, 255, 0.12);
      border-radius: 9999px;
      height: 6px;
      outline: none;
      transition: background-color 0.25s ease;
    }
    .light-theme input[type="range"] {
      background: #CBD5E1;
    }
    input[type="range"]::-webkit-slider-thumb {
      -webkit-appearance: none;
      appearance: none;
      width: 18px;
      height: 18px;
      border-radius: 50%;
      background: #FF6B4A;
      cursor: pointer;
      box-shadow: 0 0 10px rgba(255, 107, 74, 0.4);
      transition: transform 0.18s cubic-bezier(0.16, 1, 0.3, 1), box-shadow 0.18s ease;
      will-change: transform;
    }
    input[type="range"]::-webkit-slider-thumb:hover {
      transform: scale(1.25);
      box-shadow: 0 0 16px rgba(255, 107, 74, 0.7);
    }
    input[type="range"]::-webkit-slider-thumb:active {
      transform: scale(0.95);
    }

    /* Form Inputs Smooth Focus Ring */
    input, select {
      transition: border-color 0.25s cubic-bezier(0.16, 1, 0.3, 1), box-shadow 0.25s cubic-bezier(0.16, 1, 0.3, 1), background-color 0.25s ease, color 0.2s ease !important;
    }

    /* Modal Backdrop & Pop Animation */
    #confirmModalBackdrop {
      transition: opacity 0.25s ease, backdrop-filter 0.25s ease;
    }
    #confirmModalCard {
      transition: transform 0.35s cubic-bezier(0.34, 1.56, 0.64, 1), opacity 0.25s ease !important;
      will-change: transform, opacity;
    }

    /* Mobile Bottom Navigation Smooth Active Physics */
    #mobileBottomNav button {
      transition: transform 0.2s cubic-bezier(0.16, 1, 0.3, 1), color 0.2s ease !important;
    }
    #mobileBottomNav button:active {
      transform: scale(0.9);
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
    <div class="max-w-7xl mx-auto px-3 sm:px-6 lg:px-8 h-16 sm:h-20 flex items-center justify-between gap-1.5 sm:gap-4">
      
      <!-- Brand Logo (Left) -->
      <div class="flex items-center gap-2 sm:gap-3 cursor-pointer shrink-0" onclick="switchPage('home')">
        <div class="flex items-center justify-center w-8 h-8 sm:w-11 sm:h-11 rounded-xl sm:rounded-2xl bg-gradient-to-br from-coralPrimary to-amberAccent p-0.5 shadow-lg shadow-coralPrimary/30 shrink-0">
          <div class="w-full h-full bg-spaceDark rounded-[9px] sm:rounded-[14px] flex items-center justify-center">
            <span class="text-base sm:text-2xl">✈️</span>
          </div>
        </div>
        <div class="flex items-center gap-1.5">
          <span class="text-lg sm:text-xl font-extrabold tracking-tight brand-logo-title">RoamAI</span>
          <span class="hidden sm:inline-block text-[9px] sm:text-[10px] font-bold tracking-widest px-1.5 py-0.5 rounded-full bg-coralPrimary/20 text-coralPrimary border border-coralPrimary/30 uppercase">Student</span>
        </div>
      </div>

      <!-- Navigation Tabs (Center - Desktop) -->
      <nav class="hidden lg:flex items-center gap-7 text-sm font-medium text-gray-300">
        <button onclick="switchPage('home')" id="tab-home" class="nav-tab active hover:text-white flex items-center gap-1.5 transition"><span>🌟</span> Discover</button>
        <button onclick="switchPage('planner')" id="tab-planner" class="nav-tab hover:text-white flex items-center gap-1.5 transition"><span>🚀</span> AI Planner</button>
        <button onclick="switchPage('budget')" id="tab-budget" class="nav-tab hover:text-white flex items-center gap-1.5 transition"><span>💰</span> Budget Calc</button>
        <button onclick="switchPage('packing')" id="tab-packing" class="nav-tab hover:text-white flex items-center gap-1.5 transition"><span>🎒</span> Packing List</button>
        <button onclick="switchPage('saved')" id="tab-saved" class="nav-tab hover:text-white flex items-center gap-1.5 transition"><span>📂</span> Saved (<span id="savedCount">0</span>)</button>
      </nav>

      <!-- Theme Switcher, Region Selector & CTA (Right) -->
      <div class="flex items-center gap-1.5 sm:gap-2.5 shrink-0">
        
        <!-- Theme Mood Switcher (Dark / Light) -->
        <button
          id="themeToggleBtn"
          onclick="toggleThemeMood()"
          class="w-8 h-8 sm:w-9 sm:h-9 rounded-xl bg-cardDark/90 border border-white/15 hover:border-coralPrimary/50 flex items-center justify-center text-xs sm:text-sm text-gray-300 hover:text-white transition shadow-sm shrink-0"
          title="Toggle Light / Dark Mode"
          aria-label="Toggle Theme Mood"
        >
          <span id="themeToggleIcon" class="theme-icon inline-block"></span>
        </button>

        <!-- Region & Currency Selector -->
        <div class="relative flex items-center shrink-0">
          <span class="absolute left-2 text-xs sm:text-sm pointer-events-none" id="navRegionFlag">🇮🇳</span>
          <select
            id="navRegionSelector"
            onchange="onRegionChange(this.value)"
            class="pl-6 sm:pl-8 pr-5 sm:pr-7 py-1.5 sm:py-2 max-w-[82px] xs:max-w-[100px] sm:max-w-none truncate bg-cardDark/90 border border-white/15 hover:border-coralPrimary/50 rounded-xl text-[10px] sm:text-xs font-semibold text-white focus:outline-none focus:border-coralPrimary cursor-pointer shadow-sm transition"
          >
            <option value="INR" data-flag="🇮🇳" data-curr="INR" data-sym="₹" data-name="India" selected>🇮🇳 INR ₹</option>
            <option value="USD" data-flag="🇺🇸" data-curr="USD" data-sym="$" data-name="United States">🇺🇸 USD $</option>
            <option value="EUR" data-flag="🇪🇺" data-curr="EUR" data-sym="€" data-name="Europe">🇪🇺 EUR €</option>
            <option value="GBP" data-flag="🇬🇧" data-curr="GBP" data-sym="£" data-name="United Kingdom">🇬🇧 GBP £</option>
            <option value="JPY" data-flag="🇯🇵" data-curr="JPY" data-sym="¥" data-name="Japan">🇯🇵 JPY ¥</option>
            <option value="AUD" data-flag="🇦🇺" data-curr="AUD" data-sym="A$" data-name="Australia">🇦🇺 AUD A$</option>
            <option value="CAD" data-flag="🇨🇦" data-curr="CAD" data-sym="C$" data-name="Canada">🇨🇦 CAD C$</option>
            <option value="AED" data-flag="🇦🇪" data-curr="AED" data-sym="AED" data-name="UAE">🇦🇪 AED</option>
            <option value="THB" data-flag="🇹🇭" data-curr="THB" data-sym="฿" data-name="Thailand">🇹🇭 THB ฿</option>
          </select>
        </div>

        <!-- Plan Button -->
        <button onclick="switchPage('planner')" class="hidden xs:flex btn-gradient text-[11px] sm:text-sm px-2.5 sm:px-5 py-1.5 sm:py-2.5 rounded-xl items-center gap-1 sm:gap-1.5 whitespace-nowrap shadow-md">
          <span>⚡</span><span class="hidden sm:inline">Plan Trip</span><span class="sm:hidden">Plan</span>
        </button>
      </div>

    </div>
  </header>

  <!-- Modern Mobile Bottom Navigation Bar (Docked / Thumb-Friendly) -->
  <nav id="mobileBottomNav" class="lg:hidden fixed bottom-0 left-0 right-0 z-50 px-1.5 sm:px-2 py-1.5 sm:py-2 flex items-center justify-around text-xs shadow-2xl" style="padding-bottom: max(0.4rem, env(safe-area-inset-bottom));">
    <button onclick="switchPage('home')" id="mob-home" class="active-mob-tab flex flex-col items-center gap-0.5 py-1 px-2 rounded-xl transition">
      <span class="text-base leading-none">🌟</span>
      <span class="text-[9px] sm:text-[10px] leading-tight">Home</span>
    </button>
    <button onclick="switchPage('planner')" id="mob-planner" class="flex flex-col items-center gap-0.5 py-1 px-2 rounded-xl transition">
      <span class="text-base leading-none">🚀</span>
      <span class="text-[9px] sm:text-[10px] leading-tight">Planner</span>
    </button>
    <button onclick="switchPage('budget')" id="mob-budget" class="flex flex-col items-center gap-0.5 py-1 px-2 rounded-xl transition">
      <span class="text-base leading-none">💰</span>
      <span class="text-[9px] sm:text-[10px] leading-tight">Budget</span>
    </button>
    <button onclick="switchPage('packing')" id="mob-packing" class="flex flex-col items-center gap-0.5 py-1 px-2 rounded-xl transition">
      <span class="text-base leading-none">🎒</span>
      <span class="text-[9px] sm:text-[10px] leading-tight">Packing</span>
    </button>
    <button onclick="switchPage('saved')" id="mob-saved" class="flex flex-col items-center gap-0.5 py-1 px-2 rounded-xl transition">
      <span class="text-base leading-none">📂</span>
      <span class="text-[9px] sm:text-[10px] leading-tight">Saved (<span id="mobSavedCount">0</span>)</span>
    </button>
  </nav>

  <!-- ==================== MAIN CONTENT ==================== -->
  <main class="flex-grow max-w-7xl w-full mx-auto px-3 sm:px-6 lg:px-8 py-5 sm:py-8 pb-28 lg:pb-12 relative" style="z-index: 10;">

    <!-- Region Information Alert Banner -->
    <div id="regionInfoBanner" class="mb-6 sm:mb-8 p-3 sm:p-4 rounded-2xl bg-gradient-to-r from-coralPrimary/10 via-amberAccent/10 to-cyanAccent/10 border border-coralPrimary/30 flex items-center justify-between text-xs sm:text-sm text-gray-200">
      <div class="flex items-start sm:items-center gap-2.5 sm:gap-3 min-w-0 flex-1">
        <span class="text-xl sm:text-2xl shrink-0 mt-0.5 sm:mt-0" id="bannerFlag">🇮🇳</span>
        <div class="min-w-0 flex-1">
          <span class="font-bold text-amberAccent text-xs sm:text-sm block" id="bannerRegionTitle">Active Region: India (INR ₹)</span>
          <p class="text-[11px] sm:text-xs text-gray-400 mt-0.5 leading-snug sm:leading-normal" id="bannerRegionTip">
            Student Perks: Use IRCTC student concessions for rail travel & Google Pay/UPI for zero-fee local food stalls.
          </p>
        </div>
      </div>
      <button onclick="switchPage('planner')" class="hidden md:inline-block px-3 py-1.5 rounded-lg bg-white/10 hover:bg-white/15 text-xs font-bold text-white transition shrink-0 ml-2">
        Explore Plans →
      </button>
    </div>
    
    <!-- PAGE 1: DISCOVER -->
    <section id="page-home" class="space-y-12 sm:space-y-20">
      
      <!-- HERO SECTION WITH 3D DEPTH & PREVIEW WIDGET -->
      <div class="relative rounded-3xl overflow-hidden glass-card p-5 sm:p-10 lg:p-14 border border-white/15 shadow-2xl">
        <div class="grid grid-cols-1 lg:grid-cols-12 gap-8 lg:gap-10 items-center">
          
          <!-- Hero Left Column -->
          <div class="lg:col-span-7 space-y-5 sm:space-y-6">
            <div class="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-white/5 border border-white/10 text-[10px] sm:text-xs font-semibold text-amberAccent shadow-inner max-w-full">
              <span class="w-2 h-2 rounded-full bg-emeraldAccent shrink-0 animate-ping"></span>
              <span class="text-white truncate">Next-Gen Student Travel</span>
              <span class="text-gray-400 hidden sm:inline">•</span>
              <span class="hidden sm:inline">Sub-Second AI Engine</span>
            </div>

            <h1 class="text-3xl sm:text-5xl lg:text-6xl font-extrabold tracking-tight text-white leading-[1.15]">
              Plan Epic Student Adventures <br/>
              <span class="bg-clip-text text-transparent bg-gradient-to-r from-coralPrimary via-amberAccent to-cyanAccent animate-text-shimmer">
                On Any Budget in Seconds.
              </span>
            </h1>

            <p class="text-gray-300 text-xs sm:text-base leading-relaxed max-w-xl">
              Day-by-day itineraries, verified local student discounts, interactive 3D map pins, and offline PDF exports powered by high-speed Groq AI.
            </p>

            <!-- Quick Search Input & CTA -->
            <div class="pt-2 space-y-3">
              <div class="flex flex-col sm:flex-row gap-3 max-w-xl">
                <input
                  type="text"
                  id="heroDestInput"
                  autocomplete="off"
                  spellcheck="false"
                  autocorrect="off"
                  autocapitalize="off"
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
                <img src="https://images.unsplash.com/photo-1503899036084-c55cdd92da26?auto=format&fit=crop&w=600&q=80" alt="Tokyo Trip Preview" loading="lazy" decoding="async" class="w-full h-full object-cover" />
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
          <div class="flex flex-col sm:flex-row sm:items-center gap-3 w-full lg:w-auto">
            <!-- National vs International Scope Toggle -->
            <div class="p-1 rounded-2xl sm:rounded-full bg-white/5 border border-white/10 flex flex-wrap sm:flex-nowrap items-center justify-center gap-1 shadow-inner w-full sm:w-auto">
              <button
                type="button"
                data-scope="all"
                onclick="setHotspotScope('all')"
                class="hotspot-scope-btn active text-xs px-3.5 sm:px-4 py-1.5 sm:py-2 rounded-xl sm:rounded-full border border-transparent bg-gradient-to-r from-coralPrimary to-amberAccent text-white font-extrabold transition shadow-md flex items-center gap-1.5 flex-1 sm:flex-initial justify-center"
              >
                <span>🌍</span> All (16)
              </button>
              <button
                type="button"
                data-scope="national"
                onclick="setHotspotScope('national')"
                class="hotspot-scope-btn text-xs px-3.5 sm:px-4 py-1.5 sm:py-2 rounded-xl sm:rounded-full border border-white/10 bg-white/5 text-gray-300 hover:text-white hover:border-white/20 transition flex items-center gap-1.5 flex-1 sm:flex-initial justify-center"
              >
                <span>🇮🇳</span> National (8)
              </button>
              <button
                type="button"
                data-scope="international"
                onclick="setHotspotScope('international')"
                class="hotspot-scope-btn text-xs px-3.5 sm:px-4 py-1.5 sm:py-2 rounded-xl sm:rounded-full border border-white/10 bg-white/5 text-gray-300 hover:text-white hover:border-white/20 transition flex items-center gap-1.5 flex-1 sm:flex-initial justify-center"
              >
                <span>✈️</span> International (8)
              </button>
            </div>
          </div>
        </div>

        <!-- Secondary Theme Filter Pills -->
        <div class="flex flex-wrap items-center gap-1.5 sm:gap-2" id="hotspotFilterPills">
          <span class="text-xs font-bold text-gray-400 mr-1 flex items-center gap-1"><span>✨</span> Vibe:</span>
          <button type="button" data-cat="all" onclick="setHotspotCategory('all')" class="hotspot-filter-btn active text-xs px-3 sm:px-3.5 py-1.5 rounded-full border border-transparent bg-white/20 text-white font-bold transition shadow-sm">All Vibes</button>
          <button type="button" data-cat="beach" onclick="setHotspotCategory('beach')" class="hotspot-filter-btn text-xs px-3 sm:px-3.5 py-1.5 rounded-full border border-white/10 bg-white/5 text-gray-400 hover:text-white transition">🏖️ Beach</button>
          <button type="button" data-cat="mountain" onclick="setHotspotCategory('mountain')" class="hotspot-filter-btn text-xs px-3 sm:px-3.5 py-1.5 rounded-full border border-white/10 bg-white/5 text-gray-400 hover:text-white transition">🏔️ Mountains</button>
          <button type="button" data-cat="culture" onclick="setHotspotCategory('culture')" class="hotspot-filter-btn text-xs px-3 sm:px-3.5 py-1.5 rounded-full border border-white/10 bg-white/5 text-gray-400 hover:text-white transition">🏛️ History</button>
          <button type="button" data-cat="nightlife" onclick="setHotspotCategory('nightlife')" class="hotspot-filter-btn text-xs px-3 sm:px-3.5 py-1.5 rounded-full border border-white/10 bg-white/5 text-gray-400 hover:text-white transition">🎉 Nightlife</button>
          <button type="button" data-cat="adventure" onclick="setHotspotCategory('adventure')" class="hotspot-filter-btn text-xs px-3 sm:px-3.5 py-1.5 rounded-full border border-white/10 bg-white/5 text-gray-400 hover:text-white transition">⚡ Adventure</button>
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
                <img src="https://images.unsplash.com/photo-1512343879784-a960bf40e7f2?auto=format&fit=crop&w=600&q=80" alt="Goa Beaches" loading="lazy" decoding="async" class="w-full h-full object-cover group-hover:scale-105 transition duration-500" />
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
                <img src="https://images.unsplash.com/photo-1626621341517-bbf3d9990a23?auto=format&fit=crop&w=600&q=80" alt="Manali Mountains" loading="lazy" decoding="async" class="w-full h-full object-cover group-hover:scale-105 transition duration-500" />
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
                <img src="https://images.unsplash.com/photo-1599661046289-e31897846e41?auto=format&fit=crop&w=600&q=80" alt="Jaipur Palace" loading="lazy" decoding="async" class="w-full h-full object-cover group-hover:scale-105 transition duration-500" />
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
                <img src="https://images.unsplash.com/photo-1596401057633-54a8fe8ef647?auto=format&fit=crop&w=600&q=80" alt="Rishikesh River & Bridges" loading="lazy" decoding="async" class="w-full h-full object-cover group-hover:scale-105 transition duration-500" />
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
                <img src="https://images.unsplash.com/photo-1571536802807-30451e3955d8?auto=format&fit=crop&w=600&q=80" alt="Varanasi Ganga Ghats" loading="lazy" decoding="async" class="w-full h-full object-cover group-hover:scale-105 transition duration-500" />
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
                <img src="https://images.unsplash.com/photo-1602216056096-3b40cc0c9944?auto=format&fit=crop&w=600&q=80" alt="Munnar Tea Hills" loading="lazy" decoding="async" class="w-full h-full object-cover group-hover:scale-105 transition duration-500" />
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
                <img src="https://images.unsplash.com/photo-1581793745862-99fde7fa73d2?auto=format&fit=crop&w=600&q=80" alt="Leh Ladakh Pangong Lake" loading="lazy" decoding="async" class="w-full h-full object-cover group-hover:scale-105 transition duration-500" />
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
                <img src="https://images.unsplash.com/photo-1607604276583-eef5d076aa5f?auto=format&fit=crop&w=600&q=80" alt="Meghalaya Living Root Bridge & Waterfalls" loading="lazy" decoding="async" class="w-full h-full object-cover group-hover:scale-105 transition duration-500" />
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
                <img src="https://images.unsplash.com/photo-1503899036084-c55cdd92da26?auto=format&fit=crop&w=600&q=80" alt="Tokyo City" loading="lazy" decoding="async" class="w-full h-full object-cover group-hover:scale-105 transition duration-500" />
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
                <img src="https://images.unsplash.com/photo-1537996194471-e657df975ab4?auto=format&fit=crop&w=600&q=80" alt="Bali Beach" loading="lazy" decoding="async" class="w-full h-full object-cover group-hover:scale-105 transition duration-500" />
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
                <img src="https://images.unsplash.com/photo-1508009603885-50cf7c579365?auto=format&fit=crop&w=600&q=80" alt="Bangkok Temples" loading="lazy" decoding="async" class="w-full h-full object-cover group-hover:scale-105 transition duration-500" />
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
                <img src="https://images.unsplash.com/photo-1552832230-c0197dd311b5?auto=format&fit=crop&w=600&q=80" alt="Rome Colosseum" loading="lazy" decoding="async" class="w-full h-full object-cover group-hover:scale-105 transition duration-500" />
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
                <img src="https://images.unsplash.com/photo-1512470876302-972faa2aa9a4?auto=format&fit=crop&w=600&q=80" alt="Amsterdam Canals" loading="lazy" decoding="async" class="w-full h-full object-cover group-hover:scale-105 transition duration-500" />
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
                <img src="https://images.unsplash.com/photo-1493976040374-85c8e12f0c0e?auto=format&fit=crop&w=600&q=80" alt="Kyoto Shrine" loading="lazy" decoding="async" class="w-full h-full object-cover group-hover:scale-105 transition duration-500" />
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
                <img src="https://images.unsplash.com/photo-1502602898657-3e91760cbb34?auto=format&fit=crop&w=600&q=80" alt="Paris Eiffel Tower" loading="lazy" decoding="async" class="w-full h-full object-cover group-hover:scale-105 transition duration-500" />
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
                <img src="https://images.unsplash.com/photo-1512453979798-5ea266f8880c?auto=format&fit=crop&w=600&q=80" alt="Dubai Skyline" loading="lazy" decoding="async" class="w-full h-full object-cover group-hover:scale-105 transition duration-500" />
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
                <input type="text" id="plannerDest" autocomplete="off" spellcheck="false" autocorrect="off" autocapitalize="off" placeholder="e.g. Kyoto, Japan or Rome, Italy" class="w-full px-4 py-3 bg-spaceDark border border-white/15 rounded-xl text-sm text-white focus:outline-none focus:border-coralPrimary shadow-inner" />
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
                    <option value="Moderate Backpacker">Moderate Backpacker</option>
                    <option value="Luxury Student">Luxury Student</option>
                  </select>
                </div>
              </div>

              <!-- Student Mode Toggle Option -->
              <div id="studentModeCard" class="p-3.5 rounded-2xl bg-gradient-to-r from-coralPrimary/10 via-amberAccent/5 to-cyanAccent/10 border border-coralPrimary/20 flex items-center justify-between gap-3 shadow-inner transition">
                <div class="flex items-center gap-2.5">
                  <span class="text-xl" id="studentModeIcon">🎒</span>
                  <div>
                    <div class="flex items-center gap-1.5">
                      <span class="text-xs font-bold text-white">Student Mode</span>
                      <span id="studentModeBadge" class="text-[10px] font-extrabold px-2 py-0.5 rounded-full bg-coralPrimary text-white uppercase tracking-wider shadow-sm">ON</span>
                    </div>
                    <p class="text-[11px] text-gray-400 leading-tight mt-0.5" id="studentModeDesc">
                      Enables student discounts, hostel stays & budget savings hacks
                    </p>
                  </div>
                </div>
                <label class="relative inline-flex items-center cursor-pointer select-none">
                  <input type="checkbox" id="plannerStudentMode" checked class="sr-only peer" onchange="onStudentModeToggle(this.checked)" />
                  <div class="w-11 h-6 bg-gray-700 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-coralPrimary shadow-sm"></div>
                </label>
              </div>

              <div class="grid grid-cols-3 gap-3">
                <div class="space-y-1">
                  <label class="text-[11px] font-bold text-gray-400">Currency</label>
                  <input type="text" id="plannerCurr" readonly value="INR (₹)" class="w-full px-2.5 py-2.5 bg-spaceDark/60 border border-white/10 rounded-xl text-xs text-amberAccent font-bold" />
                </div>
                <div class="col-span-2 space-y-1">
                  <label class="text-[11px] font-bold text-gray-400">Cap Budget (Optional)</label>
                  <input type="text" id="plannerBudgetCap" autocomplete="off" spellcheck="false" autocorrect="off" autocapitalize="off" placeholder="e.g. 20000 or 500" class="w-full px-3 py-2.5 bg-spaceDark border border-white/15 rounded-xl text-xs text-white" />
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
                  <input type="text" id="plannerMustVisit" autocomplete="off" spellcheck="false" autocorrect="off" autocapitalize="off" placeholder="e.g. Colosseum" class="w-full px-3 py-2.5 bg-spaceDark border border-white/15 rounded-xl text-xs text-white" />
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
        <div class="glass-card p-4 sm:p-6 rounded-3xl border border-white/10 flex flex-col justify-between shadow-2xl h-full min-h-[360px] sm:min-h-[440px] lg:min-h-[540px]" id="plannerMapCard">
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
            <!-- Map Legend (shown with map) -->
            <div id="mapLegend" class="roam-map-legend hidden">
              <span><span class="legend-dot" style="background:#FF6B4A; color:#FF6B4A;"></span>Destination</span>
              <span><span class="legend-dot" style="background:#FFB347; color:#FFB347;"></span>Must Visit</span>
              <span><span class="legend-dot" style="background:#4AEAFF; color:#4AEAFF;"></span>Landmarks</span>
            </div>
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
        <div id="plannerResults" class="hidden glass-card p-4 sm:p-8 lg:p-10 rounded-3xl border border-white/10 space-y-6 shadow-2xl">
          <!-- Top Action Bar -->
          <div class="flex flex-wrap items-center justify-between gap-4 pb-5 border-b border-white/10">
            <div>
              <div class="flex items-center gap-2">
                <span class="text-2xl">📝</span>
                <div>
                  <h3 id="itineraryMainHeading" class="text-xl sm:text-2xl font-extrabold text-white leading-tight">
                    Your Itinerary Blueprint
                  </h3>
                  <p class="text-xs sm:text-sm text-gray-400 mt-0.5" id="itinerarySubtitle">
                    Comprehensive day-by-day plan, budget matrix & interactive GPS-synced landmarks
                  </p>
                </div>
              </div>
            </div>
            
            <div class="flex flex-wrap items-center gap-2.5">
              <!-- Student / Standard Traveler Mode Switcher Button on Blueprint -->
              <button id="itineraryStudentModeBtn" type="button" onclick="toggleItineraryStudentMode()" class="px-3.5 py-1.5 rounded-xl text-xs font-extrabold flex items-center gap-1.5 border transition shadow-sm bg-emerald-500/15 hover:bg-emerald-500/25 text-emerald-400 border-emerald-500/30" title="Switch between Student Mode and Standard Traveler Mode">
                <span id="itineraryStudentModeIcon">🎓</span>
                <span id="itineraryStudentModeText">Student Mode: ON</span>
              </button>

              <!-- View Mode Switcher -->
              <div class="flex items-center bg-spaceDark/80 p-1 rounded-xl border border-white/10 text-xs shadow-inner">
                <button id="viewModeCardsBtn" type="button" onclick="setItineraryViewMode('cards')" class="px-3 py-1.5 rounded-lg font-bold transition flex items-center gap-1.5 bg-coralPrimary text-white shadow-sm">
                  <span>🗂️ Cards</span>
                </button>
                <button id="viewModeDocBtn" type="button" onclick="setItineraryViewMode('doc')" class="px-3 py-1.5 rounded-lg font-bold transition flex items-center gap-1.5 text-gray-400 hover:text-white">
                  <span>📄 Document</span>
                </button>
              </div>

              <button onclick="saveTrip()" class="btn-secondary px-3.5 py-2 rounded-xl text-xs font-bold flex items-center gap-1.5 shadow-sm">
                <span>💾 Save</span>
              </button>
              <button onclick="copyTrip()" class="btn-secondary px-3.5 py-2 rounded-xl text-xs font-bold flex items-center gap-1.5 shadow-sm">
                <span>📋 Copy</span>
              </button>
              <button onclick="downloadTripPDF()" class="btn-gradient px-4 py-2 rounded-xl text-xs font-bold flex items-center gap-1.5 shadow-md">
                <span>⬇️ Export PDF</span>
              </button>
            </div>
          </div>

          <!-- Trip Overview & Metrics Ribbon -->
          <div id="itineraryMetricsBar" class="grid grid-cols-2 lg:grid-cols-4 gap-3">
            <div class="glass-card p-3.5 rounded-2xl border border-white/10 flex items-center gap-3 shadow-sm">
              <div class="w-10 h-10 rounded-xl bg-coralPrimary/15 border border-coralPrimary/30 flex items-center justify-center text-lg shadow-inner">
                📅
              </div>
              <div class="min-w-0">
                <div class="text-[10px] uppercase font-bold text-gray-400">Duration</div>
                <div id="metricDays" class="text-sm sm:text-base font-extrabold text-white truncate">3 Days</div>
              </div>
            </div>

            <div class="glass-card p-3.5 rounded-2xl border border-white/10 flex items-center gap-3 shadow-sm">
              <div class="w-10 h-10 rounded-xl bg-cyanAccent/15 border border-cyanAccent/30 flex items-center justify-center text-lg shadow-inner">
                📍
              </div>
              <div class="min-w-0">
                <div class="text-[10px] uppercase font-bold text-gray-400">Map Landmarks</div>
                <div id="metricPins" class="text-sm sm:text-base font-extrabold text-cyanAccent truncate">0 Live Pins</div>
              </div>
            </div>

            <div class="glass-card p-3.5 rounded-2xl border border-white/10 flex items-center gap-3 shadow-sm">
              <div class="w-10 h-10 rounded-xl bg-amberAccent/15 border border-amberAccent/30 flex items-center justify-center text-lg shadow-inner">
                💰
              </div>
              <div class="min-w-0">
                <div class="text-[10px] uppercase font-bold text-gray-400">Target Budget</div>
                <div id="metricBudget" class="text-sm sm:text-base font-extrabold text-amberAccent truncate">Estimated</div>
              </div>
            </div>

            <div class="glass-card p-3.5 rounded-2xl border border-white/10 flex items-center gap-3 shadow-sm">
              <div class="w-10 h-10 rounded-xl bg-emeraldAccent/15 border border-emeraldAccent/30 flex items-center justify-center text-lg shadow-inner">
                🧭
              </div>
              <div class="min-w-0">
                <div class="text-[10px] uppercase font-bold text-gray-400">Expedition Circuit</div>
                <div id="metricPhases" class="text-sm sm:text-base font-extrabold text-emeraldAccent truncate">Single Circuit</div>
              </div>
            </div>
          </div>

          <!-- Interactive Phase Navigation Ribbon (for Multi-Day / Multi-Phase Journeys) -->
          <div id="itineraryPhaseNavContainer" class="hidden space-y-2 pt-1">
            <div class="flex items-center justify-between text-xs text-gray-400">
              <span class="font-bold flex items-center gap-1.5 text-gray-300">
                <span>⚡</span> Filter by Expedition Phase:
              </span>
              <span id="activePhaseCount" class="text-[11px] text-cyanAccent">Showing All Phases</span>
            </div>
            <div id="itineraryPhasePills" class="flex items-center gap-2 overflow-x-auto pb-2 scrollbar-none">
              <!-- Dynamically populated phase pill buttons -->
            </div>
          </div>

          <!-- Search & Card Controls Toolbar -->
          <div id="itineraryCardsToolbar" class="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3 p-3 rounded-2xl bg-spaceDark/60 border border-white/10">
            <div class="relative flex-grow max-w-md">
              <span class="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-gray-400 text-xs">
                🔍
              </span>
              <input
                type="text"
                id="itinerarySearchInput"
                placeholder="Search days, landmarks, dishes, student hacks..."
                oninput="filterItineraryCards()"
                class="w-full pl-9 pr-8 py-2 bg-spaceDark border border-white/10 rounded-xl text-xs text-white placeholder-gray-500 focus:outline-none focus:border-cyanAccent transition shadow-inner"
              />
              <button
                type="button"
                id="itinerarySearchClear"
                onclick="clearItinerarySearch()"
                class="hidden absolute inset-y-0 right-0 pr-3 flex items-center text-gray-400 hover:text-white text-xs"
              >
                ✕
              </button>
            </div>

            <div class="flex items-center justify-between sm:justify-end gap-2 text-xs">
              <span id="itineraryCardsCountBadge" class="text-[11px] text-gray-400 px-2.5 py-1 rounded-lg bg-white/5 border border-white/5">
                Showing all days
              </span>
              <button
                type="button"
                onclick="toggleAllDayCards(true)"
                class="px-2.5 py-1 rounded-lg bg-white/5 hover:bg-white/10 text-gray-300 border border-white/10 transition text-xs font-semibold"
                title="Expand all day cards"
              >
                🔽 Expand
              </button>
              <button
                type="button"
                onclick="toggleAllDayCards(false)"
                class="px-2.5 py-1 rounded-lg bg-white/5 hover:bg-white/10 text-gray-300 border border-white/10 transition text-xs font-semibold"
                title="Collapse all day cards"
              >
                🔼 Collapse
              </button>
            </div>
          </div>

          <!-- Cards View: Day by Day structured interactive cards -->
          <div id="itineraryCardsView" class="space-y-4">
            <!-- Dynamic day cards rendered here -->
          </div>

          <!-- Document View: Raw sanitized Markdown (Toggleable) -->
          <div id="itineraryDocView" class="hidden">
            <div id="itineraryView" class="itinerary-prose text-sm p-5 sm:p-8 rounded-2xl bg-spaceDark/70 border border-white/5 shadow-inner"></div>
          </div>

          <!-- Essential Student Tips Banner (Always visible in cards view) -->
          <div id="itineraryTipsCard" class="hidden glass-card p-5 sm:p-6 rounded-2xl border border-cyanAccent/20 bg-gradient-to-br from-cyanAccent/5 to-transparent space-y-3 shadow-lg">
            <div class="flex items-center gap-2 pb-2 border-b border-white/10">
              <span class="text-xl">🎒</span>
              <h4 class="text-sm sm:text-base font-bold text-white">Essential Student Travel Hacks & Safety</h4>
            </div>
            <div id="itineraryTipsContent" class="grid grid-cols-1 md:grid-cols-3 gap-3 text-xs text-gray-300">
              <!-- Dynamically populated tips -->
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
            <div><label class="text-xs font-bold text-gray-300">Days</label><input type="number" id="bDays" value="4" min="1" max="90" class="w-full px-3 py-2 bg-spaceDark border border-white/15 rounded-xl text-sm text-white" oninput="debouncedCalcBudget()" /></div>
            <div><label class="text-xs font-bold text-gray-300">Region Currency</label><input type="text" id="bCurrDisplay" readonly value="INR (₹)" class="w-full px-3 py-2 bg-spaceDark/60 border border-white/10 rounded-xl text-sm text-amberAccent font-bold" /></div>
          </div>
          <div><div class="flex justify-between text-xs text-gray-300"><span>🚆 Flights / Trains</span><span id="bValTrans">₹3,000</span></div><input type="range" id="bTrans" min="0" max="50000" step="500" value="3000" class="w-full accent-coralPrimary cursor-pointer" oninput="debouncedCalcBudget()" /></div>
          <div><div class="flex justify-between text-xs text-gray-300"><span>🏨 Hostel (Per Night)</span><span id="bValStay">₹800</span></div><input type="range" id="bStay" min="200" max="10000" step="100" value="800" class="w-full accent-cyanAccent cursor-pointer" oninput="debouncedCalcBudget()" /></div>
          <div><div class="flex justify-between text-xs text-gray-300"><span>🍜 Food (Per Day)</span><span id="bValFood">₹600</span></div><input type="range" id="bFood" min="100" max="8000" step="100" value="600" class="w-full accent-amberAccent cursor-pointer" oninput="debouncedCalcBudget()" /></div>
          <div><div class="flex justify-between text-xs text-gray-300"><span>🎟️ Activities (Per Day)</span><span id="bValAct">₹400</span></div><input type="range" id="bAct" min="0" max="5000" step="100" value="400" class="w-full accent-emeraldAccent cursor-pointer" oninput="debouncedCalcBudget()" /></div>
          <div><div class="flex justify-between text-xs text-gray-300"><span>🛡️ Emergency Buffer</span><span id="bValBuf">₹1,500</span></div><input type="range" id="bBuf" min="0" max="15000" step="250" value="1500" class="w-full accent-purpleAccent cursor-pointer" oninput="debouncedCalcBudget()" /></div>
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
      <div class="glass-card p-5 sm:p-7 rounded-3xl border border-white/10 space-y-5 shadow-xl">
        <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div class="space-y-1.5 w-full sm:w-auto">
            <div class="flex items-center justify-between gap-2">
              <span class="text-[11px] font-bold text-gray-400 uppercase tracking-wider flex items-center gap-1.5">
                <span>📍</span> Itinerary & Destination Vibe
              </span>
              <span id="packVibeBadge" class="text-[10px] font-bold px-2.5 py-0.5 rounded-full bg-emeraldAccent/20 text-emeraldAccent border border-emeraldAccent/30">Auto Active</span>
            </div>
            <select
              id="packVibeSelector"
              onchange="onPackVibeChange(this.value)"
              class="w-full sm:w-auto px-3 py-2 bg-spaceDark border border-white/15 rounded-xl text-xs font-semibold text-white focus:outline-none focus:border-emeraldAccent shadow-sm"
            >
              <option value="auto">📍 Auto-detect from Itinerary / Planner</option>
              <option value="beach">🏖️ Beach, Island & Coastal (Goa, Bali, Phuket)</option>
              <option value="mountain">🏔️ Mountains, Hiking & Trekking (Manali, Alps)</option>
              <option value="city">🏙️ City Sightseeing & Culture (Tokyo, Rome, London)</option>
              <option value="winter">❄️ Cold Weather & Snow (Alps, Sapporo, Kashmir)</option>
              <option value="hostel">🎒 Classic Backpacker & Hostel Dorm</option>
            </select>
          </div>

          <div class="flex items-center gap-2 pt-1 sm:pt-0">
            <button onclick="checkAllPacking(true)" class="btn-secondary flex-1 sm:flex-initial px-3 py-1.5 rounded-xl text-xs font-semibold text-center">
              ✅ Check All
            </button>
            <button onclick="checkAllPacking(false)" class="btn-secondary flex-1 sm:flex-initial px-3 py-1.5 rounded-xl text-xs font-semibold text-center">
              🔄 Uncheck All
            </button>
            <button onclick="resetPackingDefaults()" class="p-2 rounded-xl text-xs text-gray-400 hover:text-red-400 hover:bg-white/5 transition shrink-0" title="Reset to Defaults">
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
      <div class="glass-card p-5 sm:p-6 rounded-3xl border border-white/10 space-y-4 shadow-xl">
        <h3 class="text-sm font-bold text-white flex items-center gap-2">
          <span>➕</span> Add Custom Item
        </h3>
        <div class="flex flex-col sm:flex-row gap-3">
          <input
            type="text"
            id="customPackInput"
            autocomplete="off"
            spellcheck="false"
            autocorrect="off"
            autocapitalize="off"
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

      <!-- Category Filter Pills (Horizontal Swipe on Mobile) -->
      <div class="flex items-center gap-2 overflow-x-auto pb-2 -mx-2 px-2 sm:mx-0 sm:px-0 sm:flex-wrap no-scrollbar" id="packCategoryFilterPills">
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

  <!-- Toast Notification Container (Responsive Mobile Offset) -->
  <div id="toastContainer" class="fixed bottom-20 lg:bottom-6 right-4 sm:right-6 left-4 sm:left-auto z-50 flex flex-col gap-2.5 max-w-sm w-auto sm:w-full pointer-events-none"></div>

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
  <footer class="mt-12 sm:mt-24 pb-24 lg:pb-12 px-4 sm:px-6 lg:px-8 relative" style="z-index: 10;">
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
    // PERFORMANCE UTILITIES: DEBOUNCING & THROTTLING
    // ========================================================
    function debounce(func, wait = 200) {
      let timeout;
      return function(...args) {
        clearTimeout(timeout);
        timeout = setTimeout(() => func.apply(this, args), wait);
      };
    }

    function throttle(func, limit = 50) {
      let inThrottle;
      return function(...args) {
        if (!inThrottle) {
          func.apply(this, args);
          inThrottle = true;
          setTimeout(() => inThrottle = false, limit);
        }
      };
    }

    // ========================================================
    // SMART GLASS NAVBAR AUTO-HIDE / REVEAL ON SCROLL (RAF THROTTLED)
    // ========================================================
    let lastScrollY = window.scrollY;
    let scrollTicking = false;
    const scrollThreshold = 12;
    const headerEl = document.getElementById('mainHeader');

    window.addEventListener('scroll', () => {
      if (!scrollTicking) {
        window.requestAnimationFrame(() => {
          const currentScrollY = window.scrollY;
          if (headerEl) {
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
          }
          lastScrollY = Math.max(0, currentScrollY);
          scrollTicking = false;
        });
        scrollTicking = true;
      }
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

    // Secure & Sanitized Markdown Parser (Prevents XSS Attacks)
    function safeMarkdown(content) {
      if (!content) return '';
      try {
        const rawHtml = marked.parse(content);
        return typeof DOMPurify !== 'undefined' ? DOMPurify.sanitize(rawHtml) : rawHtml;
      } catch (e) {
        return content;
      }
    }

    // Debounced Responsive Map Invalidate Listener on Resize / Orientation Change
    let mapResizeTimer = null;
    window.addEventListener('resize', function() {
      clearTimeout(mapResizeTimer);
      mapResizeTimer = setTimeout(function() {
        if (mapInstance && typeof mapInstance.invalidateSize === 'function') {
          mapInstance.invalidateSize();
        }
      }, 200);
    });

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
        if (pageEl) {
          const isTarget = (p === page);
          pageEl.classList.toggle('hidden', !isTarget);
          if (isTarget) {
            pageEl.classList.remove('page-enter');
            void pageEl.offsetWidth; // Force reflow for smooth animation restart
            pageEl.classList.add('page-enter');
          }
        }
        const t = document.getElementById(`tab-${p}`);
        if (t) t.classList.toggle('active', p === page);
        const m = document.getElementById(`mob-${p}`);
        if (m) {
          const isAct = (p === page);
          m.classList.toggle('active-mob-tab', isAct);
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
    function toggleItineraryStudentMode() {
      if (!currentTrip) return;
      if (!currentTrip.trip_summary) currentTrip.trip_summary = {};
      const currentVal = currentTrip.trip_summary.student_mode !== false;
      const newVal = !currentVal;
      currentTrip.trip_summary.student_mode = newVal;

      // Sync the planner form checkbox
      onStudentModeToggle(newVal, true);

      // Re-render the blueprint with smooth update
      renderItineraryBlueprint(currentTrip);

      showToast(newVal ? 'Switched to 🎓 Student Explorer Mode' : 'Switched to ✨ Standard Traveler Mode', 'info', 2200);
    }

    function onStudentModeToggle(isStudent, triggerAutoSave = true) {
      const checkbox = document.getElementById('plannerStudentMode');
      if (checkbox && checkbox.checked !== isStudent) {
        checkbox.checked = isStudent;
      }
      const badge = document.getElementById('studentModeBadge');
      const icon = document.getElementById('studentModeIcon');
      const desc = document.getElementById('studentModeDesc');
      const card = document.getElementById('studentModeCard');

      if (isStudent) {
        if (badge) {
          badge.innerText = 'ON';
          badge.className = 'text-[10px] font-extrabold px-2 py-0.5 rounded-full bg-coralPrimary text-white uppercase tracking-wider shadow-sm';
        }
        if (icon) icon.innerText = '🎒';
        if (desc) desc.innerText = 'Enables student discounts, hostel stays & budget savings hacks';
        if (card) card.className = 'p-3.5 rounded-2xl bg-gradient-to-r from-coralPrimary/10 via-amberAccent/5 to-cyanAccent/10 border border-coralPrimary/30 flex items-center justify-between gap-3 shadow-inner transition';
      } else {
        if (badge) {
          badge.innerText = 'OFF';
          badge.className = 'text-[10px] font-extrabold px-2 py-0.5 rounded-full bg-slate-700 text-gray-300 uppercase tracking-wider shadow-sm';
        }
        if (icon) icon.innerText = '✈️';
        if (desc) desc.innerText = 'Standard curated travel: boutique stays, gastronomy, skip-the-line admissions';
        if (card) card.className = 'p-3.5 rounded-2xl bg-gradient-to-r from-blue-500/10 via-indigo-500/5 to-purple-500/10 border border-blue-500/30 flex items-center justify-between gap-3 shadow-inner transition';
      }

      if (triggerAutoSave) {
        savePlannerDraft();
      }
    }

    function savePlannerDraft() {
      try {
        const draft = {
          destination: document.getElementById('plannerDest')?.value || '',
          days: document.getElementById('plannerDays')?.value || '3',
          tier: document.getElementById('plannerTier')?.value || 'Student (Low)',
          studentMode: document.getElementById('plannerStudentMode') ? document.getElementById('plannerStudentMode').checked : true,
          budgetCap: document.getElementById('plannerBudgetCap')?.value || '',
          mustVisit: document.getElementById('plannerMustVisit')?.value || '',
          pace: document.getElementById('plannerPace')?.value || 'Balanced',
          interests: selectedInterests
        };
        sessionStorage.setItem('roamai_planner_draft', JSON.stringify(draft));
      } catch (e) {}
    }

    const debouncedSavePlannerDraft = debounce(savePlannerDraft, 300);

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
          if (draft.studentMode !== undefined) {
            onStudentModeToggle(draft.studentMode, false);
          } else {
            onStudentModeToggle(true, false);
          }
          if (Array.isArray(draft.interests) && draft.interests.length > 0) {
            selectedInterests = draft.interests;
            document.querySelectorAll('#interestPills .chip-tag').forEach(tag => {
              const text = tag.innerText.replace(/^[^\\s]+\\s*/, '').trim();
              const isActive = selectedInterests.some(i => text.includes(i) || i.includes(text));
              tag.classList.toggle('active', isActive);
            });
          }
        }

        // 2. Attach Debounced Auto-Save listeners to all form controls
        ['plannerDest', 'plannerDays', 'plannerTier', 'plannerBudgetCap', 'plannerMustVisit', 'plannerPace'].forEach(id => {
          const el = document.getElementById(id);
          if (el) {
            el.addEventListener('input', debouncedSavePlannerDraft);
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
            renderItineraryBlueprint(tripData);
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
          onStudentModeToggle(true, false);

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

      const isStudentMode = document.getElementById('plannerStudentMode') ? document.getElementById('plannerStudentMode').checked : true;

      try {
        const res = await fetch('/api/generate', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            destination, days, budget_level: budgetTier, budget_amount: budgetAmount,
            currency, region: reg.name, interests: selectedInterests, must_visit: mustVisit, travel_pace: pace,
            student_mode: isStudentMode
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

        // Render Blueprint (Cards + Document)
        renderItineraryBlueprint(data);
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
      const legend = document.getElementById('mapLegend');
      if (placeholder) placeholder.classList.add('hidden');
      if (mapEl) mapEl.classList.remove('hidden');
      if (legend) legend.classList.remove('hidden');

      const badge = document.getElementById('mapStatusBadge');
      if (badge) {
        badge.innerText = `Live GPS Pins · ${markers.length}`;
        badge.className = 'text-xs text-cyanAccent font-semibold px-2.5 py-0.5 rounded-full bg-cyanAccent/10 border border-cyanAccent/20';
      }

      const centerCoords = center || (markers.length > 0 ? markers[0].coords : [20, 0]);
      if (!mapInstance) {
        mapInstance = L.map('map', {
          zoomControl: false,
          attributionControl: false
        }).setView(centerCoords, 13);

        L.control.zoom({ position: 'topright' }).addTo(mapInstance);
        L.control.attribution({ position: 'bottomright', prefix: false }).addTo(mapInstance);

        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
          maxZoom: 19,
          attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
        }).addTo(mapInstance);
      }

      // Recreate markersLayer using MarkerClusterGroup when available
      if (markersLayer) {
        mapInstance.removeLayer(markersLayer);
      }

      if (typeof L.markerClusterGroup === 'function') {
        markersLayer = L.markerClusterGroup({
          maxClusterRadius: 36,
          spiderfyOnMaxZoom: true,
          showCoverageOnHover: false,
          zoomToBoundsOnClick: true,
          iconCreateFunction: function(cluster) {
            const count = cluster.getChildCount();
            return L.divIcon({
              html: `<div class="roam-cluster-badge"><span>${count}</span></div>`,
              className: 'roam-cluster-container',
              iconSize: [40, 40],
              iconAnchor: [20, 20]
            });
          }
        });
        mapInstance.addLayer(markersLayer);
      } else {
        markersLayer = L.featureGroup().addTo(mapInstance);
      }

      /* --- Marker styling by type --- */
      const markerConfig = {
        destination: { color: '#FF6B4A', icon: '📍', label: 'Destination', glow: 'rgba(255,107,74,0.4)' },
        must_visit:  { color: '#FFB347', icon: '⭐', label: 'Must Visit',  glow: 'rgba(255,179,71,0.4)' },
        landmark:    { color: '#4AEAFF', icon: '🏛️', label: 'Landmark',   glow: 'rgba(74,234,255,0.35)' }
      };

      const bounds = [];
      let landmarkIdx = 0;
      window.leafletMarkersByDay = {};
      window.leafletMarkersByName = {};

      markers.forEach((m, i) => {
        if (!m.coords) return;
        bounds.push(m.coords);

        const cfg = markerConfig[m.type] || markerConfig.landmark;
        const isDestination = m.type === 'destination';
        const size = isDestination ? 42 : 34;
        const innerLabel = m.type === 'landmark' ? (++landmarkIdx) : cfg.icon;
        const borderW = isDestination ? 3 : 2;

        const customIcon = L.divIcon({
          className: 'roam-marker',
          html: `<div class="roam-pin" id="pin-marker-${innerLabel}" style="
            width:${size}px; height:${size}px;
            background: ${cfg.color};
            border: ${borderW}px solid rgba(255,255,255,0.9);
            border-radius: 50% 50% 50% 4px;
            transform: rotate(-45deg);
            box-shadow: 0 0 12px ${cfg.glow}, 0 4px 12px rgba(0,0,0,0.4);
            display:flex; align-items:center; justify-content:center;
            animation: roamPinDrop 0.5s cubic-bezier(0.34,1.56,0.64,1) ${i * 0.02}s both;
          ">
            <span style="transform:rotate(45deg); font-size:${isDestination ? '18px' : '13px'}; line-height:1; color:#fff; font-weight:800; text-shadow:0 1px 3px rgba(0,0,0,0.5);">
              ${innerLabel}
            </span>
          </div>`,
          iconSize: [size, size],
          iconAnchor: [size / 2, size],
          popupAnchor: [0, -size + 4]
        });

        const marker = L.marker(m.coords, { icon: customIcon });
        markersLayer.addLayer(marker);

        const displayName = m.name.replace(/^(Destination: |Must Visit: )/, '');
        const cleanNameKey = displayName.toLowerCase().replace(/[^a-z0-9]/g, '');
        window.leafletMarkersByName[cleanNameKey] = marker;
        if (m.type === 'landmark') {
          window.leafletMarkersByDay[landmarkIdx] = marker;
        }

        const safeDisplay = displayName.replace(/'/g, "\\'");
        const popupContent = `
          <div class="roam-popup">
            <div class="roam-popup-badge" style="background:${cfg.color}20; color:${cfg.color}; border:1px solid ${cfg.color}40;">
              ${cfg.icon} ${cfg.label} ${m.type === 'landmark' ? '#' + innerLabel : ''}
            </div>
            <div class="roam-popup-name">${displayName}</div>
            <div class="roam-popup-coords">
              ${m.coords[0].toFixed(4)}°N, ${m.coords[1].toFixed(4)}°E
            </div>
            ${m.type === 'landmark' ? `
            <button type="button" onclick="highlightItineraryDay(${innerLabel}, '${safeDisplay}')" class="mt-2.5 w-full py-1 text-[11px] font-bold rounded-lg bg-cyanAccent/20 hover:bg-cyanAccent/30 text-cyanAccent border border-cyanAccent/40 transition flex items-center justify-center gap-1 cursor-pointer">
              <span>📅 View Day ${innerLabel} in Itinerary</span>
            </button>` : ''}
          </div>`;

        marker.bindPopup(popupContent, {
          className: 'roam-popup-container',
          maxWidth: 270,
          minWidth: 190
        });

        marker.bindTooltip(displayName, {
          className: 'roam-tooltip',
          direction: 'top',
          offset: [0, -size + 2]
        });

        marker.on('click', () => {
          if (m.type === 'landmark') {
            highlightItineraryDay(innerLabel, displayName);
          }
        });
      });

      if (bounds.length > 1) {
        mapInstance.fitBounds(bounds, { padding: [55, 55], maxZoom: 14 });
      } else if (bounds.length === 1) {
        mapInstance.setView(bounds[0], 13);
      }
      setTimeout(() => mapInstance.invalidateSize(), 300);
    }

    function escapeHtml(str) {
      if (!str) return '';
      return String(str).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
    }

    function parseItineraryMarkdown(markdown) {
      const result = {
        title: '',
        budgetSummary: '',
        phases: [],
        days: [],
        tips: []
      };

      if (!markdown) return result;

      const lines = markdown.split(/\r?\n/);
      let currentPhase = null;
      let currentDay = null;
      let inTipsSection = false;

      const titleMatch = markdown.match(/^#\s+(.+)$/m);
      if (titleMatch) result.title = titleMatch[1].trim();

      const totalBudgetMatch = markdown.match(/Estimated Total:\*{0,2}\s*\*{0,2}(~?[\d,]+\s*[A-Z]+)/i);
      if (totalBudgetMatch) result.budgetSummary = totalBudgetMatch[1].trim();

      for (let i = 0; i < lines.length; i++) {
        const line = lines[i].trim();
        if (!line) continue;

        // Check for Tips Section
        if (/^##\s+(?:🎒|🗺️|💡)?\s*Essential\s+(?:Student|Travel)\s+Tips/i.test(line)) {
          inTipsSection = true;
          if (currentDay) { result.days.push(currentDay); currentDay = null; }
          continue;
        }

        if (inTipsSection) {
          if (/^-\s+/.test(line)) {
            result.tips.push(line.replace(/^-\s+/, ''));
          }
          continue;
        }

        // Check for Phase Header
        const phaseMatch = line.match(/^###\s+📍?\s*(Phase\s*\d+[^(\n]+(?:\([^\)]+\))?)/i);
        if (phaseMatch) {
          if (currentDay) { result.days.push(currentDay); currentDay = null; }
          currentPhase = {
            title: phaseMatch[1].trim(),
            desc: ''
          };
          if (lines[i + 1] && lines[i + 1].trim().startsWith('*')) {
            currentPhase.desc = lines[i + 1].trim().replace(/^\*|\*$/g, '');
          }
          result.phases.push(currentPhase);
          continue;
        }

        // Check for Day Header
        const dayMatch = line.match(/^(?:#{3,4}\s*Day\s*(\d+)\s*[:\-–]\s*([^\n]+)|\*\*Day\s*(\d+)\s*[:\-–]\s*([^\n*]+)\*\*)/i);
        if (dayMatch) {
          if (currentDay) result.days.push(currentDay);
          const dayNum = parseInt(dayMatch[1] || dayMatch[3]);
          const rawTitle = (dayMatch[2] || dayMatch[4]).trim();
          
          let landmarkName = rawTitle;
          let zone = '';
          const zoneMatch = rawTitle.match(/^(.+?)\s*\(([^)]+)\)$/);
          if (zoneMatch) {
            landmarkName = zoneMatch[1].trim();
            zone = zoneMatch[2].trim();
          }

          currentDay = {
            day: dayNum,
            rawTitle,
            landmarkName,
            zone,
            phaseIdx: result.phases.length > 0 ? result.phases.length - 1 : 0,
            morning: '',
            afternoon: '',
            evening: '',
            hack: '',
            budget: ''
          };
          continue;
        }

        // Inside day body
        if (currentDay) {
          if (/^-\s*☀️|Morning/i.test(line)) {
            currentDay.morning = line.replace(/^-\s*☀️\s*(\*\*Morning Exploration:\*\*|\*\*Morning:\*\*|\s*)?/i, '').trim();
          } else if (/^-\s*🌤️|Afternoon/i.test(line)) {
            currentDay.afternoon = line.replace(/^-\s*🌤️\s*(\*\*Afternoon Local Vibe & Eatery:\*\*|\*\*Afternoon:\*\*|\s*)?/i, '').trim();
          } else if (/^-\s*🌙|Evening/i.test(line)) {
            currentDay.evening = line.replace(/^-\s*🌙\s*(\*\*Evening Social & Sunset:\*\*|\*\*Evening:\*\*|\s*)?/i, '').trim();
          } else if (/^-\s*💡|Hack|Student Tip|Traveler Pro Tip/i.test(line)) {
            currentDay.hack = line.replace(/^-\s*💡\s*(\*\*Student Insider Hack:\*\*|\*\*Student Tip:\*\*|\s*)?/i, '').trim();
          } else if (/^-\s*💰|Daily Target Budget/i.test(line)) {
            currentDay.budget = line.replace(/^-\s*💰\s*(\*\*Daily Target Budget:\*\*|\*\*Target Budget:\*\*|\s*)?/i, '').trim();
          }
        }
      }

      if (currentDay) result.days.push(currentDay);

      return result;
    }

    function renderDayCard(d) {
      const isStudent = (currentTrip && currentTrip.trip_summary && currentTrip.trip_summary.student_mode !== false);
      const safeName = escapeHtml(d.landmarkName);
      const safeZone = escapeHtml(d.zone);
      let safeMorning = escapeHtml(d.morning);
      let safeAfternoon = escapeHtml(d.afternoon);
      let safeEvening = escapeHtml(d.evening);
      let safeHack = escapeHtml(d.hack);
      const safeBudget = escapeHtml(d.budget);

      // Cleanse student specific keywords if in standard traveler mode
      if (!isStudent) {
        safeMorning = safeMorning
          .replace(/Flash your student ID card at the entry gate for 30% to 50% concession tickets\./gi, 'Pre-book skip-the-line admissions online for effortless priority entry.')
          .replace(/indie backpacker/gi, 'panoramic boutique');

        safeEvening = safeEvening
          .replace(/indie backpacker rooftop cafe/gi, 'scenic rooftop lounge')
          .replace(/communal hostel lounge/gi, 'serene terrace lounge');

        if (safeHack) {
          safeHack = safeHack
            .replace(/Carry a refillable water bottle and flash your student ID card at ticket counters for instant 30% to 50% concession discounts\./gi, 'Reserve priority admission tickets online 48 hours in advance to bypass main ticketing queues.')
            .replace(/Take shared local transit or split a shared cab from the main stand for a fraction of private taxi rates\. Keep local small change handy for vendors\./gi, 'Arrange dedicated private cabs or premium express transit for comfortable, efficient travel between sights.')
            .replace(/Check local transit timetables with your hostel reception the night before to catch early morning departures and beat tour crowds\./gi, 'Consult your hotel concierge for recommended excursion departure times to experience viewpoints at optimal lighting.')
            .replace(/Eat where local university students eat; follow the crowds to backstreet family-run kitchens for 50% cheaper authentic regional meals\./gi, 'Explore celebrated neighborhood family-run kitchens and historic culinary spots for authentic regional flavors.')
            .replace(/student identity card \(ISIC\)/gi, 'verified priority transit pass')
            .replace(/student discounts?/gi, 'pre-booked priority rates')
            .replace(/hostel/gi, 'hotel')
            .replace(/student/gi, 'traveler');
        }
      }

      let budgetMain = safeBudget;
      let budgetDetail = '';
      if (safeBudget.includes('(')) {
        const parts = safeBudget.split('(');
        budgetMain = parts[0].trim();
        budgetDetail = '(' + parts.slice(1).join('(');
      }

      const safeJsName = d.landmarkName.replace(/'/g, "\'");

      let hackBoxHtml = '';
      if (safeHack) {
        if (isStudent) {
          hackBoxHtml = `
            <div class="p-3 rounded-xl bg-amberAccent/10 border border-amberAccent/20 text-amberAccent/90 flex items-start gap-2.5 tip-box-student shadow-sm">
              <span class="text-base leading-none select-none">💡</span>
              <div class="min-w-0"><strong class="text-amberAccent font-bold">Student Insider Hack:</strong> <span class="text-gray-200 text-xs">${safeHack}</span></div>
            </div>`;
        } else {
          hackBoxHtml = `
            <div class="p-3 rounded-xl bg-sky-500/10 border border-sky-500/20 text-sky-300 flex items-start gap-2.5 tip-box-traveler shadow-sm">
              <span class="text-base leading-none select-none">✨</span>
              <div class="min-w-0"><strong class="text-sky-400 font-bold">Traveler Pro Tip:</strong> <span class="text-gray-200 text-xs">${safeHack}</span></div>
            </div>`;
        }
      }

      return `
      <div class="day-card rounded-2xl p-4 sm:p-5 transition space-y-3 relative shadow-sm" id="day-card-${d.day}" data-day="${d.day}" data-phase="${d.phaseIdx}">
        <div class="flex items-center justify-between gap-3 cursor-pointer select-none" onclick="toggleDayCard(${d.day})">
          <div class="flex items-center gap-3 min-w-0">
            <span class="px-2.5 py-1 rounded-xl bg-coralPrimary/20 text-coralPrimary border border-coralPrimary/30 font-extrabold text-xs whitespace-nowrap">
              Day ${d.day}
            </span>
            <div class="min-w-0">
              <h4 class="text-sm sm:text-base font-bold text-white truncate">${safeName}</h4>
              <span class="text-[11px] text-gray-400 flex items-center gap-1.5 truncate">
                ${safeZone ? `<span>📍 ${safeZone}</span>` : ''}
                ${budgetMain ? `<span class="text-amberAccent font-semibold">• ${budgetMain}</span>` : ''}
              </span>
            </div>
          </div>
          <div class="flex items-center gap-2 whitespace-nowrap">
            <button type="button" onclick="event.stopPropagation(); focusDayMarker(${d.day}, '${safeJsName}');" class="px-2.5 py-1 rounded-xl bg-cyanAccent/15 hover:bg-cyanAccent/30 text-cyanAccent border border-cyanAccent/30 text-xs font-bold transition flex items-center gap-1 shadow-sm" title="Locate on Map">
              <span>📍 Map</span>
            </button>
            <span id="chevron-${d.day}" class="chevron-icon text-gray-400 text-xs">▼</span>
          </div>
        </div>
        <div id="body-${d.day}" class="day-card-body pt-2 space-y-2.5 text-xs text-gray-300 border-t border-white/5">
          ${safeMorning ? `<div class="flex items-start gap-2.5 p-2 rounded-xl bg-white/[0.02]"><span class="text-base leading-none select-none">☀️</span><div class="min-w-0"><strong class="text-white">Morning:</strong> ${safeMorning}</div></div>` : ''}
          ${safeAfternoon ? `<div class="flex items-start gap-2.5 p-2 rounded-xl bg-white/[0.02]"><span class="text-base leading-none select-none">🌤️</span><div class="min-w-0"><strong class="text-white">Afternoon:</strong> ${safeAfternoon}</div></div>` : ''}
          ${safeEvening ? `<div class="flex items-start gap-2.5 p-2 rounded-xl bg-white/[0.02]"><span class="text-base leading-none select-none">🌙</span><div class="min-w-0"><strong class="text-white">Evening:</strong> ${safeEvening}</div></div>` : ''}
          ${hackBoxHtml}
          ${safeBudget ? `<div class="flex items-center justify-between pt-1 text-[11px] text-gray-400"><span class="text-emeraldAccent font-semibold">💰 Target: ${budgetMain}</span><span class="text-gray-500 text-[10px]">${budgetDetail}</span></div>` : ''}
        </div>
      </div>`;
    }

    window.currentItineraryPhase = 'all';
    window.totalPhasesCount = 0;

    function renderItineraryBlueprint(data) {
      if (!data) return;
      const rawMd = data.itinerary || '';

      // 1. Render safe markdown into document view
      const docEl = document.getElementById('itineraryView');
      if (docEl) {
        docEl.innerHTML = safeMarkdown(rawMd);
      }

      // 2. Parse Markdown
      const parsed = parseItineraryMarkdown(rawMd);
      const daysCount = parsed.days.length || (data.trip_summary ? data.trip_summary.days : (data.days || 3));
      const markersCount = (data.markers ? data.markers.length : 0);
      const destination = (data.trip_summary ? data.trip_summary.destination : '') || (document.getElementById('plannerDest') ? document.getElementById('plannerDest').value : '');

      // Update Student Mode Button on Blueprint
      const isStudentMode = (data.trip_summary ? data.trip_summary.student_mode !== false : true);
      const studentBtn = document.getElementById('itineraryStudentModeBtn');
      const studentIcon = document.getElementById('itineraryStudentModeIcon');
      const studentText = document.getElementById('itineraryStudentModeText');
      const searchInputEl = document.getElementById('itinerarySearchInput');

      if (studentBtn) {
        if (isStudentMode) {
          studentBtn.className = 'px-3.5 py-1.5 rounded-xl text-xs font-extrabold flex items-center gap-1.5 border transition shadow-sm bg-emerald-500/15 hover:bg-emerald-500/25 text-emerald-400 border-emerald-500/30';
          if (studentIcon) studentIcon.innerText = '🎓';
          if (studentText) studentText.innerText = 'Student Mode: ON';
        } else {
          studentBtn.className = 'px-3.5 py-1.5 rounded-xl text-xs font-extrabold flex items-center gap-1.5 border transition shadow-sm bg-blue-500/15 hover:bg-blue-500/25 text-blue-400 border-blue-500/30';
          if (studentIcon) studentIcon.innerText = '✨';
          if (studentText) studentText.innerText = 'Traveler Mode (Normal)';
        }
      }

      if (searchInputEl) {
        searchInputEl.placeholder = isStudentMode ? 'Search days, landmarks, dishes, student hacks...' : 'Search days, landmarks, activities, local tips...';
      }

      // 3. Update Metrics Ribbon
      const metricDays = document.getElementById('metricDays');
      if (metricDays) metricDays.innerText = `${daysCount} Days`;

      const metricPins = document.getElementById('metricPins');
      if (metricPins) metricPins.innerText = `${markersCount} Live GPS Pins`;

      const metricBudget = document.getElementById('metricBudget');
      if (metricBudget) {
        metricBudget.innerText = parsed.budgetSummary || (data.trip_summary ? `${data.trip_summary.budget_level}` : 'Custom Tier');
      }

      const metricPhases = document.getElementById('metricPhases');
      if (metricPhases) {
        window.totalPhasesCount = parsed.phases.length;
        metricPhases.innerText = parsed.phases.length > 1 ? `${parsed.phases.length} Regional Circuits` : 'Direct Itinerary';
      }

      const mainHeading = document.getElementById('itineraryMainHeading');
      if (mainHeading && destination) {
        mainHeading.innerText = `${destination} — ${daysCount} Days Blueprint`;
      }

      // 4. Render Phase Navigation Pills
      const phaseNavContainer = document.getElementById('itineraryPhaseNavContainer');
      const phasePillsContainer = document.getElementById('itineraryPhasePills');
      if (parsed.phases.length > 1 && phasePillsContainer && phaseNavContainer) {
        phaseNavContainer.classList.remove('hidden');
        let pillsHtml = `
          <button type="button" onclick="filterItineraryPhase('all')" data-phase="all" class="phase-pill-btn active px-3.5 py-1.5 rounded-full text-xs font-bold border border-white/15 bg-white/10 text-white flex items-center gap-1.5 shadow-sm">
            <span>✨ All Days (${daysCount})</span>
          </button>
        `;
        parsed.phases.forEach((ph, pIdx) => {
          const daysInPhase = parsed.days.filter(d => d.phaseIdx === pIdx).length;
          let shortTitle = ph.title.replace(/^Phase\s*\d+\s*:\s*/i, '');
          if (shortTitle.length > 28) shortTitle = shortTitle.substring(0, 26) + '...';
          pillsHtml += `
            <button type="button" onclick="filterItineraryPhase(${pIdx})" data-phase="${pIdx}" class="phase-pill-btn px-3.5 py-1.5 rounded-full text-xs font-bold border border-white/15 bg-white/5 hover:bg-white/10 text-gray-300 flex items-center gap-1.5 shadow-sm" title="${ph.title}">
              <span>P${pIdx + 1}: ${shortTitle} (${daysInPhase})</span>
            </button>
          `;
        });
        phasePillsContainer.innerHTML = pillsHtml;
      } else if (phaseNavContainer) {
        phaseNavContainer.classList.add('hidden');
      }

      // 5. Render Day Cards with Phase Headers
      const cardsView = document.getElementById('itineraryCardsView');
      if (cardsView) {
        if (parsed.days.length > 0) {
          let cardsHtml = '';
          let lastPhaseIdx = -1;

          parsed.days.forEach(d => {
            if (d.phaseIdx !== lastPhaseIdx && parsed.phases[d.phaseIdx]) {
              lastPhaseIdx = d.phaseIdx;
              const ph = parsed.phases[d.phaseIdx];
              cardsHtml += `
                <div class="phase-divider-header pt-4 pb-1 border-b border-white/10" data-phase="${d.phaseIdx}">
                  <div class="flex items-center gap-2">
                    <span class="text-xs px-2.5 py-0.5 rounded-full bg-cyanAccent/20 text-cyanAccent font-extrabold border border-cyanAccent/30 uppercase tracking-wider">
                      Circuit ${d.phaseIdx + 1}
                    </span>
                    <h4 class="text-sm sm:text-base font-extrabold text-white">${ph.title}</h4>
                  </div>
                  ${ph.desc ? `<p class="text-xs text-gray-400 mt-1 italic">${ph.desc}</p>` : ''}
                </div>
              `;
            }
            cardsHtml += renderDayCard(d);
          });

          cardsView.innerHTML = cardsHtml;
          setItineraryViewMode('cards');
        } else {
          setItineraryViewMode('doc');
        }
      }

      // 6. Render Tips Card
      const tipsCard = document.getElementById('itineraryTipsCard');
      const tipsContent = document.getElementById('itineraryTipsContent');
      if (tipsCard && tipsContent) {
        if (parsed.tips.length > 0) {
          tipsContent.innerHTML = parsed.tips.map(tip => `
            <div class="p-3 rounded-xl bg-white/[0.02] border border-white/5 flex items-start gap-2">
              <span class="text-coralPrimary text-sm leading-none">✓</span>
              <div>${tip}</div>
            </div>
          `).join('');
          tipsCard.classList.remove('hidden');
        } else {
          tipsCard.classList.add('hidden');
        }
      }

      // 7. Reset filters
      window.currentItineraryPhase = 'all';
      const searchInput = document.getElementById('itinerarySearchInput');
      if (searchInput) searchInput.value = '';
      filterItineraryCards();
    }

    function setItineraryViewMode(mode) {
      const cardsView = document.getElementById('itineraryCardsView');
      const docView = document.getElementById('itineraryDocView');
      const toolbar = document.getElementById('itineraryCardsToolbar');
      const phaseNav = document.getElementById('itineraryPhaseNavContainer');
      const tipsCard = document.getElementById('itineraryTipsCard');
      const btnCards = document.getElementById('viewModeCardsBtn');
      const btnDoc = document.getElementById('viewModeDocBtn');

      if (mode === 'cards') {
        if (cardsView) cardsView.classList.remove('hidden');
        if (toolbar) toolbar.classList.remove('hidden');
        if (phaseNav && window.totalPhasesCount > 1) phaseNav.classList.remove('hidden');
        if (tipsCard) tipsCard.classList.remove('hidden');
        if (docView) docView.classList.add('hidden');

        if (btnCards) {
          btnCards.className = 'px-3 py-1.5 rounded-lg font-bold transition flex items-center gap-1.5 bg-coralPrimary text-white shadow-sm';
        }
        if (btnDoc) {
          btnDoc.className = 'px-3 py-1.5 rounded-lg font-bold transition flex items-center gap-1.5 text-gray-400 hover:text-white';
        }
      } else {
        if (cardsView) cardsView.classList.add('hidden');
        if (toolbar) toolbar.classList.add('hidden');
        if (phaseNav) phaseNav.classList.add('hidden');
        if (tipsCard) tipsCard.classList.add('hidden');
        if (docView) docView.classList.remove('hidden');

        if (btnCards) {
          btnCards.className = 'px-3 py-1.5 rounded-lg font-bold transition flex items-center gap-1.5 text-gray-400 hover:text-white';
        }
        if (btnDoc) {
          btnDoc.className = 'px-3 py-1.5 rounded-lg font-bold transition flex items-center gap-1.5 bg-coralPrimary text-white shadow-sm';
        }
      }
    }

    function toggleDayCard(dayNum) {
      const body = document.getElementById('body-' + dayNum);
      const chevron = document.getElementById('chevron-' + dayNum);
      if (!body) return;
      const isCollapsed = body.classList.contains('collapsed');
      if (isCollapsed) {
        body.classList.remove('collapsed');
        if (chevron) chevron.style.transform = 'rotate(0deg)';
      } else {
        body.classList.add('collapsed');
        if (chevron) chevron.style.transform = 'rotate(-90deg)';
      }
    }

    function toggleAllDayCards(expand) {
      document.querySelectorAll('.day-card-body').forEach(b => {
        b.classList.toggle('collapsed', !expand);
      });
      document.querySelectorAll('[id^="chevron-"]').forEach(ch => {
        ch.style.transform = expand ? 'rotate(0deg)' : 'rotate(-90deg)';
      });
      showToast(expand ? 'Expanded all day cards' : 'Collapsed all day cards', 'info', 1500);
    }

    function filterItineraryPhase(phaseIdx) {
      window.currentItineraryPhase = phaseIdx;

      document.querySelectorAll('.phase-pill-btn').forEach(btn => {
        const p = btn.getAttribute('data-phase');
        const isActive = String(p) === String(phaseIdx);
        btn.classList.toggle('active', isActive);
      });

      const phaseCountLabel = document.getElementById('activePhaseCount');
      if (phaseCountLabel) {
        phaseCountLabel.innerText = phaseIdx === 'all' ? 'Showing All Phases' : `Showing Phase ${parseInt(phaseIdx) + 1}`;
      }

      filterItineraryCards();
    }

    function filterItineraryCards() {
      const input = document.getElementById('itinerarySearchInput');
      const query = input ? input.value.toLowerCase().trim() : '';
      const clearBtn = document.getElementById('itinerarySearchClear');
      if (clearBtn) {
        clearBtn.classList.toggle('hidden', !query);
      }

      const activePhase = window.currentItineraryPhase || 'all';
      const cards = document.querySelectorAll('.day-card');
      const phaseHeaders = document.querySelectorAll('.phase-divider-header');
      let visibleCount = 0;

      cards.forEach(card => {
        const cardPhase = card.getAttribute('data-phase');
        const text = card.innerText.toLowerCase();

        const matchesPhase = (activePhase === 'all' || cardPhase === String(activePhase));
        const matchesSearch = (!query || text.includes(query));

        if (matchesPhase && matchesSearch) {
          card.classList.remove('hidden');
          visibleCount++;
        } else {
          card.classList.add('hidden');
        }
      });

      phaseHeaders.forEach(hdr => {
        const hdrPhase = hdr.getAttribute('data-phase');
        if (activePhase === 'all') {
          hdr.classList.remove('hidden');
        } else if (hdrPhase === String(activePhase)) {
          hdr.classList.remove('hidden');
        } else {
          hdr.classList.add('hidden');
        }
      });

      const countBadge = document.getElementById('itineraryCardsCountBadge');
      if (countBadge) {
        countBadge.innerText = `Showing ${visibleCount} of ${cards.length} Days`;
      }
    }

    function clearItinerarySearch() {
      const input = document.getElementById('itinerarySearchInput');
      if (input) input.value = '';
      filterItineraryCards();
    }

    function focusDayMarker(dayNum, landmarkName) {
      const mapCard = document.getElementById('plannerMapCard');
      if (mapCard) {
        mapCard.scrollIntoView({ behavior: 'smooth', block: 'center' });
      }

      let marker = window.leafletMarkersByDay ? window.leafletMarkersByDay[dayNum] : null;
      if (!marker && landmarkName && window.leafletMarkersByName) {
        const cleanKey = landmarkName.toLowerCase().replace(/[^a-z0-9]/g, '');
        for (const k in window.leafletMarkersByName) {
          if (k.includes(cleanKey) || cleanKey.includes(k)) {
            marker = window.leafletMarkersByName[k];
            break;
          }
        }
      }

      if (marker && mapInstance) {
        setTimeout(() => {
          if (markersLayer && typeof markersLayer.zoomToShowLayer === 'function') {
            markersLayer.zoomToShowLayer(marker, () => {
              mapInstance.panTo(marker.getLatLng(), { animate: true });
              marker.openPopup();
            });
          } else {
            mapInstance.setView(marker.getLatLng(), 14, { animate: true });
            marker.openPopup();
          }
        }, 350);
      } else {
        showToast(`Day ${dayNum} pin plotted in destination overview!`, 'info', 2000);
      }
    }

    function highlightItineraryDay(dayNum, landmarkName) {
      setItineraryViewMode('cards');

      if (window.currentItineraryPhase !== 'all') {
        filterItineraryPhase('all');
      }
      const searchInput = document.getElementById('itinerarySearchInput');
      if (searchInput && searchInput.value) {
        searchInput.value = '';
        clearItinerarySearch();
      }

      const card = document.getElementById('day-card-' + dayNum);
      if (card) {
        const body = document.getElementById('body-' + dayNum);
        const chevron = document.getElementById('chevron-' + dayNum);
        if (body && (body.classList.contains('collapsed') || body.classList.contains('hidden'))) {
          body.classList.remove('collapsed', 'hidden');
          if (chevron) chevron.style.transform = 'rotate(0deg)';
        }

        card.scrollIntoView({ behavior: 'smooth', block: 'center' });
        card.classList.add('day-card-highlight');
        setTimeout(() => card.classList.remove('day-card-highlight'), 2200);
        showToast(`Jumped to Day ${dayNum}: ${landmarkName || ''}`, 'success', 2000);
      }
    }

    function resetMapPlaceholder() {
      const placeholder = document.getElementById('mapPlaceholder');
      const mapEl = document.getElementById('map');
      const legend = document.getElementById('mapLegend');
      if (placeholder) placeholder.classList.remove('hidden');
      if (mapEl) mapEl.classList.add('hidden');
      if (legend) legend.classList.add('hidden');

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

    let isPdfLibLoading = false;
    function loadPdfEngine(callback) {
      if (typeof html2pdf !== 'undefined') {
        callback();
        return;
      }
      if (isPdfLibLoading) {
        showToast('PDF engine is initializing, please wait a moment...', 'info');
        return;
      }
      isPdfLibLoading = true;
      showToast('Loading PDF engine on demand...', 'info', 2500);
      const s = document.createElement('script');
      s.src = 'https://cdnjs.cloudflare.com/ajax/libs/html2pdf.js/0.10.1/html2pdf.bundle.min.js';
      s.async = true;
      s.onload = () => {
        isPdfLibLoading = false;
        callback();
      };
      s.onerror = () => {
        isPdfLibLoading = false;
        showToast('Failed to load PDF library. Please check your connection.', 'error');
      };
      document.head.appendChild(s);
    }

    function buildPrintablePdfDocument(tripData) {
      if (!tripData) return '';
      const isStudent = tripData.trip_summary ? tripData.trip_summary.student_mode !== false : true;
      const destination = (tripData.trip_summary && tripData.trip_summary.destination) ? tripData.trip_summary.destination : 'Your Destination';
      const daysCount = (tripData.trip_summary && tripData.trip_summary.days) ? tripData.trip_summary.days : (tripData.days || 3);
      const markersCount = tripData.markers ? tripData.markers.length : 0;
      const pace = (tripData.trip_summary && tripData.trip_summary.travel_pace) ? tripData.trip_summary.travel_pace : 'Balanced';

      const rawMd = tripData.itinerary || '';
      const parsed = parseItineraryMarkdown(rawMd);
      const budgetEstimate = parsed.budgetSummary || (tripData.trip_summary ? `${tripData.trip_summary.budget_level} Tier` : 'Estimated Budget');

      let daysHtml = '';
      let lastPhaseIdx = -1;

      if (parsed.days && parsed.days.length > 0) {
        parsed.days.forEach(d => {
          if (d.phaseIdx !== lastPhaseIdx && parsed.phases && parsed.phases[d.phaseIdx]) {
            lastPhaseIdx = d.phaseIdx;
            const ph = parsed.phases[d.phaseIdx];
            daysHtml += `
              <div class="pdf-phase-header" style="background:#f1f5f9; border-left: 4px solid #0284c7; border-radius: 6px; padding: 8px 12px; margin-top: 16px; margin-bottom: 10px; page-break-inside: avoid; break-inside: avoid;">
                <div style="font-size: 12px; font-weight: 800; color: #0f172a;">
                  🧭 Circuit ${d.phaseIdx + 1}: ${escapeHtml(ph.title)}
                </div>
                ${ph.desc ? `<div style="font-size: 10px; color: #475569; font-style: italic; margin-top: 2px;">${escapeHtml(ph.desc)}</div>` : ''}
              </div>
            `;
          }

          const safeName = escapeHtml(d.landmarkName);
          const safeZone = escapeHtml(d.zone);
          const safeMorning = escapeHtml(d.morning);
          const safeAfternoon = escapeHtml(d.afternoon);
          const safeEvening = escapeHtml(d.evening);
          const safeHack = escapeHtml(d.hack);
          const safeBudget = escapeHtml(d.budget);

          daysHtml += `
            <div class="pdf-day-card" style="background: #ffffff; border: 1px solid #e2e8f0; border-left: 4px solid #FF6B4A; border-radius: 8px; padding: 11px 14px; margin-bottom: 10px; page-break-inside: avoid; break-inside: avoid; font-family: inherit;">
              <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px; border-bottom: 1px solid #f1f5f9; padding-bottom: 5px;">
                <div style="display: flex; align-items: center; gap: 8px;">
                  <span style="background: #FF6B4A; color: #ffffff; font-weight: 800; font-size: 10px; padding: 2px 7px; border-radius: 4px; text-transform: uppercase;">
                    Day ${d.day}
                  </span>
                  <span style="font-weight: 800; font-size: 12.5px; color: #0f172a;">
                    ${safeName}
                  </span>
                  ${safeZone ? `<span style="font-size: 10.5px; color: #64748b;">(📍 ${safeZone})</span>` : ''}
                </div>
                ${safeBudget ? `
                <span style="font-size: 10px; font-weight: 700; color: #059669; background: #ecfdf5; border: 1px solid #d1fae5; padding: 2px 6px; border-radius: 4px;">
                  ${safeBudget.split('(')[0].trim()}
                </span>` : ''}
              </div>

              <div style="font-size: 10.5px; color: #334155; line-height: 1.45; display: flex; flex-direction: column; gap: 3.5px;">
                ${safeMorning ? `<div><strong>☀️ Morning:</strong> ${safeMorning}</div>` : ''}
                ${safeAfternoon ? `<div><strong>🌤️ Afternoon:</strong> ${safeAfternoon}</div>` : ''}
                ${safeEvening ? `<div><strong>🌙 Evening:</strong> ${safeEvening}</div>` : ''}
                ${safeHack ? `
                <div style="background: #fffbeb; border: 1px solid #fef3c7; padding: 5px 8px; border-radius: 5px; color: #92400e; margin-top: 2px;">
                  <strong>💡 ${isStudent ? 'Student Hack' : 'Traveler Pro Tip'}:</strong> ${safeHack}
                </div>` : ''}
              </div>
            </div>
          `;
        });
      }

      let tipsBoxHtml = '';
      if (parsed.tips && parsed.tips.length > 0) {
        tipsBoxHtml = `
          <div class="pdf-tips-box" style="background: #f8fafc; border: 1px solid #cbd5e1; border-radius: 8px; padding: 12px 14px; margin-top: 16px; margin-bottom: 12px; page-break-inside: avoid; break-inside: avoid;">
            <div style="font-size: 11.5px; font-weight: 800; color: #0f172a; margin-bottom: 8px;">
              ${isStudent ? '🎒 Essential Student Travel Hacks & Guidance' : '🗺️ Essential Traveler Guidance & Local Tips'}
            </div>
            <div style="font-size: 10.5px; color: #334155; line-height: 1.5; display: flex; flex-direction: column; gap: 4px;">
              ${parsed.tips.map(t => `<div>• ${escapeHtml(t)}</div>`).join('')}
            </div>
          </div>
        `;
      }

      return `
      <div class="roamai-pdf-doc" style="background:#ffffff; color:#1e293b; font-family:-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; padding:20px 24px; line-height:1.5; width:760px; margin:0 auto; box-sizing:border-box;">
        <!-- Brand Header -->
        <div style="border-bottom: 2.5px solid #FF6B4A; padding-bottom: 12px; margin-bottom: 16px; display: flex; justify-content: space-between; align-items: flex-start;">
          <div>
            <div style="font-size: 10px; font-weight: 800; letter-spacing: 1.5px; color: #FF6B4A; text-transform: uppercase; margin-bottom: 2px;">
              RoamAI Travel Architect Blueprint
            </div>
            <h1 style="font-size: 20px; font-weight: 900; color: #0f172a; margin: 0; line-height: 1.2;">
              ${escapeHtml(destination)}
            </h1>
            <div style="font-size: 12px; font-weight: 600; color: #64748b; margin-top: 3px;">
              ${daysCount}-Day Comprehensive Itinerary • ${isStudent ? '🎒 Student Explorer Edition' : '✨ Curated Traveler Edition'}
            </div>
          </div>
          <div style="text-align: right;">
            <span style="display: inline-block; padding: 3px 8px; background: #fff1ee; color: #FF6B4A; font-weight: 800; font-size: 10.5px; border-radius: 6px; border: 1px solid #fed7cc;">
              ${escapeHtml(budgetEstimate)}
            </span>
            <div style="font-size: 9.5px; color: #94a3b8; margin-top: 4px;">
              Generated: ${new Date().toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}
            </div>
          </div>
        </div>

        <!-- Trip Matrix Box -->
        <div class="pdf-summary-box" style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 10px 12px; margin-bottom: 16px; page-break-inside: avoid; break-inside: avoid;">
          <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 8px; font-size: 10.5px;">
            <div style="background: #ffffff; border: 1px solid #e2e8f0; border-radius: 6px; padding: 6px 8px;">
              <div style="color: #64748b; font-size: 9.5px;">📅 Duration</div>
              <div style="font-weight: 800; color: #0f172a; font-size: 11.5px;">${daysCount} Days</div>
            </div>
            <div style="background: #ffffff; border: 1px solid #e2e8f0; border-radius: 6px; padding: 6px 8px;">
              <div style="color: #64748b; font-size: 9.5px;">📍 Landmarks</div>
              <div style="font-weight: 800; color: #0284c7; font-size: 11.5px;">${markersCount} GPS Pins</div>
            </div>
            <div style="background: #ffffff; border: 1px solid #e2e8f0; border-radius: 6px; padding: 6px 8px;">
              <div style="color: #64748b; font-size: 9.5px;">💰 Budget</div>
              <div style="font-weight: 800; color: #d97706; font-size: 11.5px;">${escapeHtml(budgetEstimate)}</div>
            </div>
            <div style="background: #ffffff; border: 1px solid #e2e8f0; border-radius: 6px; padding: 6px 8px;">
              <div style="color: #64748b; font-size: 9.5px;">🧭 Pace</div>
              <div style="font-weight: 800; color: #059669; font-size: 11.5px;">${escapeHtml(pace)} Pace</div>
            </div>
          </div>
        </div>

        <!-- Day by Day Itinerary -->
        <div>
          ${daysHtml}
        </div>

        <!-- Tips Box -->
        ${tipsBoxHtml}

        <!-- Footer -->
        <div style="border-top: 1px solid #e2e8f0; padding-top: 10px; margin-top: 16px; font-size: 9px; color: #94a3b8; text-align: center; page-break-inside: avoid; break-inside: avoid;">
          Generated with RoamAI Travel Architect • Your Smart AI Companion • Safe Travels!
        </div>
      </div>
      `;
    }

    function downloadTripPDF() {
      if (!currentTrip) return;
      loadPdfEngine(() => {
        showToast('Generating high-resolution print-ready PDF itinerary...', 'info', 3000);
        const container = document.createElement('div');
        container.style.position = 'fixed';
        container.style.left = '-9999px';
        container.style.top = '0';
        container.style.width = '794px';
        container.style.background = '#ffffff';
        container.style.zIndex = '-9999';
        container.innerHTML = buildPrintablePdfDocument(currentTrip);
        document.body.appendChild(container);

        const safeDest = (currentTrip.trip_summary?.destination || 'Destination').replace(/[^a-zA-Z0-9_\-]/g, '_');
        const opt = {
          margin: [10, 10, 10, 10],
          filename: `RoamAI_${safeDest}_Itinerary.pdf`,
          image: { type: 'jpeg', quality: 0.98 },
          html2canvas: { scale: 2, useCORS: true, logging: false, letterRendering: true },
          jsPDF: { unit: 'mm', format: 'a4', orientation: 'portrait' },
          pagebreak: { mode: ['avoid-all', 'css', 'legacy'] }
        };

        html2pdf().set(opt).from(container).save().then(() => {
          if (document.body.contains(container)) document.body.removeChild(container);
          showToast('PDF downloaded successfully!', 'success');
        }).catch(err => {
          if (document.body.contains(container)) document.body.removeChild(container);
          console.error('PDF export error:', err);
          showToast('Failed to export PDF. Please try again.', 'error');
        });
      });
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
        const mobCountEl = document.getElementById('mobSavedCount');
        if (mobCountEl) mobCountEl.innerText = trips.length;
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
        student_mode: currentTrip.trip_summary ? (currentTrip.trip_summary.student_mode !== false) : true,
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

      renderItineraryBlueprint(trip);
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

      loadPdfEngine(() => {
        showToast('Preparing high-resolution PDF export...', 'info', 3000);
        const tripData = {
          trip_summary: {
            destination: trip.destination,
            days: trip.days,
            student_mode: trip.student_mode !== undefined ? trip.student_mode : true
          },
          itinerary: trip.itinerary,
          markers: trip.markers || [],
          destination_coords: trip.destination_coords || null
        };

        const container = document.createElement('div');
        container.style.position = 'fixed';
        container.style.left = '-9999px';
        container.style.top = '0';
        container.style.width = '794px';
        container.style.background = '#ffffff';
        container.style.zIndex = '-9999';
        container.innerHTML = buildPrintablePdfDocument(tripData);
        document.body.appendChild(container);

        const safeDest = (trip.destination || 'Trip').replace(/[^a-zA-Z0-9_\-]/g, '_');
        const opt = {
          margin: [10, 10, 10, 10],
          filename: `RoamAI_${safeDest}_Itinerary.pdf`,
          image: { type: 'jpeg', quality: 0.98 },
          html2canvas: { scale: 2, useCORS: true, logging: false, letterRendering: true },
          jsPDF: { unit: 'mm', format: 'a4', orientation: 'portrait' },
          pagebreak: { mode: ['avoid-all', 'css', 'legacy'] }
        };

        html2pdf().set(opt).from(container).save().then(() => {
          if (document.body.contains(container)) document.body.removeChild(container);
          showToast('PDF downloaded successfully!', 'success');
        }).catch(err => {
          if (document.body.contains(container)) document.body.removeChild(container);
          console.error('PDF export error:', err);
          showToast('Failed to export PDF. Please try again.', 'error');
        });
      });
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

    const debouncedCalcBudget = debounce(calcBudget, 20);

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
          class="text-xs px-3.5 py-1.5 rounded-full border transition shrink-0 whitespace-nowrap flex items-center gap-1.5 ${activePackFilter === p.key ? 'bg-gradient-to-r from-coralPrimary to-amberAccent text-white font-bold border-transparent shadow-md' : 'bg-white/5 border-white/10 text-gray-400 hover:text-white hover:border-white/20'}"
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

      const isMobile = window.innerWidth < 768 || ('ontouchstart' in window);

      // Debounce window resize to eliminate layout thrashing
      window.addEventListener('resize', debounce(() => {
        width = canvas.width = window.innerWidth;
        height = canvas.height = window.innerHeight;
      }, 150), { passive: true });

      // Throttle & pause canvas when touch-scrolling on mobile to prioritize main thread for UI
      let isScrolling = false;
      let scrollTimer = null;
      window.addEventListener('scroll', () => {
        if (isMobile) {
          isScrolling = true;
          clearTimeout(scrollTimer);
          scrollTimer = setTimeout(() => {
            isScrolling = false;
          }, 120);
        }
      }, { passive: true });

      // 1. Cruising Airplanes with Contrails (Adaptive for Mobile)
      const planeCount = isMobile ? 3 : 6;
      const planes = [];
      for (let i = 0; i < planeCount; i++) {
        planes.push({
          x: Math.random() * width,
          y: Math.random() * height,
          speed: isMobile ? (Math.random() * 0.6 + 0.5) : (Math.random() * 0.8 + 0.6),
          angle: (Math.random() * Math.PI * 0.6) - 0.3,
          size: isMobile ? (Math.random() * 3 + 11) : (Math.random() * 4 + 12),
          history: [],
          color: i % 2 === 0 ? '#FF5E36' : '#06B6D4'
        });
      }

      // 2. Floating Hot Air Balloons
      const balloons = isMobile ? [
        { x: width * 0.18, y: height * 0.45, vy: -0.20, vx: 0.08, radius: 13, hue: '#FFA000', phase: 0 },
        { x: width * 0.80, y: height * 0.72, vy: -0.16, vx: -0.06, radius: 14, hue: '#FF5E36', phase: 1.5 },
        { x: width * 0.48, y: height * 0.88, vy: -0.22, vx: 0.10, radius: 12, hue: '#06B6D4', phase: 3 }
      ] : [
        { x: width * 0.12, y: height * 0.40, vy: -0.25, vx: 0.12, radius: 13, hue: '#FFA000', phase: 0 },
        { x: width * 0.85, y: height * 0.70, vy: -0.20, vx: -0.08, radius: 15, hue: '#FF5E36', phase: 1.5 },
        { x: width * 0.50, y: height * 0.82, vy: -0.28, vx: 0.10, radius: 12, hue: '#8B5CF6', phase: 3 },
        { x: width * 0.28, y: height * 0.90, vy: -0.22, vx: -0.12, radius: 14, hue: '#06B6D4', phase: 4.5 }
      ];

      // 3. Shimmering Compass Stars & Firefly Embers
      const starCount = isMobile ? 22 : 45;
      const stars = [];
      for (let i = 0; i < starCount; i++) {
        stars.push({
          x: Math.random() * width,
          y: Math.random() * height,
          vx: (Math.random() - 0.5) * (isMobile ? 0.2 : 0.3),
          vy: (Math.random() - 0.5) * (isMobile ? 0.2 : 0.3),
          size: Math.random() * 2 + 1.2,
          isCompass: !isMobile && Math.random() > 0.65,
          color: Math.random() > 0.5 ? 'rgba(255, 160, 0, ' : 'rgba(6, 182, 212, ',
          alpha: Math.random() * 0.5 + 0.3,
          pulse: Math.random() * 0.02 + 0.01
        });
      }

      // 4. Destination Waypoint Radars
      const waypoints = [
        { x: width * 0.20, y: height * 0.25, name: "Tokyo", pulseRadius: 0 },
        { x: width * 0.78, y: height * 0.32, name: "Rome", pulseRadius: 15 },
        { x: width * 0.45, y: height * 0.65, name: "Goa", pulseRadius: 30 }
      ];

      let mouse = { x: null, y: null, ripple: 0 };
      if (!isMobile) {
        window.addEventListener('mousemove', (e) => {
          mouse.x = e.clientX;
          mouse.y = e.clientY;
          mouse.ripple = (mouse.ripple + 1) % 50;
        });
        window.addEventListener('mouseleave', () => {
          mouse.x = null;
          mouse.y = null;
        });
      }

      function drawPlane(p, isLight) {
        ctx.save();
        ctx.translate(p.x, p.y);
        ctx.rotate(p.angle);

        const planeColor = isLight ? (p.color === '#06B6D4' ? '#0284C7' : '#EA580C') : p.color;
        ctx.fillStyle = planeColor;
        if (!isMobile) {
          ctx.shadowColor = isLight ? 'rgba(2, 132, 199, 0.4)' : planeColor;
          ctx.shadowBlur = isLight ? 6 : 10;
        }
        ctx.beginPath();
        ctx.moveTo(p.size * 1.1, 0);
        ctx.lineTo(-p.size * 0.4, p.size * 0.9);
        ctx.lineTo(-p.size * 0.2, p.size * 0.2);
        ctx.lineTo(-p.size * 0.85, p.size * 0.5);
        ctx.lineTo(-p.size * 0.7, 0);
        ctx.lineTo(-p.size * 0.85, -p.size * 0.5);
        ctx.lineTo(-p.size * 0.2, -p.size * 0.2);
        ctx.lineTo(-p.size * 0.4, -p.size * 0.9);
        ctx.closePath();
        ctx.fill();

        ctx.restore();
      }

      function drawBalloon(b, isLight) {
        ctx.save();
        ctx.translate(b.x, b.y);

        ctx.fillStyle = b.hue;
        if (!isMobile) {
          ctx.shadowColor = isLight ? 'rgba(0,0,0,0.2)' : b.hue;
          ctx.shadowBlur = 8;
        }
        ctx.beginPath();
        ctx.arc(0, 0, b.radius, 0, Math.PI, true);
        ctx.quadraticCurveTo(-b.radius * 0.9, b.radius * 1.1, 0, b.radius * 1.4);
        ctx.quadraticCurveTo(b.radius * 0.9, b.radius * 1.1, b.radius, 0);
        ctx.fill();

        ctx.fillStyle = isLight ? '#334155' : 'rgba(255, 255, 255, 0.8)';
        ctx.fillRect(-b.radius * 0.25, b.radius * 1.65, b.radius * 0.5, b.radius * 0.35);

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
        if (!isMobile) {
          ctx.shadowColor = isLight ? 'rgba(217, 119, 6, 0.7)' : starColor + '0.8)';
          ctx.shadowBlur = 6;
        }

        ctx.beginPath();
        const rOuter = s.size * 2.2;
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

      let animRunning = true;
      let lastFrameTime = 0;
      const targetInterval = isMobile ? 33 : 16; // 30fps on mobile (saves 50% CPU/GPU), 60fps on desktop

      document.addEventListener('visibilitychange', () => {
        animRunning = !document.hidden;
        if (animRunning) requestAnimationFrame(animate);
      });

      function animate(now = 0) {
        if (!animRunning) return;

        requestAnimationFrame(animate);

        // Delta-time throttle (smooth 30fps on mobile to keep touch responsive, 60fps on desktop)
        if (now - lastFrameTime < targetInterval) return;
        lastFrameTime = now;

        ctx.clearRect(0, 0, width, height);
        const isLight = document.documentElement.classList.contains('light-theme') || document.body.classList.contains('light-theme');

        // 1. Draw Global Great-Circle Flight Arcs
        ctx.save();
        ctx.setLineDash([8, 14]);
        ctx.lineWidth = isLight ? 1.5 : 1;
        ctx.strokeStyle = isLight ? 'rgba(234, 88, 12, 0.35)' : 'rgba(255, 160, 0, 0.12)';
        ctx.beginPath();
        ctx.moveTo(0, height * 0.3);
        ctx.quadraticCurveTo(width * 0.5, height * 0.1, width, height * 0.45);
        ctx.stroke();

        ctx.strokeStyle = isLight ? 'rgba(2, 132, 199, 0.35)' : 'rgba(6, 182, 212, 0.1)';
        ctx.beginPath();
        ctx.moveTo(0, height * 0.7);
        ctx.quadraticCurveTo(width * 0.4, height * 0.85, width, height * 0.6);
        ctx.stroke();
        ctx.restore();

        // 2. Draw Destination Waypoint Pulses
        waypoints.forEach(wp => {
          wp.pulseRadius = (wp.pulseRadius + 0.3) % 50;
          const pAlpha = (1 - wp.pulseRadius / 50) * (isLight ? 0.6 : 0.35);
          ctx.beginPath();
          ctx.arc(wp.x, wp.y, wp.pulseRadius, 0, Math.PI * 2);
          ctx.strokeStyle = isLight ? `rgba(2, 132, 199, ${pAlpha})` : `rgba(6, 182, 212, ${pAlpha})`;
          ctx.lineWidth = isLight ? 1.5 : 1;
          ctx.stroke();

          ctx.beginPath();
          ctx.arc(wp.x, wp.y, 3, 0, Math.PI * 2);
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

          s.alpha += Math.sin(Date.now() * s.pulse) * 0.006;
          const curAlpha = Math.max(0.25, Math.min(0.9, s.alpha));

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
          b.phase += 0.015;
          b.y += b.vy;
          b.x += b.vx + Math.sin(b.phase) * 0.12;
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

          const maxHistory = isMobile ? 14 : 25;
          p.history.push({ x: p.x, y: p.y });
          if (p.history.length > maxHistory) p.history.shift();

          if (p.history.length > 2) {
            ctx.save();
            ctx.setLineDash([4, 6]);
            ctx.lineWidth = isLight ? 1.5 : 1;
            for (let i = 0; i < p.history.length - 1; i++) {
              const trailAlpha = (i / p.history.length) * (isLight ? 0.6 : 0.35);
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
          if (p.x > width + 50) {
            p.x = -50;
            p.y = Math.random() * height;
            p.history = [];
          }
          if (p.y > height + 50) {
            p.y = -50;
            p.history = [];
          }
          if (p.y < -50) {
            p.y = height + 50;
            p.history = [];
          }

          drawPlane(p, isLight);
        });

        // 6. Interactive Mouse Compass Radar Ring (Desktop only)
        if (!isMobile && mouse.x !== null && mouse.y !== null) {
          ctx.save();
          ctx.beginPath();
          ctx.arc(mouse.x, mouse.y, 40, 0, Math.PI * 2);
          ctx.strokeStyle = isLight ? 'rgba(225, 29, 72, 0.4)' : 'rgba(255, 94, 54, 0.2)';
          ctx.lineWidth = 1;
          ctx.setLineDash([4, 4]);
          ctx.stroke();

          ctx.beginPath();
          ctx.arc(mouse.x, mouse.y, 18, 0, Math.PI * 2);
          ctx.strokeStyle = 'rgba(255, 160, 0, 0.3)';
          ctx.lineWidth = 1;
          ctx.stroke();
          ctx.restore();
        }
      }

      animate();
    }

    document.addEventListener('DOMContentLoaded', () => {
      // 1. Critical first paints: Badge count & Theme Mood & Page Switch
      updateSavedCount();
      initThemeMood();

      // 2. Initialize animated moving travel sky background canvas immediately
      initBackgroundCanvas();

      // 3. Restore saved region (prevent resetting to INR on reload)
      const savedRegion = localStorage.getItem('roamai_selected_region') || 'INR';
      onRegionChange(savedRegion, false);

      // 4. Restore saved active page (prevent automatically resetting to home on reload)
      const hashPage = window.location.hash.replace('#', '');
      const savedPage = hashPage || localStorage.getItem('roamai_active_page') || 'home';
      switchPage(savedPage, false);

      // 5. Restore Trip Architect Form Draft & Active Itinerary (prevents info loss on reload)
      initPlannerDraft();

      // 6. Defer packing checklist and offline vault rendering to idle frames
      const scheduleIdle = window.requestIdleCallback || function(cb) { setTimeout(cb, 16); };
      scheduleIdle(() => {
        renderPacking();
        renderSaved();
      });
    });
  </script>
</body>
</html>"""

@app.api_route("/", methods=["GET", "HEAD"], response_class=HTMLResponse)
def serve_index():
    response = HTMLResponse(content=HTML_CONTENT, status_code=200)
    response.headers["Cache-Control"] = "public, max-age=600, stale-while-revalidate=86400"
    return response

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
