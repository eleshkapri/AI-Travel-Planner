import streamlit as st
from groq import Groq
import folium
from streamlit_folium import st_folium
from geopy.geocoders import Nominatim
from fpdf import FPDF # <--- NEW IMPORT

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="AI Student Travel Planner", 
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
    # ✈️ LOGO
    st.image("https://cdn-icons-png.flaticon.com/512/2200/2200326.png", width=60)
    st.title("Trip Settings")
    st.markdown("---")
    
    destination = st.text_input("📍 Where to?", placeholder="e.g. Kyoto, Japan")
    
    col1, col2 = st.columns(2)
    with col1:
        days = st.number_input("📅 Days", 1, 30, 3)
    with col2:
        budget_level = st.selectbox("💰 Tier", ["Student (Low)", "Moderate", "Luxury"])
        
    budget_amount = st.text_input("💵 Total Budget (Optional)", placeholder="e.g. $500, 20000 INR")
    
    st.subheader("❤️ Interests")
    selected_interests = st.multiselect(
        "Select Tags", 
        ["History", "Street Food", "Nature", "Nightlife", "Museums", "Adventure"],
        default=["Street Food"]
    )
    
    custom_interests = st.text_input("Other (Type & Enter)", placeholder="e.g. Anime, Cafes...")
    
    # Must-Visit Place
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

# ⚡ MAP FIX: Unique User Agent
@st.cache_data
def get_coordinates(location_name):
    try:
        # Unique ID to prevent blocking
        geolocator = Nominatim(user_agent="student_travel_planner_2026_elesh_pdf_v1")
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

# 📄 PDF GENERATOR FUNCTION
def create_pdf(text):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    
    # Add Title
    pdf.set_font("Arial", style="B", size=16)
    pdf.cell(200, 10, txt="AI Travel Itinerary", ln=True, align='C')
    pdf.ln(10) # Line break
    
    # Add Content
    pdf.set_font("Arial", size=12)
    
    # FPDF doesn't support emojis/special chars well, so we sanitize the text
    # We replace common problematic characters
    clean_text = text.replace("’", "'").replace("–", "-").replace("—", "-")
    
    for line in clean_text.split('\n'):
        # Encode to latin-1 to avoid unicode crashes (strips emojis)
        safe_line = line.encode('latin-1', 'replace').decode('latin-1')
        pdf.multi_cell(0, 10, txt=safe_line)
        
    return pdf.output(dest='S').encode('latin-1')

# --- MAIN UI LAYOUT ---

# 🌍 HEADER
col1, col2 = st.columns([1, 8])

with col1:
    st.image("https://cdn-icons-png.flaticon.com/512/921/921490.png", width=80)

with col2:
    st.title("AI Student Travel Planner")
    st.caption("Your personalized, budget-friendly travel agent powered by Llama 3.")

st.markdown("---")

# 1. Trigger AI Generation
if generate_btn and destination:
    with st.spinner("✨ Drafting the perfect plan..."):
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

# 2. Display Results
if st.session_state.itinerary:
    
    # --- SECTION 1: THE MAP ---
    st.markdown('<div class="css-card">', unsafe_allow_html=True)
    st.subheader(f"📍 Exploring {destination}")
    
    start_coords = get_coordinates(destination)
    if start_coords:
        m = folium.Map(location=start_coords, zoom_start=12)
        
        # Pins
        folium.Marker(
            start_coords, 
            popup=f"Destination: {destination}", 
            icon=folium.Icon(color="red", icon="info-sign")
        ).add_to(m)
        
        if must_visit:
            mv_coords = get_coordinates(f"{must_visit}, {destination}")
            if mv_coords:
                 folium.Marker(mv_coords, popup=f"Must Visit: {must_visit}", icon=folium.Icon(color="green", icon="star")).add_to(m)

        for place in st.session_state.landmarks:
            coords = get_coordinates(f"{place}, {destination}")
            if coords:
                folium.Marker(coords, popup=place, icon=folium.Icon(color="blue", icon="camera")).add_to(m)
        
        st_folium(m, width=1200, height=500)
    else:
        st.error("Could not find location. Please check the spelling.")
    
    st.markdown('</div>', unsafe_allow_html=True)

    # --- SECTION 2: THE ITINERARY & PDF EXPORT ---
    st.markdown('<div class="css-card">', unsafe_allow_html=True)
    st.subheader("📝 Your AI Itinerary")
    st.markdown(f'<div class="highlight">{st.session_state.itinerary}</div>', unsafe_allow_html=True)
    
    # 📄 GENERATE PDF
    pdf_data = create_pdf(st.session_state.itinerary)
    
    st.download_button(
        label="📄 Download Itinerary as PDF",
        data=pdf_data,
        file_name=f"Trip_to_{destination}.pdf",
        mime="application/pdf"
    )
    st.markdown('</div>', unsafe_allow_html=True)