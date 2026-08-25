import os
import json
import streamlit as st
from groq import Groq
import folium
from streamlit_folium import st_folium
from geopy.geocoders import Nominatim
from fpdf import FPDF

# ========================================================
# 1. PAGE CONFIGURATION & 3D VIBRANT THEME
# ========================================================
st.set_page_config(
    page_title="RoamAI • AI Student Travel Planner",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom 3D & Vibrant Bright Modern CSS Injection
st.markdown("""
<style>
    /* Google Font */
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&display=swap');

    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', sans-serif;
    }

    /* Main App Background */
    .stApp {
        background-color: #0B0F19;
        background-image: 
            radial-gradient(circle at 10% 10%, rgba(255, 94, 54, 0.12) 0%, transparent 45%),
            radial-gradient(circle at 90% 20%, rgba(6, 182, 212, 0.10) 0%, transparent 45%),
            radial-gradient(circle at 50% 90%, rgba(139, 92, 246, 0.10) 0%, transparent 50%);
        color: #F3F4F6;
    }

    /* 3D Glassmorphic Container Cards */
    .glass-card {
        background: rgba(18, 24, 38, 0.85);
        backdrop-filter: blur(16px);
        -webkit-backdrop-filter: blur(16px);
        border: 1px solid rgba(255, 255, 255, 0.09);
        border-radius: 20px;
        padding: 24px;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.4);
        margin-bottom: 24px;
        transition: all 0.3s ease;
    }
    .glass-card:hover {
        border-color: rgba(255, 94, 54, 0.35);
        transform: translateY(-2px);
        box-shadow: 0 15px 35px rgba(255, 94, 54, 0.15);
    }

    /* Vibrant Gradient Buttons */
    .stButton>button {
        width: 100%;
        background: linear-gradient(135deg, #FF5E36 0%, #FFA000 100%);
        color: #FFFFFF !important;
        border: none;
        padding: 12px 24px;
        border-radius: 14px;
        font-weight: 800;
        font-size: 15px;
        letter-spacing: 0.3px;
        box-shadow: 0 4px 20px rgba(255, 94, 54, 0.4);
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        transform: scale(1.02);
        box-shadow: 0 8px 25px rgba(255, 94, 54, 0.6);
        color: #FFFFFF !important;
    }

    /* Download Buttons */
    .stDownloadButton>button {
        background: rgba(255, 255, 255, 0.08);
        border: 1px solid rgba(255, 255, 255, 0.18);
        color: #FFFFFF !important;
        border-radius: 12px;
        font-weight: 700;
        transition: all 0.2s ease;
    }
    .stDownloadButton>button:hover {
        background: linear-gradient(135deg, #FF5E36 0%, #FFA000 100%);
        border-color: transparent;
    }

    /* Highlighted Itinerary Box */
    .highlight-box {
        background: rgba(26, 32, 48, 0.9);
        border-left: 5px solid #FF5E36;
        border-radius: 16px;
        padding: 24px;
        color: #E2E8F0;
        line-height: 1.8;
        box-shadow: 0 6px 20px rgba(0,0,0,0.3);
        margin-top: 15px;
    }
    .highlight-box h1, .highlight-box h2 {
        color: #FF5E36 !important;
    }
    .highlight-box h3 {
        color: #FFA000 !important;
    }

    /* Sidebar Customization */
    [data-testid="stSidebar"] {
        background-color: #0E1320 !important;
        border-right: 1px solid rgba(255, 255, 255, 0.08);
    }

    /* Input Fields Styling */
    .stTextInput>div>div>input, .stSelectbox>div>div, .stNumberInput>div>div>input {
        background-color: #121826 !important;
        border: 1px solid rgba(255, 255, 255, 0.12) !important;
        color: #FFFFFF !important;
        border-radius: 12px !important;
    }

    /* Metric Cards */
    [data-testid="stMetricValue"] {
        color: #FF5E36 !important;
        font-weight: 800;
    }

    /* Radio buttons / Tabs */
    .stRadio [role="radiogroup"] {
        gap: 10px;
    }
</style>
""", unsafe_allow_html=True)


# ========================================================
# 2. SESSION STATE MANAGEMENT
# ========================================================
if "nav_page" not in st.session_state:
    st.session_state.nav_page = "🌟 Discover & Explore"
if "itinerary" not in st.session_state:
    st.session_state.itinerary = ""
if "landmarks" not in st.session_state:
    st.session_state.landmarks = []
if "current_destination" not in st.session_state:
    st.session_state.current_destination = ""
if "saved_trips" not in st.session_state:
    st.session_state.saved_trips = []
if "packing_items" not in st.session_state:
    st.session_state.packing_items = {
        "Passport / Student ID": True,
        "Zero-Forex Travel Card": True,
        "Universal Power Adapter": True,
        "Power Bank (10k mAh)": False,
        "Comfortable Walking Shoes": True,
        "Quick-dry Hostel Towel": False,
        "Basic First Aid & Meds": False,
        "Rain Jacket / Windbreaker": False
    }


# ========================================================
# 3. HELPER FUNCTIONS (GEOCODING, GROQ, PDF)
# ========================================================
def get_groq_api_key():
    if "GROQ_API_KEY" in st.secrets:
        return st.secrets["GROQ_API_KEY"]
    if os.environ.get("GROQ_API_KEY"):
        return os.environ.get("GROQ_API_KEY")
    return None

@st.cache_data(show_spinner=False)
def get_coordinates(location_name):
    try:
        geolocator = Nominatim(user_agent="travel_planner_python_v12")
        location = geolocator.geocode(location_name, timeout=12)
        if location:
            return location.latitude, location.longitude
    except Exception:
        pass
    return None

def generate_trip_itinerary(destination, days, budget_level, budget_amount, currency, interests, must_visit, pace, accommodation):
    api_key = get_groq_api_key()
    if not api_key:
        st.error("⚠️ GROQ_API_KEY is not set in `.streamlit/secrets.toml` or environment variables.")
        return None

    client = Groq(api_key=api_key)

    budget_text = f"{budget_level} Tier ({currency})"
    if budget_amount:
        budget_text += f" with strict limit of {budget_amount} {currency}"

    must_visit_instruction = ""
    if must_visit:
        must_visit_instruction = f"CRITICAL: You MUST include a visit to '{must_visit}' in the itinerary."

    interests_str = ", ".join(interests) if interests else "Local culture, street food, budget gems"

    prompt = f"""
    You are an award-winning local travel architect specializing in epic, student-friendly, budget adventures.
    Create a high-energy, realistic {days}-day trip itinerary to {destination}.

    Trip Specifications:
    - Destination: {destination}
    - Duration: {days} Days
    - Budget: {budget_text}
    - Specific Interests: {interests_str}
    - Travel Pace: {pace}
    - Accommodation: {accommodation}
    {must_visit_instruction}

    Structure your response strictly in clean Markdown as follows:
    # 🌍 [Catchy Trip Title & Emoji]

    ## 💰 Estimated Student Budget Breakdown ({currency})
    - 🏨 **Accommodation ({accommodation}):** [Estimated cost per night & total]
    - 🍜 **Food & Street Eats:** [Daily & total food estimate]
    - 🚇 **Local Transport:** [Passes/Subway/Bus estimates]
    - 🎟️ **Activities & Entry Fees:** [Cost estimates for attractions]
    - 💡 **Student Savings Tip:** [1 high-impact money-saving hack]

    ## 🗓️ Day-by-Day Itinerary

    ### Day 1: [Day 1 Theme]
    - ☀️ **Morning:** [Actionable morning activity + budget tip]
    - 🌤️ **Afternoon:** [Actionable afternoon activity + food spot]
    - 🌙 **Evening:** [Sunset viewpoint, night walk, or student vibes]

    (Provide full detailed breakdown for all {days} days)

    ## 🎒 Essential Student Tips
    - 3 practical tips for safety, SIM cards, or student discounts in {destination}.

    LANDMARKS: Place 1, Place 2, Place 3
    """

    models_to_try = [
        "openai/gpt-oss-120b",
        "openai/gpt-oss-20b",
        "llama-3.1-8b-instant",
        "qwen/qwen3.6-27b",
    ]

    last_err = None
    for model_name in models_to_try:
        try:
            completion = client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model=model_name,
            )
            return completion.choices[0].message.content
        except Exception as e:
            last_err = e
            continue

    st.error(f"AI Generation Error: {last_err}")
    return None

# PDF Generator Class
class SmartTravelPDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 16)
        self.set_text_color(255, 94, 54) # Sunset Coral
        self.cell(0, 10, 'RoamAI - Student Travel Itinerary', 0, 1, 'C')
        self.ln(3)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.set_text_color(150, 150, 150)
        self.cell(0, 10, f'Page {self.page_no()} | Generated by RoamAI', 0, 0, 'C')

def create_itinerary_pdf(text, destination_name):
    pdf = SmartTravelPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    
    replacements = {
        "₹": "Rs. ", "€": "EUR ", "£": "GBP ", "$": "USD ",
        "’": "'", "“": '"', "”": '"', "–": "-", "—": "-", "**": ""
    }
    
    clean_text = text
    for key, val in replacements.items():
        clean_text = clean_text.replace(key, val)

    lines = clean_text.split('\n')
    for line in lines:
        line = line.strip()
        if not line:
            pdf.ln(4)
            continue
        
        safe_line = line.encode('latin-1', 'ignore').decode('latin-1')

        if line.startswith('# '):
            pdf.set_font("Arial", 'B', 15)
            pdf.set_text_color(255, 94, 54)
            pdf.cell(0, 8, safe_line.replace('# ', '').strip(), ln=True)
            pdf.set_text_color(0, 0, 0)
        elif line.startswith('## '):
            pdf.set_font("Arial", 'B', 13)
            pdf.set_text_color(255, 160, 0)
            pdf.cell(0, 7, safe_line.replace('## ', '').strip(), ln=True)
            pdf.set_text_color(0, 0, 0)
        elif line.startswith('### '):
            pdf.set_font("Arial", 'B', 11)
            pdf.set_text_color(6, 182, 212)
            pdf.cell(0, 6, safe_line.replace('### ', '').strip(), ln=True)
            pdf.set_text_color(0, 0, 0)
        elif line.startswith('*') or line.startswith('-'):
            clean_item = safe_line[1:].strip()
            pdf.set_font("Arial", '', 10)
            pdf.set_x(15)
            pdf.cell(5, 5, chr(149), 0, 0)
            pdf.multi_cell(0, 5, clean_item)
        else:
            pdf.set_font("Arial", '', 10)
            pdf.multi_cell(0, 5, safe_line)
            
    return pdf.output(dest='S').encode('latin-1')


# ========================================================
# 4. SIDEBAR NAVIGATION & CONTROLS
# ========================================================
with st.sidebar:
    st.markdown("""
    <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 10px;">
        <span style="font-size: 32px;">✈️</span>
        <div>
            <h2 style="margin: 0; color: #FFFFFF; font-weight: 800; font-size: 22px;">RoamAI</h2>
            <p style="margin: 0; color: #FF5E36; font-size: 11px; font-weight: bold; text-transform: uppercase;">Student Travel Architect</p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("---")

    selected_nav = st.radio(
        "Navigation",
        [
            "🌟 Discover & Explore",
            "🚀 AI Trip Planner",
            "💰 Budget Calculator",
            "🎒 Packing Checklist",
            f"📂 Saved Trips ({len(st.session_state.saved_trips)})"
        ],
        index=["🌟 Discover & Explore", "🚀 AI Trip Planner", "💰 Budget Calculator", "🎒 Packing Checklist", f"📂 Saved Trips ({len(st.session_state.saved_trips)})"].index(
            st.session_state.nav_page if st.session_state.nav_page in ["🌟 Discover & Explore", "🚀 AI Trip Planner", "💰 Budget Calculator", "🎒 Packing Checklist"] else f"📂 Saved Trips ({len(st.session_state.saved_trips)})"
        )
    )
    st.session_state.nav_page = selected_nav

    st.markdown("---")
    st.caption("⚡ Powered by Groq AI Models")


# ========================================================
# 5. PAGE ROUTER & IMPLEMENTATION
# ========================================================

# ----------------------------------------------------
# PAGE 1: 🌟 DISCOVER & EXPLORE
# ----------------------------------------------------
if "Discover" in st.session_state.nav_page:
    # 3D Hero Banner
    st.markdown("""
    <div class="glass-card" style="border: 1px solid rgba(255, 94, 54, 0.3);">
        <span style="background: rgba(255, 160, 0, 0.2); color: #FFA000; padding: 4px 12px; border-radius: 999px; font-size: 12px; font-weight: 700;">
            ✨ Next-Gen AI Travel Architect
        </span>
        <h1 style="font-size: 36px; font-weight: 800; color: #FFFFFF; margin-top: 12px; margin-bottom: 8px;">
            Plan Epic Adventures <span style="background: linear-gradient(135deg, #FF5E36, #FFA000); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">In Seconds.</span>
        </h1>
        <p style="color: #9CA3AF; font-size: 15px; max-width: 680px; line-height: 1.6;">
            Personalized day-by-day schedules, student budget hacks, interactive 3D map pins, and offline PDF exports generated instantly.
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Live Metrics
    m1, m2, m3 = st.columns(3)
    with m1:
        st.metric("Trips Planned", "50,000+", "⚡ Real-time")
    with m2:
        st.metric("Global Destinations", "120+ Countries", "🌍 Worldwide")
    with m3:
        st.metric("Student Cost", "100% Free", "🎓 Open Source")

    st.markdown("### 🔥 Trending Student Hotspots")
    st.caption("Click any popular student destination to launch the planner immediately:")

    c1, c2, c3 = st.columns(3)

    with c1:
        st.markdown("""
        <div class="glass-card" style="padding: 16px;">
            <img src="https://images.unsplash.com/photo-1503899036084-c55cdd92da26?auto=format&fit=crop&w=500&q=80" style="width: 100%; height: 160px; object-fit: cover; border-radius: 12px; margin-bottom: 12px;" />
            <h3 style="margin: 0; color: #FFFFFF;">Tokyo, Japan</h3>
            <p style="color: #FFA000; font-size: 12px; font-weight: bold; margin: 4px 0;">💰 ~$50/day • Neon Alleys & Cheap Ramen</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("🚀 Plan Tokyo Trip", key="btn_tokyo"):
            st.session_state.quick_dest = "Tokyo, Japan"
            st.session_state.quick_days = 4
            st.session_state.nav_page = "🚀 AI Trip Planner"
            st.rerun()

    with c2:
        st.markdown("""
        <div class="glass-card" style="padding: 16px;">
            <img src="https://images.unsplash.com/photo-1537996194471-e657df975ab4?auto=format&fit=crop&w=500&q=80" style="width: 100%; height: 160px; object-fit: cover; border-radius: 12px; margin-bottom: 12px;" />
            <h3 style="margin: 0; color: #FFFFFF;">Bali, Indonesia</h3>
            <p style="color: #06B6D4; font-size: 12px; font-weight: bold; margin: 4px 0;">💰 ~$30/day • Surfing & Lush Waterfalls</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("🚀 Plan Bali Trip", key="btn_bali"):
            st.session_state.quick_dest = "Bali, Indonesia"
            st.session_state.quick_days = 5
            st.session_state.nav_page = "🚀 AI Trip Planner"
            st.rerun()

    with c3:
        st.markdown("""
        <div class="glass-card" style="padding: 16px;">
            <img src="https://images.unsplash.com/photo-1512343879784-a960bf40e7f2?auto=format&fit=crop&w=500&q=80" style="width: 100%; height: 160px; object-fit: cover; border-radius: 12px; margin-bottom: 12px;" />
            <h3 style="margin: 0; color: #FFFFFF;">Goa, India</h3>
            <p style="color: #10B981; font-size: 12px; font-weight: bold; margin: 4px 0;">💰 ~$25/day • Beach Shacks & Nightlife</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("🚀 Plan Goa Trip", key="btn_goa"):
            st.session_state.quick_dest = "Goa, India"
            st.session_state.quick_days = 3
            st.session_state.nav_page = "🚀 AI Trip Planner"
            st.rerun()


# ----------------------------------------------------
# PAGE 2: 🚀 AI TRIP PLANNER (CORE GENERATOR)
# ----------------------------------------------------
elif "Planner" in st.session_state.nav_page:
    st.markdown("## 🚀 AI Trip Architect")
    st.caption("Craft your dream itinerary with interactive mapping and student budget optimization.")

    col_input, col_view = st.columns([4, 6], gap="large")

    with col_input:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.markdown("#### 🧭 Trip Parameters")

        default_dest = st.session_state.get("quick_dest", "Kyoto, Japan")
        default_days = st.session_state.get("quick_days", 3)

        destination = st.text_input("📍 Destination", value=default_dest, placeholder="e.g. Kyoto, Japan")

        col_d, col_b = st.columns(2)
        with col_d:
            days = st.slider("📅 Duration (Days)", min_value=1, max_value=14, value=default_days)
        with col_b:
            budget_level = st.selectbox("💰 Budget Tier", ["Student (Low)", "Moderate", "Luxury"])

        col_c, col_a = st.columns([1, 2])
        with col_c:
            currency = st.selectbox("Currency", ["USD ($)", "INR (₹)", "EUR (€)", "GBP (£)", "JPY (¥)"])
        with col_a:
            budget_amount = st.text_input("Cap Amount (Optional)", placeholder="e.g. 500 or 25000")

        selected_interests = st.multiselect(
            "❤️ Vibe & Interests",
            ["Street Food", "History & Shrines", "Nature & Trekking", "Nightlife", "Museums", "Adventure", "Cute Cafes", "Photography"],
            default=["Street Food", "History & Shrines"]
        )

        must_visit = st.text_input("📍 Must-Visit Place (Optional)", placeholder="e.g. Fushimi Inari Taisha")

        col_p, col_acc = st.columns(2)
        with col_p:
            pace = st.selectbox("⚡ Pace", ["Balanced", "Relaxed", "Packed Action"])
        with col_acc:
            accommodation = st.selectbox("🏨 Stay Style", ["Hostel Dorm", "Private Hostel", "Airbnb", "Budget Hotel"])

        st.markdown("<br>", unsafe_allow_html=True)
        generate_clicked = st.button("🚀 Generate Itinerary", use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with col_view:
        if generate_clicked and destination:
            with st.spinner("✨ Architecting your trip, calculating budget, and geocoding landmarks..."):
                response = generate_trip_itinerary(
                    destination, days, budget_level, budget_amount, currency.split()[0],
                    selected_interests, must_visit, pace, accommodation
                )
                if response:
                    st.session_state.current_destination = destination
                    if "LANDMARKS:" in response:
                        parts = response.split("LANDMARKS:")
                        st.session_state.itinerary = parts[0].strip()
                        raw_lm = parts[1].strip().split(",")
                        st.session_state.landmarks = [l.strip().rstrip('.') for l in raw_lm if l.strip()]
                    else:
                        st.session_state.itinerary = response.strip()
                        st.session_state.landmarks = [destination]

        if st.session_state.itinerary:
            dest_name = st.session_state.current_destination or destination
            
            # Map View
            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            st.markdown(f"### 📍 Interactive Map: {dest_name}")
            
            start_coords = get_coordinates(dest_name)
            if start_coords:
                m = folium.Map(location=start_coords, zoom_start=12, tiles="OpenStreetMap")
                folium.Marker(start_coords, popup=f"Destination: {dest_name}", tooltip=dest_name, icon=folium.Icon(color="red", icon="info-sign")).add_to(m)
                
                if must_visit:
                    mv_coords = get_coordinates(f"{must_visit}, {dest_name}")
                    if mv_coords:
                        folium.Marker(mv_coords, popup=f"Must Visit: {must_visit}", tooltip=must_visit, icon=folium.Icon(color="green", icon="star")).add_to(m)

                for place in st.session_state.landmarks:
                    l_coords = get_coordinates(f"{place}, {dest_name}")
                    if l_coords:
                        folium.Marker(l_coords, popup=place, tooltip=place, icon=folium.Icon(color="blue", icon="camera")).add_to(m)

                st_folium(m, use_container_width=True, height=360)
            else:
                st.info("Map coordinates could not be resolved automatically.")
            st.markdown('</div>', unsafe_allow_html=True)

            # Itinerary Markdown & Action Toolbar
            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            t_col1, t_col2, t_col3 = st.columns([1, 1, 1])
            
            with t_col1:
                pdf_data = create_itinerary_pdf(st.session_state.itinerary, dest_name)
                st.download_button(
                    label="📄 Download PDF",
                    data=pdf_data,
                    file_name=f"Trip_to_{dest_name}.pdf",
                    mime="application/pdf"
                )
            with t_col2:
                st.download_button(
                    label="📄 Download TXT",
                    data=st.session_state.itinerary,
                    file_name=f"Trip_to_{dest_name}.txt",
                    mime="text/plain"
                )
            with t_col3:
                if st.button("💾 Save to My Trips"):
                    st.session_state.saved_trips.append({
                        "destination": dest_name,
                        "days": days,
                        "itinerary": st.session_state.itinerary
                    })
                    st.success("Trip saved successfully!")

            st.markdown(f'<div class="highlight-box">{st.session_state.itinerary}</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class="glass-card" style="text-align: center; padding: 60px 20px;">
                <span style="font-size: 48px;">🗺️</span>
                <h3 style="color: #FFFFFF; margin-top: 10px;">Your Custom Itinerary Awaits</h3>
                <p style="color: #9CA3AF; font-size: 13px;">Choose your destination on the left and click "Generate Itinerary".</p>
            </div>
            """, unsafe_allow_html=True)


# ----------------------------------------------------
# PAGE 3: 💰 STUDENT BUDGET CALCULATOR
# ----------------------------------------------------
elif "Budget" in st.session_state.nav_page:
    st.markdown("## 💰 Student Trip Budget Calculator")
    st.caption("Estimate and balance your travel expenses so you never run out of funds abroad.")

    b_col1, b_col2 = st.columns([5, 5], gap="large")

    with b_col1:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        calc_days = st.number_input("📅 Trip Duration (Days)", min_value=1, max_value=30, value=4)
        curr_sym = st.selectbox("Currency", ["$", "₹", "€", "£", "¥"])

        trans_cost = st.slider(f"🚆 Flights / Trains ({curr_sym})", 0, 1000, 120, step=10)
        stay_cost = st.slider(f"🏨 Hostel / Stay Per Night ({curr_sym})", 5, 200, 25, step=5)
        food_cost = st.slider(f"🍜 Food Per Day ({curr_sym})", 5, 150, 20, step=5)
        act_cost = st.slider(f"🎟️ Passes & Entry Fees Per Day ({curr_sym})", 0, 100, 15, step=5)
        buffer_cost = st.slider(f"🛡️ Emergency Buffer ({curr_sym})", 0, 300, 50, step=10)
        st.markdown('</div>', unsafe_allow_html=True)

    with b_col2:
        total_stay = stay_cost * max(calc_days - 1, 1)
        total_food = food_cost * calc_days
        total_act = act_cost * calc_days
        grand_total = trans_cost + total_stay + total_food + total_act + buffer_cost
        daily_avg = grand_total / calc_days

        st.markdown(f"""
        <div class="glass-card" style="border-left: 5px solid #FF5E36;">
            <p style="color: #9CA3AF; font-size: 12px; margin: 0; text-transform: uppercase;">Estimated Total</p>
            <h1 style="color: #FFFFFF; font-size: 42px; font-weight: 800; margin: 5px 0;">{curr_sym}{grand_total:,.0f}</h1>
            <p style="color: #06B6D4; font-weight: bold; font-size: 14px;">Average {curr_sym}{daily_avg:,.2f} / day</p>
            <hr style="border-color: rgba(255,255,255,0.08); margin: 15px 0;" />
            <h4 style="color: #FFA000; font-size: 14px; margin-bottom: 8px;">💡 Student Money-Saving Cheatsheet:</h4>
            <ul style="color: #D1D5DB; font-size: 12px; line-height: 1.7; padding-left: 18px;">
                <li>Always carry your Student ID for 20-50% off museums and monuments.</li>
                <li>Take overnight sleeper trains to save on one full night of accommodation.</li>
                <li>Shop at local university cafeterias and evening discount street markets.</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)


# ----------------------------------------------------
# PAGE 4: 🎒 SMART PACKING CHECKLIST
# ----------------------------------------------------
elif "Packing" in st.session_state.nav_page:
    st.markdown("## 🎒 Smart Student Packing Checklist")
    st.caption("Interactive checklist saved dynamically to your current session.")

    total_items = len(st.session_state.packing_items)
    checked_count = sum(1 for v in st.session_state.packing_items.values() if v)
    pct = int((checked_count / total_items) * 100) if total_items > 0 else 0

    st.progress(pct / 100.0, text=f"📦 {pct}% Packed ({checked_count}/{total_items} items)")

    col_add, col_list = st.columns([4, 6], gap="large")

    with col_add:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.markdown("#### ➕ Add Custom Item")
        new_item = st.text_input("Item Name", placeholder="e.g. Earplugs, Swimsuit")
        if st.button("Add to List") and new_item:
            st.session_state.packing_items[new_item] = False
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    with col_list:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        for item, checked in list(st.session_state.packing_items.items()):
            new_checked = st.checkbox(item, value=checked, key=f"pack_{item}")
            st.session_state.packing_items[item] = new_checked
        st.markdown('</div>', unsafe_allow_html=True)


# ----------------------------------------------------
# PAGE 5: 📂 SAVED TRIPS
# ----------------------------------------------------
elif "Saved" in st.session_state.nav_page:
    st.markdown("## 📂 My Saved Itineraries")
    st.caption("Access and export all the trips you have saved.")

    if not st.session_state.saved_trips:
        st.info("You haven't saved any trips yet. Generate a trip in the AI Planner and click 'Save to My Trips'!")
    else:
        for idx, trip in enumerate(st.session_state.saved_trips):
            with st.expander(f"📍 {trip['destination']} ({trip['days']} Days)", expanded=True):
                st.markdown(trip['itinerary'])
                pdf_bytes = create_itinerary_pdf(trip['itinerary'], trip['destination'])
                st.download_button(
                    f"📄 Download PDF ({trip['destination']})",
                    data=pdf_bytes,
                    file_name=f"Saved_Trip_{trip['destination']}.pdf",
                    mime="application/pdf",
                    key=f"saved_dl_{idx}"
                )