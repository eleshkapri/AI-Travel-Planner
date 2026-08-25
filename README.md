# 🌍 AI Travel Planner

A smart, budget-friendly travel itinerary generator built for students. This application leverages the power of **Generative AI (Llama 3 via Groq)** to create personalized day-by-day travel plans and visualizes them on an interactive map using **Folium**.

## ✨ Features

* **🤖 AI-Powered Itineraries:** Generates detailed, day-by-day trip plans based on your destination, budget, and interests using the Llama 3.1 70B model.
* **📍 Interactive Map:** Automatically pins your destination, specific "Must Visit" spots, and AI-suggested landmarks on a dynamic map.
* **💰 Budget Management:** Input your budget tier (Student, Moderate, Luxury) or a specific amount, and get a breakdown of estimated costs.
* **⬇️ Export Options:** Download your complete itinerary as a formatted **Text file** (best for keeping emojis) or a clean **PDF**.
* **⚡ High Performance:** Uses caching strategies to ensure maps load instantly after the first search.

## 🛠️ Tech Stack

* **Frontend:** [Streamlit](https://streamlit.io/)
* **AI Model:** Llama 3.1 70B (via [Groq API](https://groq.com/))
* **Mapping:** Folium & Streamlit-Folium
* **Geocoding:** Geopy (Nominatim API)
* **PDF Generation:** FPDF

## 📂 Project Structure

```text
AI_Travel_Planner/
├── .streamlit/
│   └── secrets.toml      # API Keys (Not pushed to GitHub)
├── venv/                 # Virtual Environment
├── app.py                # Main Application Logic
├── requirements.txt      # Project Dependencies
├── packages.txt          # System dependencies (optional for deployment)
├── LICENSE               # MIT License
└── README.md             # Project Documentation

```

## 🚀 Installation & Setup

Follow these steps to run the project locally on your machine.

### 1. Clone the Repository

```bash
git clone [https://github.com/eleshkapri/AI-Travel-Planner.git]
cd AI-Travel-Planner

```

### 2. Create a Virtual Environment (Recommended)

**Windows:**

```bash
python -m venv venv
.\venv\Scripts\activate

```

**Mac/Linux:**

```bash
python3 -m venv venv
source venv/bin/activate

```

### 3. Install Dependencies

```bash
pip install -r requirements.txt

```

### 4. Set up API Keys

1. Get your free API Key from [Groq Cloud Console](https://console.groq.com/keys).
2. Create a folder named `.streamlit` in the root directory.
3. Inside it, create a file named `secrets.toml`.
4. Add your key like this:
```toml
GROQ_API_KEY = "gsk_your_actual_api_key_here"

```



### 5. Run the Application

```bash
streamlit run app.py

```

## 📸 Screenshots

![image alt](https://github.com/eleshkapri/AI-Travel-Planner/blob/cc9f7003ae8aad6e6b9338c229987525e4f82d4f/Screenshot%202026-01-11%20012005.png)

![image alt](https://github.com/eleshkapri/AI-Travel-Planner/blob/cc9f7003ae8aad6e6b9338c229987525e4f82d4f/Screenshot%202026-01-11%20012016.png)
