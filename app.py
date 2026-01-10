import streamlit as st
from groq import Groq
import folium
from streamlit_folium import st_folium
from geopy.geocoders import Nominatim
import time

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Student AI Travel Planner", 
    page_icon="✈️", 
    layout="wide"
)

# --- ADVANCED CSS STYLING ---
st.markdown("""
<style>
    /* Main Background */
    .stApp {
        background-color: #0E1117;
    }
    
    /* Card-like Containers */
    .css-card {
        background-color: #1E1E1E;
        padding: 25px;
        border-radius: 15px;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.5);
        margin-bottom: 25px;
        border: 1px solid #333;
    }
    
    /* Gradient Button */
    .stButton>button {
        width: 100%;
        background: linear-gradient(90deg, #FF4B4B 0%, #FF914D 100%);
        color: white;
        border: none;
        padding: 12px;
        border-radius: 10px;
        font-weight: bold;
        font-size: 16px;
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        transform: scale(1.02);
        box-shadow: 0 5px 15px rgba(255, 75, 75, 0.4);
    }
    
    /* Headings */
    h1 {
        font-family: 'Helvetica Neue', sans-serif;
        font-weight: 800;
        background: -webkit-linear-gradient(#eee, #999);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    h3 {
        color: #FF914D !important;
    }
    
    /* Itinerary Text Box */
    .highlight {
        background-color: #262730;
        color: #E0E0E0;
        padding: 25px;
        border-radius: 10px;
        border-left: 5px solid #FF4B4B;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        line-height: 1.6;
    }
</style>
""", unsafe_allow_html=True)

# --- SESSION STATE ---
if "itinerary" not in st.session_state:
    st.session_state.itinerary = ""
if "landmarks" not in st.session_state:
    st.session_state.landmarks = []

# --- SIDEBAR INPUTS ---
with st.sidebar:
    st.title("✈️ Trip Settings")
    st.markdown("---")
    
    destination = st.text_input("📍 Where to?", placeholder="e.g. Kyoto, Japan")
    
    col1, col2 = st.columns(2)
    with col1:
        days = st.number_input("📅 Days", 1, 30, 3)
    with col2:
        budget_level = st.selectbox("💰 Tier", ["Student (Low)", "Moderate", "Luxury"])
        
    budget_amount = st.text_input("💵 Total Budget (Optional)", placeholder="e.g. $500, ₹20000")
    
    st.subheader("❤️ Interests")
    selected_interests = st.multiselect(
        "Select Tags", 
        ["History", "Street Food", "Nature", "Nightlife", "Museums", "Adventure"],
        default=["Street Food"]
    )
    
    custom_interests = st.text_input("Other (Type & Enter)", placeholder="e.g. Anime, Cafes...")
    
    # NEW: Must-Visit Place
    st.subheader("📍 Must Visit")
    must_visit = st.text_input("Specific Place (Optional)", placeholder="e.g. Tokyo Tower")

    # Combine interests
    all_interests = selected_interests.copy()
    if custom_interests:
        all_interests.append(custom_interests)
    interests_string = ", ".join(all_interests)
    
    st.markdown("---")
    generate_btn = st.button("🚀 Plan My Adventure")

# --- FUNCTIONS ---

# ⚡ PERFORMANCE FIX: Cache coordinates so we don't fetch them every time
@st.cache_data
def get_coordinates(location_name):
    try:
        geolocator = Nominatim(user_agent="student_travel_planner_v8_hover")
        location = geolocator.geocode(location_name, timeout=10)
        if location:
            return location.latitude, location.longitude
    except Exception as e:
        print(f"Map Error: {e}")
        return None
    return None

def generate_trip():
    client = Groq(api_key=st.secrets["GROQ_API_KEY"])
    
    # Build Prompt
    budget_text = f"{budget_level} Tier"
    if budget_amount:
        budget_text += f" with a strict cap of {budget_amount}"

    # Logic to include the must-visit place
    must_visit_instruction = ""
    if must_visit:
        must_visit_instruction = f"CRITICAL: You MUST include a visit to '{must_visit}' in the itinerary."

    prompt = f"""
    Act as an expert local travel guide. Create a {days}-day trip to {destination} for a student. 
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
    try:
        completion = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.3-70b-versatile",
        )
        return completion.choices[0].message.content
    except Exception as e:
        st.error(f"AI Error: {e}")
        return None

# --- MAIN UI LAYOUT ---

st.title("🌍 AI Student Travel Planner")
st.caption("Your personalized, budget-friendly travel agent powered by Llama 3.")

# 1. Trigger AI Generation
if generate_btn and destination:
    with st.spinner("✨ Drafting the perfect plan..."):
        # Clear cache if destination changes significantly (optional, but good for fresh starts)
        # st.cache_data.clear() 
        
        response = generate_trip()
        if response:
            if "LANDMARKS:" in response:
                parts = response.split("LANDMARKS:")
                st.session_state.itinerary = parts[0]
                raw_landmarks = parts[1].strip().split(",")
                st.session_state.landmarks = [l.strip() for l in raw_landmarks]
            else:
                st.session_state.itinerary = response
                st.session_state.landmarks = [destination]

# 2. Display Results (Stacked Layout)
if st.session_state.itinerary:
    
    # --- SECTION 1: THE MAP (Full Width) ---
    st.markdown('<div class="css-card">', unsafe_allow_html=True)
    st.subheader(f"📍 Exploring {destination}")
    
    start_coords = get_coordinates(destination)
    if start_coords:
        # Create a wider map
        m = folium.Map(location=start_coords, zoom_start=12)
        
        # 1. MAIN CITY PIN (Red)
        folium.Marker(
            start_coords, 
            popup=f"Destination: {destination}", 
            tooltip=f"Destination: {destination}", # Hover Text
            icon=folium.Icon(color="red", icon="info-sign")
        ).add_to(m)
        
        # 2. USER'S MUST-VISIT PIN (Green Star)
        if must_visit:
            mv_coords = get_coordinates(f"{must_visit}, {destination}")
            if mv_coords:
                 folium.Marker(
                    mv_coords, 
                    popup=f"Must Visit: {must_visit}", 
                    tooltip=f"Must Visit: {must_visit}", # Hover Text
                    icon=folium.Icon(color="green", icon="star")
                ).add_to(m)

        # 3. AI SUGGESTED PINS (Blue Camera)
        for place in st.session_state.landmarks:
            coords = get_coordinates(f"{place}, {destination}")
            if coords:
                folium.Marker(
                    coords, 
                    popup=place, 
                    tooltip=place, # Hover Text
                    icon=folium.Icon(color="blue", icon="camera")
                ).add_to(m)
        
        # Display Map Full Width
        st_folium(m, width=1200, height=500)
    else:
        st.warning("Map server is busy, but your itinerary is ready below!")
    
    st.markdown('</div>', unsafe_allow_html=True)

    # --- SECTION 2: THE ITINERARY (Full Width) ---
    st.markdown('<div class="css-card">', unsafe_allow_html=True)
    st.subheader("📝 Your AI Itinerary")
    st.markdown(f'<div class="highlight">{st.session_state.itinerary}</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    