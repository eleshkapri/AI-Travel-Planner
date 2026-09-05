# -*- coding: utf-8 -*-
"""
RoamAI GeoLocation and Knowledge Base Service.
Encapsulates high-performance in-memory coordinate caching,
OSM Nominatim fallback geocoding, and offline fallback itinerary synthesis.
"""
from __future__ import annotations
import re
import math
import threading
from typing import Optional, List, Dict, Tuple, Any
from geopy.geocoders import Nominatim
from core.security import InputSanitizer


class GeoLocationService:
    """
    Object-Oriented Geocoding, Geographic Intelligence, and Fallback Trip Synthesis.
    Encapsulates internal coordinate cache, Nominatim resolution, and landmark catalogs.
    """
    _instance: Optional[GeoLocationService] = None
    _lock: threading.Lock = threading.Lock()

    def __new__(cls) -> GeoLocationService:
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(GeoLocationService, cls).__new__(cls)
                cls._instance._initialize()
            return cls._instance

    @classmethod
    def get_instance(cls) -> GeoLocationService:
        if cls._instance is None:
            return cls()
        return cls._instance

    def _initialize(self) -> None:
        """Initialize geolocator, caches, and destination knowledge base."""
        try:
            self._geolocator = Nominatim(user_agent="roamai_travel_architect_v24_oop")
        except Exception:
            self._geolocator = None

        self._aliases: Dict[str, List[str]] = {
            "goa": ["goa"],
            "manali": ["manali", "kasol", "kullu"],
            "jaipur": ["jaipur", "udaipur", "jodhpur", "rajasthan"],
            "rishikesh": ["rishikesh", "haridwar", "dehradun"],
            "varanasi": ["varanasi", "kashi", "banaras"],
            "leh": ["leh", "ladakh"],
            "tokyo": ["tokyo", "japan", "kyoto", "osaka"]
        }

        self._coord_cache: Dict[str, List[float]] = {
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
            "laxman jhula & suspension bridge": [30.1294, 78.3283],
            "triveni ghat evening maha aarti": [30.1030, 78.2970],
            "the beatles ashram (chaurasi kutia)": [30.1170, 78.3120],
            "ram jhula & swarg ashram": [30.1230, 78.3180],
            "shivpuri white water rafting beach": [30.1420, 78.3890],
            "neer garh waterfall trek": [30.1470, 78.3340],
            "kunjapuri sunrise peak & temple": [30.1830, 78.3240],

            # Varanasi
            "varanasi": [25.3176, 82.9739],
            "dashashwamedh ghat evening aarti": [25.3060, 83.0100],
            "assi ghat morning yoga & boat jetty": [25.2900, 83.0060],
            "kashi vishwanath golden temple": [25.3109, 83.0107],
            "manikarnika sacred cremation ghat": [25.3110, 83.0140],
            "sarnath deer park & chaukhandi stupa": [25.3810, 83.0230],
            "banaras hindu university (bhu) & vishwanath temple": [25.2670, 82.9910],

            # Leh & Ladakh
            "leh": [34.1526, 77.5771],
            "shanti stupa sunrise dome": [34.1670, 77.5850],
            "leh palace & namgyal tsemo monastery": [34.1650, 77.5840],
            "thiksey monastery (mini potala)": [34.0560, 77.6660],
            "pangong tso lake & crystal shores": [33.7590, 78.6670],
            "khardung la pass (17,982 ft)": [34.2780, 77.6040],
            "nubra valley sand dunes & bactrian camels": [34.6860, 77.5670],
            "hemis national park & monastery": [33.9120, 77.7080],

            # Tokyo & Japan
            "tokyo": [35.6762, 139.6503],
            "shibuya crossing & hachiko": [35.6595, 139.7005],
            "senso-ji temple & nakamise dori (asakusa)": [35.7148, 139.7967],
            "shinjuku gyoen national garden": [35.6852, 139.7101],
            "akihabara electric town & anime lane": [35.6983, 139.7731],
            "meiji shrine & yoyogi park": [35.6764, 139.6993],
            "teamlab planets digital art (toyosu)": [35.6493, 139.7898],
            "tsukiji outer food market": [35.6654, 139.7707],
            "roppongi hills tokyo city view": [35.6605, 139.7292],

            # Global Hubs
            "paris": [48.8566, 2.3522],
            "london": [51.5074, -0.1278],
            "new york": [40.7128, -74.0060],
            "dubai": [25.2048, 55.2708],
            "singapore": [1.3521, 103.8198],
            "bangkok": [13.7563, 100.5018],
            "bali": [-8.4095, 115.1889],
            "rome": [41.9028, 12.4964],
            "barcelona": [41.3851, 2.1734],
            "amsterdam": [52.3676, 4.9041],
            "khao san road backpacker alley": [13.7589, 100.4974],
            "patong beach & bangla nightlife": [7.8960, 98.2970],
            "old phuket town sino-portuguese lanes": [7.8840, 98.3880],
            "phi phi islands & maya bay": [7.7407, 98.7784]
        }

        self._destination_db: Dict[str, Any] = {
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
                    ("Old Manali Village & Cafes", [32.2530, 77.1764], "Alpine Bohemian Hub", "Historic cedar-wood village, vibrant backpacker cafes, live music, and apple orchards."),
                    ("Hadimba Devi Temple & Cedar Woods", [32.2483, 77.1804], "Sacred Forest Sanctuary", "16th-century pagoda-style wooden temple sheltered within towering deodar forests."),
                    ("Vashisht Hot Water Sulfur Springs", [32.2612, 77.1912], "Natural Geothermal Baths", "Natural therapeutic hot sulfur baths overlooking the roaring Beas river valley."),
                    ("Jogini Waterfall Trek", [32.2678, 77.1978], "Valley Trekking Trail", "Scenic 45-minute pine trail from Vashisht leading to a cascading sacred cliff waterfall."),
                    ("Solang Valley Adventure Hub", [32.3167, 77.1583], "High-Altitude Glacial Basin", "Paragliding, quad biking, and alpine meadows nestled beneath snowy Himalayan peaks."),
                    ("Rohtang Pass & Snow Plateau", [32.3716, 77.2466], "Piramidal High Pass (13,058 ft)", "Gateway pass to Lahaul & Spiti with 360-degree glaciated Himalayan panoramas."),
                    ("Sethan Igloo Village & Hampta Trail", [32.2030, 77.2280], "Off-Grid Buddhist Hamlet", "Tranquil Khampa village, winter igloo stays, and panoramic trailheads."),
                    ("Kasol Backpacker Market & Parvati River", [32.0100, 77.3150], "Parvati Valley Center", "Famous backpacker hub, riverside wooden cafes, Israeli bakeries, and pine woods."),
                    ("Chalal Pine Forest Trail", [32.0150, 77.3250], "Riverside Nature Trail", "Tranquil walking path following the aqua Parvati river towards rustic artisan huts."),
                    ("Manikaran Sahib Gurudwara & Springs", [32.0270, 77.3480], "Sacred Geothermal Valley", "Sacred riverfront shrine with geothermal boiling springs and communal langar feast."),
                    ("Tosh Village & Glacier Viewpoints", [32.0180, 77.4490], "Clifftop Alpine Settlement", "Traditional wooden village perched at 7,800 ft overlooking Tosh glacier peaks."),
                    ("Kheerganga Hot Springs Trek", [31.9890, 77.5140], "Himalayan Ridge Meadow", "Famous 12km alpine trail terminating at high-altitude natural hot mineral baths."),
                    ("Naggar Castle & Roerich Gallery", [32.1150, 77.1680], "Kullu Heritage Citadel", "15th-century wood-and-stone royal palace commanding breathtaking Beas valley vistas."),
                    ("Jana Waterfall & Local Dhaba", [32.1350, 77.1920], "Hinterland Pine Escape", "Secluded natural waterfall surrounded by traditional Himachali food stalls.")
                ]
            },
            "jaipur": {
                "title": "Pink City Palaces, Regal Citadels & Historic Bazaars",
                "default_coords": [26.9124, 75.7873],
                "dishes": ["Dal Baati Churma", "Pyaaz Kachori", "Ghewar Sweet", "Laal Maas", "Ker Sangri"],
                "savings_tip": "Purchase the Jaipur Composite Heritage Entry Ticket at Hawa Mahal or Amer Fort to gain access to 8 major state monuments with 50% student discount.",
                "transit_tip": "Jaipur Metro connects Railway Station to Chandpole (Old Pink City) for ₹10-20. Use E-rickshaws for short trips inside walled city gates.",
                "landmarks": [
                    ("Hawa Mahal (Palace of Winds)", [26.9239, 75.8267], "Pink City Core", "Five-story pink sandstone facade with 953 intricately carved jharokha honeycomb windows."),
                    ("Amer Fort & Elephant Ramparts", [26.9855, 75.8513], "Aravalli Ridge Citadel", "UNESCO hill fortress featuring the magnificent Sheesh Mahal mirror palace."),
                    ("City Palace & Courtyards", [26.9258, 75.8237], "Royal Heritage Center", "Blend of Rajput and Mughal architecture housing museums, peacock courtyards, and armory."),
                    ("Jantar Mantar UNESCO Observatory", [26.9248, 75.8246], "Astronomical Wonder", "World's largest stone sundial and 19 historic astronomical measuring instruments."),
                    ("Nahargarh Fort Sunset Bastion", [26.9372, 75.8156], "High Cliff Overlook", "Spectacular vantage point offering unobstructed sunset vistas across the pink city."),
                    ("Jal Mahal (Water Palace)", [26.9535, 75.8462], "Man Sagar Lake", "Romantic floating palace standing majestically in the center of tranquil waters."),
                    ("Bapu Bazaar & Johari Jewels", [26.9198, 75.8231], "Walled City Bazaar", "Vibrant arcaded streets selling leather mojari footwear, tie-dye textiles, and spices."),
                    ("Albert Hall State Museum", [26.9117, 75.8194], "Ram Niwas Garden", "Indo-Saracenic architectural museum glowing under night illuminations."),
                    ("Lake Pichola & Boat Jetty (Udaipur)", [24.5765, 73.6800], "City of Lakes Promenade", "Tranquil freshwater lake featuring sunset boat cruises around floating palaces."),
                    ("City Palace of Udaipur", [24.5764, 73.6835], "Lakeside Royal Complex", "Rajasthan's largest royal palace complex with panoramic balconies over Lake Pichola."),
                    ("Jag Mandir Island Palace", [24.5681, 73.6780], "Lake Island Haven", "Historic island palace retreat surrounded by carved marble elephants and courtyards."),
                    ("Monsoon Palace (Sajjangarh)", [24.5950, 73.6370], "Bansdara Peak Overlook", "Hilltop palace built to track monsoon clouds, offering breathtaking Aravalli sunsets."),
                    ("Saheliyon-ki-Bari Fountains", [24.6015, 73.6854], "Royal Courtyard Oasis", "Historic ornamental gardens with marble elephant fountains and lotus pools."),
                    ("Fatehsagar Lake Promenade", [24.5986, 73.6740], "Lakeside Sunset Drive", "Scenic promenade lined with popular student street food stalls and paddleboats.")
                ]
            },
            "rishikesh": {
                "title": "Sacred Ganges Ghats, Yoga Ashrams & Alpine Rapids",
                "default_coords": [30.0869, 78.2676],
                "dishes": ["Ganga Kinare Chai & Bun Maska", "Aloo Poori Bhandar", "Ayurvedic Kitchari", "Wood-fired Organic Pizzas", "Lassi & Sweets"],
                "savings_tip": "Stay in ashram guest houses or riverside student hostels in Tapovan for ₹350-500/night. Attend open morning meditation and yoga classes on the ghats for free.",
                "transit_tip": "Hop on Vikram shared autos (₹15-20) between Rishikesh town, Ram Jhula, and Laxman Jhula. Walk along the scenic riverside pedestrian bridges.",
                "landmarks": [
                    ("Laxman Jhula & Suspension Bridge", [30.1294, 78.3283], "Ganges North Crossing", "Iconic pedestrian iron suspension bridge towering across turquoise Himalayan rapids."),
                    ("Triveni Ghat Evening Maha Aarti", [30.1030, 78.2970], "Sacred River Confluence", "Grand devotional sunset ceremony with synchronised chants, flaming oil lamps, and river diyas."),
                    ("The Beatles Ashram (Chaurasi Kutia)", [30.1170, 78.3120], "Rajaji Forest Reserve", "Historic meditation domes covered in international psychedelic murals and heritage artifacts."),
                    ("Ram Jhula & Swarg Ashram", [30.1230, 78.3180], "Spiritual Riverbank Strip", "Spiritual center packed with historic ashrams, classical bookstore alleys, and river steps."),
                    ("Shivpuri White Water Rafting Beach", [30.1420, 78.3890], "Upper Canyon Rapids", "Launch point for grade III & IV white-water river rafting navigating Roller Coaster rapids."),
                    ("Neer Garh Waterfall Trek", [30.1470, 78.3340], "Jungle Limestone Cascades", "Multi-tiered emerald natural pools hidden in Himalayan forests, ideal for a refreshing swim."),
                    ("Kunjapuri Sunrise Peak & Temple", [30.1830, 78.3240], "5,400 ft Ridge Summit", "Vantage point offering sunrise vistas of snow-capped Himalayan peaks including Bandarpoonch.")
                ]
            },
            "varanasi": {
                "title": "Eternal Ghats, Sacred Dawn Rites & Ancient Silk Alleys",
                "default_coords": [25.3176, 82.9739],
                "dishes": ["Banarasi Kachori Sabzi & Jalebi", "Blue Lassi Bhandar", "Malaiyo (Winter Saffron Foam)", "Tamatar Chaat", "Banarasi Paan"],
                "savings_tip": "Wake up at 5:30 AM for a shared wooden rowboat at Assi Ghat for ~₹100/person instead of hiring a private motor launch (₹1500+).",
                "transit_tip": "Navigate the old town maze exclusively on foot. Use shared cycle-rickshaws (₹20-30) along the outer boulevard circuits.",
                "landmarks": [
                    ("Dashashwamedh Ghat Evening Aarti", [25.3060, 83.0100], "Central Ritual Ghat", "World-renowned hypnotic Ganga Aarti ceremony conducted by seven saffron-robed priests."),
                    ("Assi Ghat Morning Yoga & Boat Jetty", [25.2900, 83.0060], "Southern Gateway Ghat", "Dawn Subah-e-Banaras classical music recitals, sunrise yoga gatherings, and rowboats."),
                    ("Kashi Vishwanath Golden Temple", [25.3109, 83.0107], "Spiritual Epicenter", "Sacred Jyotirlinga shrine topped with 800kg of gold leaf, featuring the new river corridor."),
                    ("Manikarnika Sacred Cremation Ghat", [25.3110, 83.0140], "Ancient Riverfront Bastion", "Varanasi's primary cremation ghat, steeped in timeless philosophical solemnity."),
                    ("Sarnath Deer Park & Chaukhandi Stupa", [25.3810, 83.0230], "Buddhist Heritage Oasis", "Sacred site where Lord Buddha delivered his first sermon following enlightenment."),
                    ("Banaras Hindu University (BHU) & Vishwanath Temple", [25.2670, 82.9910], "Academic Green Oasis", "Historic 1,300-acre lush campus featuring the towering New Vishwanath marble temple.")
                ]
            },
            "leh": {
                "title": "Trans-Himalayan Stupas, Monasteries & High Passes",
                "default_coords": [34.1526, 77.5771],
                "dishes": ["Ladakhi Skyu Stew", "Thukpa Noodle Soup", "Butter Tea (Gur Gur Chai)", "Tingmo Steamed Bread", "Yak Cheese Chhurpi"],
                "savings_tip": "Strictly spend Day 1 resting for acclimatization. Form groups at your hostel noticeboard to split shared taxi costs to Pangong and Nubra Valley by up to 75%.",
                "transit_tip": "Rent local Royal Enfield or Himalayan bikes (₹1,200-1,500/day) only after 48 hours of acclimatization. Shared taxis depart from Leh Polo Ground stand.",
                "landmarks": [
                    ("Shanti Stupa Sunrise Dome", [34.1670, 77.5850], "Changspa Hilltop", "White-domed Buddhist stupa providing sunrise panoramas over Leh city and the Indus valley."),
                    ("Leh Palace & Namgyal Tsemo Monastery", [34.1650, 77.5840], "Royal Crag Bastion", "9-story 17th-century fortress modeled after Lhasa's Potala Palace."),
                    ("Thiksey Monastery (Mini Potala)", [34.0560, 77.6660], "Indus Valley Ridge", "12-story architectural marvel of Tibetan Buddhism housing a 49-foot Maitreya Buddha statue."),
                    ("Pangong Tso Lake & Crystal Shores", [33.7590, 78.6670], "High Altitude Endorheic Basin", "World-famous 134km long high-altitude saline lake shifting shades from turquoise to indigo."),
                    ("Khardung La Pass (17,982 ft)", [34.2780, 77.6040], "Karakoram Gateway", "Legendary high motorable mountain pass leading north to the Nubra and Shyok valleys."),
                    ("Nubra Valley Sand Dunes & Bactrian Camels", [34.6860, 77.5670], "Cold Desert Valley", "Dramatic high-altitude white sand dunes at Hunder featuring double-humped Bactrian camels."),
                    ("Hemis National Park & Monastery", [33.9120, 77.7080], "Snow Leopard Habitat", "Ladakh's largest and wealthiest monastery, surrounded by wild rugged valleys.")
                ]
            },
            "tokyo": {
                "title": "Neon Metropolises, Shinto Shrines & Cyberpunk Districts",
                "default_coords": [35.6762, 139.6503],
                "dishes": ["Tonkotsu Ramen & Tsukemen", "Conbini Onigiri & Egg Sandwiches", "Yakitori Skewers", "Fresh Nigiri Sushi", "Matcha Soft Serve"],
                "savings_tip": "Purchase the Tokyo Subway 72-Hour Tourist Ticket (~¥1,500) for unlimited rides on all Tokyo Metro & Toei Subway lines. Pick up evening dinner bentos at 50% discount at grocery stores.",
                "transit_tip": "Add a digital Suica or Pasmo card to your smartphone wallet for tap-and-go transit across all Japanese rail and subway operators.",
                "landmarks": [
                    ("Shibuya Crossing & Hachiko", [35.6595, 139.7005], "Youth Cultural Hub", "The world's busiest pedestrian scramble intersection flanked by glowing neon advertising towers."),
                    ("Senso-ji Temple & Nakamise Dori (Asakusa)", [35.7148, 139.7967], "Historic Downtown Core", "Tokyo's oldest Buddhist temple founded in 645 AD, entered through the giant Kaminarimon lantern."),
                    ("Shinjuku Gyoen National Garden", [35.6852, 139.7101], "Imperial Garden Sanctuary", "144-acre peaceful park blending traditional Japanese landscape, English, and French formal styles."),
                    ("Akihabara Electric Town & Anime Lane", [35.6983, 139.7731], "Otaku & Tech Mecca", "Multi-story electronics markets, retro gaming shops, hobby stores, and themed cafes."),
                    ("Meiji Shrine & Yoyogi Park", [35.6764, 139.6993], "Harajuku Forest Oasis", "Monumental cypress torii gates and 170 acres of sacred evergreen forest honoring Emperor Meiji."),
                    ("teamLab Planets Digital Art (Toyosu)", [35.6493, 139.7898], "Immersive Digital Pavilion", "Sensory museum where visitors walk barefoot through water and infinite crystal light projections."),
                    ("Tsukiji Outer Food Market", [35.6654, 139.7707], "Culinary Street Maze", "Bustling open-air seafood market with vendors serving wagyu skewers, tamagoyaki, and uni bowls."),
                    ("Roppongi Hills Tokyo City View", [35.6605, 139.7292], "Skyline Observation Deck", "Open-air sky deck atop Mori Tower commanding panoramic vistas of Tokyo Tower and Mount Fuji.")
                ]
            }
        }

        # Populate cache from database defaults
        for dest_k, dest_val in self._destination_db.items():
            if "default_coords" in dest_val:
                self._coord_cache[dest_k.lower()] = dest_val["default_coords"]
            for lm in dest_val.get("landmarks", []):
                if len(lm) > 1 and lm[1]:
                    self._coord_cache[lm[0].lower().strip()] = lm[1]

    @property
    def coord_cache(self) -> Dict[str, List[float]]:
        return self._coord_cache

    @property
    def destination_count(self) -> int:
        return len(self._coord_cache)

    def identify_destination_key(self, dest_str: Optional[str]) -> Optional[str]:
        """Matches a user input query to a known knowledge base preset."""
        if not dest_str:
            return None
        dest_lower = dest_str.lower().strip()
        for k, words in self._aliases.items():
            if any(w in dest_lower for w in words):
                return k
        return None

    def resolve_coordinates(self, location_name: str, destination_context: Optional[str] = None) -> Optional[List[float]]:
        """
        Multi-tier coordinate resolution:
        1. Exact cache hit.
        2. Cleaned primary landmark match.
        3. Regional landmark catalog lookup.
        4. Substring and token overlap analysis.
        5. Live OSM Nominatim fallback with result caching.
        """
        if not location_name:
            return None

        raw = location_name.strip()
        cleaned = raw.lower()
        cleaned = re.sub(r'^(destination:\s*|must visit:\s*)', '', cleaned).strip()

        # 1. Exact match on cleaned full query
        if cleaned in self._coord_cache:
            return self._coord_cache[cleaned]

        # 2. Extract primary landmark name if comma-separated
        parts = [p.strip() for p in cleaned.split(",") if p.strip()]
        primary = parts[0] if parts else cleaned

        # 3. Check within DESTINATION_DB for the given destination context
        dest_ctx = destination_context or (parts[1] if len(parts) > 1 else None)
        dest_key = self.identify_destination_key(dest_ctx) if dest_ctx else None
        if dest_key and dest_key in self._destination_db:
            db_info = self._destination_db[dest_key]
            for lm in db_info.get("landmarks", []):
                lm_name = lm[0].lower()
                if primary in lm_name or lm_name in primary:
                    return lm[1]
                p_tokens = set(re.findall(r'\b[a-z]{3,}\b', primary))
                l_tokens = set(re.findall(r'\b[a-z]{3,}\b', lm_name))
                if len(p_tokens & l_tokens) >= 2:
                    return lm[1]

        # 4. Direct exact match on primary landmark
        if primary in self._coord_cache:
            return self._coord_cache[primary]

        # 5. Safe substring match against cache
        for k, v in self._coord_cache.items():
            if len(k) < 4 or len(primary) < 4:
                continue
            if primary in k:
                return v
            if (len(k) >= 10 or " " in k) and k in primary:
                return v

        # 6. Geocoding via Nominatim fallback
        if self._geolocator:
            try:
                location = self._geolocator.geocode(location_name, timeout=5)
                if not location and len(parts) > 1:
                    location = self._geolocator.geocode(parts[0], timeout=5)
                if location:
                    coords = [round(location.latitude, 5), round(location.longitude, 5)]
                    self._coord_cache[cleaned] = coords
                    self._coord_cache[primary] = coords
                    return coords
            except Exception:
                pass

        return None

    def build_fallback_itinerary(
        self,
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
        """Synthesize high-fidelity fallback markdown itinerary when offline or API key absent."""
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

        dest_key = self.identify_destination_key(destination)
        dest_info = self._destination_db.get(dest_key) if dest_key else None

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


# Singleton Instance
geo_service = GeoLocationService.get_instance()

# Backward-compatible function and data exports
def get_coordinates(location_name: str, destination_context: Optional[str] = None) -> Optional[List[float]]:
    return geo_service.resolve_coordinates(location_name, destination_context)

def get_destination_key(dest_str: Optional[str]) -> Optional[str]:
    return geo_service.identify_destination_key(dest_str)

def generate_fallback_itinerary(*args, **kwargs) -> str:
    return geo_service.build_fallback_itinerary(*args, **kwargs)

COORD_CACHE = geo_service.coord_cache
DESTINATION_DB = geo_service._destination_db
