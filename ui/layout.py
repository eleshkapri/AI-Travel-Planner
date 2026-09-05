# -*- coding: utf-8 -*-
"""
RoamAI Page Layout & View Module.
Pure Python HTML template rendering engine.
"""
from ui.styles import APP_CSS
from ui.scripts import APP_JS

_HTML_TEMPLATE = r"""<!DOCTYPE html>
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
        } else {
          document.documentElement.classList.remove('light-theme');
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
  <!-- Google Fonts (Playfair Display for Everest editorial titles & Plus Jakarta Sans) -->
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,500;0,600;0,700;1,500;1,600&family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">

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

  <!-- Vanilla Tilt (3D Card Physics) -->
  <script src="https://cdnjs.cloudflare.com/ajax/libs/vanilla-tilt/1.8.1/vanilla-tilt.min.js" defer></script>

  <style id="roamaiAppStyles">
/* __ROAM_APP_CSS__ */
</style>
<body class="min-h-screen flex flex-col antialiased relative">
  <!-- Top Global Expedition Progress Bar (Everest #progress Parity) -->
  <div id="progress" aria-hidden="true"><i id="topProgressFill"></i></div>

  <!-- ==================== THEATRICAL EXPEDITION PRELOADER (#veil) ==================== -->
  <div id="veil" role="button" tabindex="0" aria-label="Begin expedition" onclick="dismissVeil()">
    <!-- Theatrical Drama Curtain Panels (Left & Right Parting Wings) -->
    <div class="veil-curtain veil-curtain-left"><div class="curtain-fringe"></div></div>
    <div class="veil-curtain veil-curtain-right"><div class="curtain-fringe"></div></div>

    <!-- Four-Corner Travel Telemetry & Global Coordinates -->
    <div class="veil-decor veil-decor-tl">✈️ 120+ GLOBAL DESTINATIONS · 9 CURRENCIES</div>
    <div class="veil-decor veil-decor-tr">🧭 REAL-TIME AI ITINERARY GENERATOR</div>
    <div class="veil-decor veil-decor-bl">🎒 SMART PACKING & STUDENT SAVINGS</div>
    <div class="veil-decor veil-decor-br">📍 INTERACTIVE GPS MAPPING · ROAMAI</div>

    <!-- Atmospheric Ambient Glow & Celestial Astrolabe Orbital Rings -->
    <div class="veil-glow"></div>
    <div class="veil-rings"></div>

    <!-- Architectural Frosted Glass Central Card -->
    <div class="veil-card">
      <!-- Signature RoamAI Travel Flight Badge -->
      <div class="veil-emblem">
        <div class="veil-emblem-box">
          <div class="veil-emblem-inner">
            <span class="veil-plane">✈️</span>
          </div>
        </div>
      </div>
      <div class="mark">✦ THE EXPEDITION · STUDENT TRAVEL ✦</div>
      <div class="t">RoamAI</div>
      <div class="st">wanderlust architect</div>
      <div class="bar"><i id="veilBar"></i></div>
      <div class="s" id="veilStatus">✈️ PLOTTING EXPEDITION FLIGHT CORRIDORS · 120+ COUNTRIES</div>
      <button class="go" id="veilBtn" onclick="dismissVeil(event)">
        <span class="pi">✈️</span>
        BEGIN EXPEDITION
      </button>
      <div class="sndh">NEXT-GEN AI TRAVEL PLANNER · WORLDWIDE ADVENTURES</div>
    </div>
  </div>

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
          <span id="brandModePill" class="hidden sm:inline-block text-[9px] sm:text-[10px] font-bold tracking-widest px-1.5 py-0.5 rounded-full bg-coralPrimary/20 text-coralPrimary border border-coralPrimary/30 uppercase transition">Student</span>
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
        
        <!-- Global Student Mode Switcher (Site-Wide) -->
        <button
          id="navStudentModeToggle"
          type="button"
          onclick="toggleGlobalStudentMode()"
          class="px-2.5 sm:px-3 py-1.5 rounded-xl border text-[10px] sm:text-xs font-extrabold transition flex items-center gap-1.5 shadow-sm shrink-0 itin-mode-btn-student"
          title="Toggle Student Mode vs Standard Traveler Mode across the whole site"
        >
          <span id="navStudentModeIcon">🎒</span>
          <span id="navStudentModeText" class="hidden md:inline">Student: ON</span>
        </button>

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
            <option value="INR" data-flag="🇮🇳" data-curr="INR" data-sym="₹" data-name="India" selected>INR ₹</option>
            <option value="USD" data-flag="🇺🇸" data-curr="USD" data-sym="$" data-name="United States">USD $</option>
            <option value="EUR" data-flag="🇪🇺" data-curr="EUR" data-sym="€" data-name="Europe">EUR €</option>
            <option value="GBP" data-flag="🇬🇧" data-curr="GBP" data-sym="£" data-name="United Kingdom">GBP £</option>
            <option value="JPY" data-flag="🇯🇵" data-curr="JPY" data-sym="¥" data-name="Japan">JPY ¥</option>
            <option value="AUD" data-flag="🇦🇺" data-curr="AUD" data-sym="A$" data-name="Australia">AUD A$</option>
            <option value="CAD" data-flag="🇨🇦" data-curr="CAD" data-sym="C$" data-name="Canada">CAD C$</option>
            <option value="AED" data-flag="🇦🇪" data-curr="AED" data-sym="AED" data-name="UAE">AED</option>
            <option value="THB" data-flag="🇹🇭" data-curr="THB" data-sym="฿" data-name="Thailand">THB ฿</option>
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
      <div class="relative rounded-3xl overflow-hidden glass-card p-5 sm:p-10 lg:p-14 border border-white/15 shadow-2xl nelson-reveal">
        <div class="grid grid-cols-1 lg:grid-cols-12 gap-8 lg:gap-10 items-center">
          
          <!-- Hero Left Column -->
          <div class="lg:col-span-7 space-y-5 sm:space-y-6">
            <div class="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-white/5 border border-white/10 text-[10px] sm:text-xs font-semibold shadow-inner max-w-full">
              <span class="star-mark">✦</span>
              <span id="heroBadgeText" class="text-white tracking-widest font-mono uppercase text-[10px]">THE EXPEDITION · STUDENT TRAVEL</span>
              <span class="text-gray-500 hidden sm:inline">•</span>
              <span class="hidden sm:inline text-amber-300 font-bold">120+ COUNTRIES</span>
            </div>

            <h1 class="text-3xl sm:text-5xl lg:text-6xl font-extrabold tracking-tight text-white leading-[1.15]">
              <span id="heroMainHeading" class="nelson-line-reveal inline-block font-serif italic font-semibold">Plan Epic Adventures</span> <br/>
              <span class="bg-clip-text text-transparent bg-gradient-to-r from-coralPrimary via-amberAccent to-cyanAccent animate-text-shimmer">
                On Any Budget in Seconds.
              </span>
            </h1>

            <p id="heroDescText" class="text-gray-300 text-xs sm:text-base leading-relaxed max-w-xl">
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
                <p id="heroTrustStudents" class="text-xs text-gray-400 font-medium">For All Students</p>
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
                    <p id="heroPreviewEdition" class="text-[11px] text-gray-300">3 Days • Student Low Budget</p>
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
      <div class="space-y-8 nelson-reveal">
        <div class="flex flex-col lg:flex-row lg:items-end justify-between gap-6 pb-2 border-b border-white/10">
          <div class="space-y-1">
            <div class="flex items-center gap-2">
              <span class="text-xs font-bold uppercase tracking-wider text-coralPrimary">Curated For Students</span>
              <span class="text-[10px] font-extrabold px-2.5 py-0.5 rounded-full bg-emeraldAccent/20 text-emeraldAccent border border-emeraldAccent/30">16 Destinations</span>
            </div>
            <h2 class="text-2xl sm:text-3xl font-extrabold text-white nelson-line-reveal inline-block">🔥 Trending Student Destinations</h2>
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
      <div class="space-y-8 nelson-reveal">
        <div class="text-center max-w-2xl mx-auto space-y-2">
          <span class="text-xs font-bold uppercase tracking-wider text-cyanAccent">Architected For Gen-Z & Students</span>
          <h2 class="text-3xl font-extrabold text-white nelson-line-reveal inline-block">Superpowers That Make Travel Effortless</h2>
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

        <!-- Loading State (Everest Expedition Architect) -->
        <div id="plannerLoading" class="hidden glass-card rounded-3xl p-10 sm:p-14 text-center space-y-5 border shadow-2xl relative overflow-hidden" style="border-color: var(--gold-line);">
          <!-- Orbital ring background -->
          <div style="position: absolute; inset: 0; display: flex; align-items: center; justify-content: center; pointer-events: none;">
            <div style="width: 220px; height: 220px; border-radius: 50%; border: 1px solid var(--gold-line); animation: veilOrbitSpin 14s linear infinite;"></div>
          </div>
          <div style="position: absolute; inset: 0; display: flex; align-items: center; justify-content: center; pointer-events: none;">
            <div style="width: 150px; height: 150px; border-radius: 50%; border: 1px dashed var(--gold-line); opacity: 0.5; animation: veilOrbitSpin 9s linear infinite reverse;"></div>
          </div>
          <div class="star-mark text-3xl mx-auto relative" style="animation: pulseStar 1.8s infinite; z-index: 2; color: var(--gold);">✦</div>
          <h3 class="text-xl sm:text-2xl font-serif italic relative" style="z-index: 2; color: var(--pearl);">Architecting Expedition Blueprint...</h3>
          <div class="mx-auto relative" style="width: min(280px, 85%); height: 2px; background: var(--panel-line); overflow: hidden; margin: 0 auto; border-radius: 2px; z-index: 2;">
            <i class="block h-full w-full relative overflow-hidden" style="background: linear-gradient(90deg, var(--gold), var(--orange));">
              <span class="absolute inset-0" style="background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.6), transparent); animation: barSheen 1.8s linear infinite; width: 70px;"></span>
            </i>
          </div>
          <p id="plannerLoadingStatus" class="eyebrow-tracked text-[11px] animate-pulse tracking-widest relative" style="z-index: 2; color: var(--gold);">
            ✦ PREPARING TERRAIN &amp; REGIONAL WEATHER · GROQ AI
          </p>
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
              <div id="viewModeSwitcherContainer" class="flex items-center bg-spaceDark/80 p-1 rounded-xl border border-white/10 text-xs shadow-inner transition">
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
              <span class="text-xl" id="itineraryTipsIcon">🎒</span>
              <h4 id="itineraryTipsTitle" class="text-sm sm:text-base font-bold text-white">Essential Student Travel Hacks & Safety</h4>
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
        <h2 id="budgetPageTitle" class="text-3xl font-extrabold text-white">💰 Student Trip Budget Calculator</h2>
        <p class="text-gray-400 text-sm">Estimate and balance your trip expenses synced to your selected region currency.</p>
      </div>

      <div class="grid grid-cols-1 md:grid-cols-12 gap-8">
        <div class="md:col-span-7 glass-card p-6 sm:p-8 rounded-3xl border border-white/10 space-y-5">
          <div class="grid grid-cols-2 gap-4">
            <div><label class="text-xs font-bold text-gray-300">Days</label><input type="number" id="bDays" value="4" min="1" max="90" class="w-full px-3 py-2 bg-spaceDark border border-white/15 rounded-xl text-sm text-white" oninput="debouncedCalcBudget()" /></div>
            <div><label class="text-xs font-bold text-gray-300">Region Currency</label><input type="text" id="bCurrDisplay" readonly value="INR (₹)" class="w-full px-3 py-2 bg-spaceDark/60 border border-white/10 rounded-xl text-sm text-amberAccent font-bold" /></div>
          </div>
          <div><div class="flex justify-between text-xs text-gray-300"><span>🚆 Flights / Trains</span><span id="bValTrans">₹3,000</span></div><input type="range" id="bTrans" min="0" max="50000" step="500" value="3000" class="w-full accent-coralPrimary cursor-pointer" oninput="debouncedCalcBudget()" /></div>
          <div><div class="flex justify-between text-xs text-gray-300"><span id="budgetStayLabel">🏨 Hostel (Per Night)</span><span id="bValStay">₹800</span></div><input type="range" id="bStay" min="200" max="10000" step="100" value="800" class="w-full accent-cyanAccent cursor-pointer" oninput="debouncedCalcBudget()" /></div>
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
        <h2 id="packingPageTitle" class="text-3xl font-extrabold text-white">Smart Student Packing Checklist</h2>
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
              <option id="packVibeHostelOption" value="hostel">🎒 Classic Backpacker & Hostel Dorm</option>
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
          <span class="w-1.5 h-1.5 rounded-full bg-emeraldAccent animate-pulse"></span> <span id="footerStudentPill">Free for Students</span>
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

  <!-- Nelson Travel Inspired Luxury Magnetic Cursor Follower (Desktop Only) -->
  <div id="nelsonCursorDot" class="cursor-hidden"></div>
  <div id="nelsonCursorRing" class="cursor-hidden"></div>

  <!-- Everest Inspired Expedition Telemetry Dock -->
  <div id="expeditionHud" role="complementary" aria-label="Expedition telemetry">
    <div class="cell">
      <div class="k">REGION</div>
      <div class="v" id="hudRegion">INR <small>₹</small></div>
    </div>
    <div class="cell">
      <div class="k">EXPEDITION</div>
      <div class="v" id="hudMode">Student</div>
    </div>
    <div class="cell hide-mob">
      <div class="k">HOTSPOTS</div>
      <div class="v">16 <small>Curated</small></div>
    </div>
    <div class="cell cursor-pointer hover:opacity-85 transition" onclick="switchPage('planner')" title="Click to plan your destination">
      <div class="k">DESTINATION</div>
      <div class="v" id="hudCoords"><span class="text-amber-400 font-bold flex items-center gap-1 animate-pulse">Plan Trip ✈️</span></div>
    </div>
    <div class="cell hide-mob">
      <div class="k">LOCAL TIME</div>
      <div class="v" id="hudTime">--:--</div>
    </div>
  </div>

  <!-- ==================== JAVASCRIPT LOGIC ==================== -->
  <script id="roamaiAppScript">
/* __ROAM_APP_JS__ */
</script>
</body>
</html>
"""

def get_page_html() -> str:
    """Return the complete, self-contained single-page application HTML."""
    from ui.styles import get_app_css
    from ui.scripts import get_app_js
    return _HTML_TEMPLATE.replace("/* __ROAM_APP_CSS__ */", get_app_css()).replace("/* __ROAM_APP_JS__ */", get_app_js())

