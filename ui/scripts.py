# -*- coding: utf-8 -*-
"""
RoamAI Client-side Interactive Engine Module.
Pure Python representation of client-side application logic, theme engine,
Student Mode toggle, Leaflet map controller, and PDF generation.
"""

APP_JS = r"""// ========================================================
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
      if (window.updateExpeditionHud) window.updateExpeditionHud();
    }

    function switchPage(page, saveState = true) {
      if (typeof window.triggerTopProgress === 'function') {
        window.triggerTopProgress(40);
        setTimeout(() => window.triggerTopProgress(100), 180);
      }
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

    // ========================================================
    // GLOBAL SITE-WIDE STUDENT MODE ENGINE (PERSISTED)
    // ========================================================
    let siteWideStudentMode = true;

    function initSiteWideStudentMode() {
      try {
        const saved = localStorage.getItem('roamai_student_mode');
        if (saved !== null) {
          siteWideStudentMode = (saved === 'true');
        } else {
          siteWideStudentMode = true;
        }
      } catch (e) {
        siteWideStudentMode = true;
      }
      applySiteWideStudentMode(siteWideStudentMode, false);
    }

    function toggleGlobalStudentMode() {
      siteWideStudentMode = !siteWideStudentMode;
      try {
        localStorage.setItem('roamai_student_mode', siteWideStudentMode ? 'true' : 'false');
      } catch (e) {}
      applySiteWideStudentMode(siteWideStudentMode, true);
    }

    function applySiteWideStudentMode(isStudent, showNotification = true) {
      siteWideStudentMode = isStudent;

      // 1. Header Navbar Elements
      const brandPill = document.getElementById('brandModePill');
      if (brandPill) {
        if (isStudent) {
          brandPill.innerText = 'Student';
          brandPill.className = 'hidden sm:inline-block text-[9px] sm:text-[10px] font-bold tracking-widest px-1.5 py-0.5 rounded-full bg-coralPrimary/20 text-coralPrimary border border-coralPrimary/30 uppercase transition';
        } else {
          brandPill.innerText = 'Traveler';
          brandPill.className = 'hidden sm:inline-block text-[9px] sm:text-[10px] font-bold tracking-widest px-1.5 py-0.5 rounded-full bg-blue-500/20 text-blue-400 border border-blue-500/30 uppercase transition';
        }
      }

      const navBtn = document.getElementById('navStudentModeToggle');
      const navIcon = document.getElementById('navStudentModeIcon');
      const navText = document.getElementById('navStudentModeText');
      if (navBtn) {
        if (isStudent) {
          navBtn.className = 'px-2.5 sm:px-3 py-1.5 rounded-xl border text-[10px] sm:text-xs font-extrabold transition flex items-center gap-1.5 shadow-sm shrink-0 itin-mode-btn-student';
          if (navIcon) navIcon.innerText = '🎒';
          if (navText) navText.innerText = 'Student: ON';
        } else {
          navBtn.className = 'px-2.5 sm:px-3 py-1.5 rounded-xl border text-[10px] sm:text-xs font-extrabold transition flex items-center gap-1.5 shadow-sm shrink-0 itin-mode-btn-traveler';
          if (navIcon) navIcon.innerText = '✈️';
          if (navText) navText.innerText = 'Standard Traveler';
        }
      }

      // 2. Home Page Elements
      const heroBadge = document.getElementById('heroBadgeText');
      if (heroBadge) heroBadge.innerText = isStudent ? 'Next-Gen Student Travel' : 'Next-Gen Global Travel';

      const heroHeading = document.getElementById('heroMainHeading');
      if (heroHeading) heroHeading.innerText = isStudent ? 'Plan Epic Student Adventures' : 'Plan Curated Travel Adventures';

      const heroDesc = document.getElementById('heroDescText');
      if (heroDesc) {
        heroDesc.innerText = isStudent
          ? 'Day-by-day itineraries, verified local student discounts, interactive 3D map pins, and offline PDF exports powered by high-speed Groq AI.'
          : 'Day-by-day itineraries, boutique & budget stays, interactive 3D map pins, and offline PDF exports powered by high-speed Groq AI.';
      }

      const heroTrust = document.getElementById('heroTrustStudents');
      if (heroTrust) heroTrust.innerText = isStudent ? 'For All Students' : 'For All Travelers';

      const heroPrevSub = document.getElementById('heroPreviewEdition');
      if (heroPrevSub) heroPrevSub.innerText = isStudent ? '3 Days • Student Low Budget' : '3 Days • Curated Traveler Edition';

      const hotspotBadge = document.getElementById('hotspotSectionBadge');
      if (hotspotBadge) hotspotBadge.innerText = isStudent ? 'Curated For Students' : 'Curated For Travelers';

      const hotspotTitle = document.getElementById('hotspotSectionTitle');
      if (hotspotTitle) hotspotTitle.innerText = isStudent ? '🔥 Trending Student Destinations' : '🔥 Trending Travel Destinations';

      const hotspotDesc = document.getElementById('hotspotSectionDesc');
      if (hotspotDesc) {
        hotspotDesc.innerText = isStudent
          ? 'Classified by National (India) and International hotspots with authentic student discounts & budget estimates'
          : 'Classified by National (India) and International hotspots with curated highlights & regional budget estimates';
      }

      const footerPill = document.getElementById('footerStudentPill');
      if (footerPill) footerPill.innerText = isStudent ? 'Free for Students' : 'Free for All Travelers';

      // 3. Budget Calculator Page
      const budgetTitle = document.getElementById('budgetPageTitle');
      if (budgetTitle) budgetTitle.innerText = isStudent ? '💰 Student Trip Budget Calculator' : '💰 Trip Budget Calculator';

      const stayLabel = document.getElementById('budgetStayLabel');
      if (stayLabel) stayLabel.innerText = isStudent ? '🏨 Hostel (Per Night)' : '🏨 Hotel / Stay (Per Night)';

      const bStay = document.getElementById('bStay');
      const bTrans = document.getElementById('bTrans');
      const bFood = document.getElementById('bFood');
      const bAct = document.getElementById('bAct');
      if (bStay && bTrans && bFood && bAct) {
        const reg = (typeof REGIONS !== 'undefined' && REGIONS[activeRegionKey]) ? REGIONS[activeRegionKey] : { defaults: { trans: 3000, stay: 800, food: 600, act: 400 } };
        if (isStudent) {
          bStay.value = reg.defaults.stay;
          bTrans.value = reg.defaults.trans;
          bFood.value = reg.defaults.food;
          bAct.value = reg.defaults.act;
        } else {
          bStay.value = Math.round(reg.defaults.stay * 2.75);
          bTrans.value = Math.round(reg.defaults.trans * 1.5);
          bFood.value = Math.round(reg.defaults.food * 1.6);
          bAct.value = Math.round(reg.defaults.act * 2.0);
        }
        if (typeof calcBudget === 'function') calcBudget();
      }

      // 4. Packing List Page
      const packTitle = document.getElementById('packingPageTitle');
      if (packTitle) packTitle.innerText = isStudent ? 'Smart Student Packing Checklist' : 'Smart Travel Packing Checklist';

      const packHostelOpt = document.getElementById('packVibeHostelOption');
      if (packHostelOpt) packHostelOpt.innerText = isStudent ? '🎒 Classic Backpacker & Hostel Dorm' : '🏨 Hotel, Resort & Boutique Stay';

      // 5. Trip Architect Sidebar & Active Itinerary
      onStudentModeToggle(isStudent, true);
      if (window.updateExpeditionHud) window.updateExpeditionHud();

      if (showNotification) {
        showToast(isStudent ? 'Site transformed to 🎒 Student Explorer Mode' : 'Site transformed to ✨ Standard Traveler Mode', 'info', 2200);
      }
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
      const tierSelect = document.getElementById('plannerTier');

      // 1. Update Badge, Icon, Description & Card Styling
      if (isStudent) {
        if (badge) {
          badge.innerText = 'ON';
          badge.className = 'text-[10px] font-extrabold px-2.5 py-0.5 rounded-full student-mode-badge-on uppercase tracking-wider shadow-sm';
        }
        if (icon) icon.innerText = '🎒';
        if (desc) desc.innerText = 'Enables student discounts, hostel stays & budget savings hacks';
        if (card) {
          card.className = 'p-3.5 rounded-2xl student-card-active border flex items-center justify-between gap-3 shadow-inner transition';
        }
      } else {
        if (badge) {
          badge.innerText = 'OFF';
          badge.className = 'text-[10px] font-extrabold px-2.5 py-0.5 rounded-full student-mode-badge-off uppercase tracking-wider shadow-sm';
        }
        if (icon) icon.innerText = '✈️';
        if (desc) desc.innerText = 'Standard curated travel: boutique stays, gastronomy, skip-the-line admissions';
        if (card) {
          card.className = 'p-3.5 rounded-2xl student-card-inactive border flex items-center justify-between gap-3 shadow-inner transition';
        }
      }

      // 2. Dynamically update the TIER select options based on Student Mode!
      if (tierSelect) {
        const currentTier = tierSelect.value;
        if (isStudent) {
          tierSelect.innerHTML = `
            <option value="Student (Low)">Student (Low)</option>
            <option value="Moderate Backpacker">Moderate Backpacker</option>
            <option value="Luxury Student">Luxury Student</option>
          `;
          if (currentTier === 'Economy Traveler' || currentTier === 'Budget Traveler') {
            tierSelect.value = 'Student (Low)';
          } else if (currentTier === 'Comfort Explorer' || currentTier === 'Moderate Explorer') {
            tierSelect.value = 'Moderate Backpacker';
          } else if (currentTier === 'Boutique Luxury' || currentTier === 'Luxury Traveler') {
            tierSelect.value = 'Luxury Student';
          } else {
            tierSelect.value = 'Student (Low)';
          }
        } else {
          tierSelect.innerHTML = `
            <option value="Economy Traveler">Economy Traveler</option>
            <option value="Comfort Explorer">Comfort Explorer</option>
            <option value="Boutique Luxury">Boutique Luxury</option>
          `;
          if (currentTier === 'Student (Low)') {
            tierSelect.value = 'Economy Traveler';
          } else if (currentTier === 'Moderate Backpacker') {
            tierSelect.value = 'Comfort Explorer';
          } else if (currentTier === 'Luxury Student') {
            tierSelect.value = 'Boutique Luxury';
          } else {
            tierSelect.value = 'Economy Traveler';
          }
        }
      }

      // 3. IMMEDIATELY update and re-render the active itinerary if one is loaded!
      if (currentTrip) {
        if (!currentTrip.trip_summary) currentTrip.trip_summary = {};
        const modeChanged = (currentTrip.trip_summary.student_mode !== isStudent);
        currentTrip.trip_summary.student_mode = isStudent;
        currentTrip.student_mode = isStudent;
        renderItineraryBlueprint(currentTrip);
        if (modeChanged) {
          showToast(isStudent ? 'Adapted to 🎓 Student Explorer Mode' : 'Adapted to ✨ Standard Traveler Mode', 'info', 2000);
        }
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

          window.activeExpeditionDestination = null;
          window.activeExpeditionCoords = null;
          if (window.updateExpeditionHud) window.updateExpeditionHud();

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

      if (typeof VanillaTilt !== 'undefined') {
        VanillaTilt.init(document.querySelectorAll('.hotspot-card:not(.hidden)[data-tilt]'));
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

      const coordsMap = {
        'Goa, India': '15.29°N · 74.12°E',
        'Manali, Himachal Pradesh, India': '32.24°N · 77.19°E',
        'Jaipur, Rajasthan, India': '26.91°N · 75.78°E',
        'Rishikesh, Uttarakhand, India': '30.08°N · 78.26°E',
        'Varanasi, Uttar Pradesh, India': '25.31°N · 82.97°E',
        'Munnar, Kerala, India': '10.08°N · 77.06°E',
        'Leh Ladakh, India': '34.15°N · 77.57°E',
        'Shillong, Meghalaya, India': '25.57°N · 91.89°E',
        'Tokyo, Japan': '35.67°N · 139.65°E',
        'Bali, Indonesia': '8.34°S · 115.09°E',
        'Bangkok, Thailand': '13.75°N · 100.50°E',
        'Rome, Italy': '41.90°N · 12.49°E',
        'Amsterdam, Netherlands': '52.36°N · 4.90°E',
        'Kyoto, Japan': '35.01°N · 135.76°E',
        'Paris, France': '48.85°N · 2.35°E',
        'Dubai, UAE': '25.20°N · 55.27°E'
      };
      const hudC = document.getElementById('hudCoords');
      if (hudC && coordsMap[dest]) hudC.innerText = coordsMap[dest];

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

      // Trigger Top Global Expedition Progress & Rotating Expedition Status
      if (typeof window.triggerTopProgress === 'function') {
        window.triggerTopProgress(25);
      }
      const loadingStatusEl = document.getElementById('plannerLoadingStatus');
      const telemetryStages = [
        '✦ CALIBRATING ROUTE ELEVATION & REGIONAL CLIMATE · GROQ AI',
        '✦ COMPUTING STUDENT BUDGET MULTIPLIERS & EXPENSES',
        '✦ GEOCODING INTERACTIVE GPS PINS & MAP POLYLINES',
        '✦ COMPOSING CIRCUIT BLUEPRINT & OFFLINE TRIP VAULT'
      ];
      let stageIdx = 0;
      let curProgress = 30;
      if (loadingStatusEl) loadingStatusEl.innerText = telemetryStages[0];
      const telemetryTimer = setInterval(() => {
        stageIdx = (stageIdx + 1) % telemetryStages.length;
        if (loadingStatusEl) loadingStatusEl.innerText = telemetryStages[stageIdx];
        curProgress = Math.min(92, curProgress + 18);
        if (typeof window.triggerTopProgress === 'function') {
          window.triggerTopProgress(curProgress);
        }
      }, 950);

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

        clearInterval(telemetryTimer);
        if (typeof window.triggerTopProgress === 'function') {
          window.triggerTopProgress(100);
        }
        document.getElementById('plannerLoading').classList.add('hidden');
        document.getElementById('plannerResults').classList.remove('hidden');
        window.activeExpeditionDestination = destination;
        if (window.updateExpeditionHud) window.updateExpeditionHud();
        showToast(`Itinerary for ${destination} generated successfully!`, 'success');
        setTimeout(() => {
          const resultsEl = document.getElementById('plannerResults');
          if (resultsEl) resultsEl.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }, 150);
      } catch (err) {
        clearInterval(telemetryTimer);
        if (typeof window.triggerTopProgress === 'function') {
          window.triggerTopProgress(100);
        }
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

    function sanitizeTipContent(raw) {
      let s = String(raw || '').trim();
      let prev = '';
      while (s !== prev) {
        prev = s;
        s = s.replace(/^[\s\-•*]*(?:💡|✨)?[\s\-•*]*/i, '')
             .replace(/^\*\*(?:Student Insider Hack|Traveler Pro Tip|Student Tip|Traveler Tip|Pro Tip|Insider Hack|Local Insider Tip):\*\*\s*/i, '')
             .replace(/^(?:Student Insider Hack|Traveler Pro Tip|Student Tip|Traveler Tip|Pro Tip|Insider Hack|Local Insider Tip)[:\* ]*\s*/i, '')
             .replace(/^\*\*|\*\*$/g, '')
             .trim();
      }
      return s;
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

    function getAdaptedBudget(tripData, isStudent) {
      const reg = (typeof REGIONS !== 'undefined' && REGIONS[activeRegionKey]) ? REGIONS[activeRegionKey] : { curr: 'INR' };
      const curr = (tripData && tripData.trip_summary && tripData.trip_summary.currency) ? tripData.trip_summary.currency : (reg ? reg.curr : 'INR');
      const multipliers = {
        "INR": 1.0, "USD": 0.012, "EUR": 0.011, "GBP": 0.0095, "JPY": 1.8,
        "AUD": 0.018, "CAD": 0.016, "AED": 0.044, "THB": 0.44
      };
      const m = multipliers[curr] || 1.0;
      const tier = (tripData && tripData.trip_summary && tripData.trip_summary.budget_level) ? tripData.trip_summary.budget_level : 'Standard';
      const tierMult = (tier.includes('Moderate') || tier.includes('Comfort')) ? 1.8 : ((tier.includes('Luxury') || tier.includes('Boutique')) ? 3.2 : 1.0);

      if (isStudent) {
        const stay = Math.round(800 * m * tierMult);
        const food = Math.round(500 * m * tierMult);
        const trans = Math.round(300 * m * tierMult);
        const total = stay + food + trans;
        return {
          curr,
          totalPerDay: total,
          main: `~${total.toLocaleString()} ${curr}`,
          detail: `(Stay: ~${stay.toLocaleString()} ${curr} • Food: ~${food.toLocaleString()} ${curr} • Transit: ~${trans.toLocaleString()} ${curr})`
        };
      } else {
        const stay = Math.round(2200 * m * tierMult);
        const food = Math.round(1000 * m * tierMult);
        const trans = Math.round(600 * m * tierMult);
        const total = stay + food + trans;
        return {
          curr,
          totalPerDay: total,
          main: `~${total.toLocaleString()} ${curr}`,
          detail: `(Stay: ~${stay.toLocaleString()} ${curr} • Food: ~${food.toLocaleString()} ${curr} • Transit: ~${trans.toLocaleString()} ${curr})`
        };
      }
    }

    function renderDayCard(d) {
      const isStudent = (currentTrip && currentTrip.trip_summary && currentTrip.trip_summary.student_mode !== false);
      const safeName = escapeHtml(d.landmarkName);
      const safeZone = escapeHtml(d.zone);
      let safeMorning = escapeHtml(d.morning);
      let safeAfternoon = escapeHtml(d.afternoon);
      let safeEvening = escapeHtml(d.evening);
      let rawCleanHack = sanitizeTipContent(d.hack);

      const budgetInfo = getAdaptedBudget(currentTrip, isStudent);
      const budgetMain = budgetInfo.main;
      const budgetDetail = budgetInfo.detail;

      // Cleanse and enrich content when switching between Student and Standard Traveler Modes
      if (!isStudent) {
        safeMorning = safeMorning
          .replace(/Flash your student ID card at the entry gate for 30% to 50% concession tickets\./gi, 'Pre-book priority admission online for effortless skip-the-line entry.')
          .replace(/Carry a refillable water bottle and flash your student ID card at ticket counters for instant 30% to 50% concession discounts\./gi, 'Reserve priority admission tickets online 48 hours in advance to bypass main queuing lines.')
          .replace(/indie backpacker/gi, 'panoramic boutique')
          .replace(/hostel/gi, 'hotel')
          .replace(/dorm/gi, 'private suite');

        safeAfternoon = safeAfternoon
          .replace(/Eat where local university students eat; follow the crowds to backstreet family-run kitchens for 50% cheaper authentic regional meals\./gi, 'Explore celebrated neighborhood family-run kitchens and historic culinary spots for authentic regional flavors.')
          .replace(/budget street food stall/gi, 'celebrated local kitchen & artisan eatery')
          .replace(/cheap student/gi, 'authentic regional');

        safeEvening = safeEvening
          .replace(/indie backpacker rooftop cafe/gi, 'scenic rooftop lounge')
          .replace(/communal hostel lounge/gi, 'serene heritage terrace lounge')
          .replace(/communal hostel hearth/gi, 'refined fireside terrace lounge')
          .replace(/hostel common room/gi, 'hotel lounge');

        if (rawCleanHack) {
          rawCleanHack = rawCleanHack
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

      let safeHack = escapeHtml(sanitizeTipContent(rawCleanHack));
      const safeJsName = d.landmarkName.replace(/'/g, "\'");

      let hackBoxHtml = '';
      if (safeHack) {
        if (isStudent) {
          hackBoxHtml = `
            <div class="p-3 rounded-xl tip-box-student flex items-start gap-2.5 shadow-sm">
              <span class="text-base leading-none select-none">💡</span>
              <div class="min-w-0">
                <strong class="font-bold tip-title">Student Insider Hack:</strong>
                <span class="tip-content text-xs ml-1">${safeHack}</span>
              </div>
            </div>`;
        } else {
          hackBoxHtml = `
            <div class="p-3 rounded-xl tip-box-traveler flex items-start gap-2.5 shadow-sm">
              <span class="text-base leading-none select-none">✨</span>
              <div class="min-w-0">
                <strong class="font-bold tip-title">Traveler Pro Tip:</strong>
                <span class="tip-content text-xs ml-1">${safeHack}</span>
              </div>
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
          ${budgetMain ? `<div class="flex items-center justify-between pt-1 text-[11px] text-gray-400"><span class="text-emeraldAccent font-semibold">💰 Target: ${budgetMain}</span><span class="text-gray-500 text-[10px]">${budgetDetail}</span></div>` : ''}
        </div>
      </div>`;
    }

    window.currentItineraryPhase = 'all';
    window.totalPhasesCount = 0;

    function renderItineraryBlueprint(data) {
      if (!data) return;
      const isStudentMode = (data.trip_summary ? data.trip_summary.student_mode !== false : true);
      const rawMd = data.itinerary || '';

      // 1. Render adaptive markdown into document view
      const docEl = document.getElementById('itineraryView');
      if (docEl) {
        let displayMd = rawMd;
        if (!isStudentMode) {
          displayMd = displayMd
            .replace(/^#\s+🌍\s*(\d+)-Day\s+Grand\s+Explorer:\s*/m, '# 🌍 $1-Day Curated Journey: ')
            .replace(/##\s+💰\s*Estimated\s+Student\s+Budget\s+Breakdown/gi, '## 💰 Estimated Travel Budget Breakdown')
            .replace(/##\s+🎒\s*Essential\s+Student\s+Tips/gi, '## 🗺️ Essential Travel Tips & Guidance')
            .replace(/Flash your student ID card at the entry gate for 30% to 50% concession tickets\./gi, 'Pre-book skip-the-line admissions online for effortless priority entry.')
            .replace(/Carry a refillable water bottle and flash your student ID card at ticket counters for instant 30% to 50% concession discounts\./gi, 'Reserve priority admission tickets online 48 hours in advance to bypass main queuing lines.')
            .replace(/Take shared local transit or split a shared cab from the main stand for a fraction of private taxi rates\. Keep local small change handy for vendors\./gi, 'Arrange dedicated private cabs or premium express transit for comfortable, efficient travel between sights.')
            .replace(/Check local transit timetables with your hostel reception the night before to catch early morning departures and beat tour crowds\./gi, 'Consult your hotel concierge for recommended excursion departure times to experience viewpoints at optimal lighting.')
            .replace(/Eat where local university students eat; follow the crowds to backstreet family-run kitchens for 50% cheaper authentic regional meals\./gi, 'Explore celebrated neighborhood family-run kitchens and historic culinary spots for authentic regional flavors.')
            .replace(/\*\*Student Insider Hack:\*\*/gi, '**Traveler Pro Tip:**')
            .replace(/\*\*Student Tip:\*\*/gi, '**Traveler Pro Tip:**')
            .replace(/Student Backpacker District/gi, 'Charming Bohemian Arts Quarter')
            .replace(/Youth Quarter/gi, 'Arts & Heritage Quarter')
            .replace(/indie backpacker rooftop cafe/gi, 'scenic panoramic rooftop lounge')
            .replace(/communal hostel lounge/gi, 'serene heritage terrace lounge');
        }
        docEl.innerHTML = safeMarkdown(displayMd);
      }

      // 2. Parse Markdown
      const parsed = parseItineraryMarkdown(rawMd);
      const daysCount = parsed.days.length || (data.trip_summary ? data.trip_summary.days : (data.days || 3));
      const markersCount = (data.markers ? data.markers.length : 0);
      const destination = (data.trip_summary ? data.trip_summary.destination : '') || (document.getElementById('plannerDest') ? document.getElementById('plannerDest').value : '');

      // Update Student Mode Button on Blueprint
      const studentBtn = document.getElementById('itineraryStudentModeBtn');
      const studentIcon = document.getElementById('itineraryStudentModeIcon');
      const studentText = document.getElementById('itineraryStudentModeText');
      const searchInputEl = document.getElementById('itinerarySearchInput');

      if (studentBtn) {
        if (isStudentMode) {
          studentBtn.className = 'px-3.5 py-1.5 rounded-xl text-xs font-extrabold flex items-center gap-1.5 border transition shadow-sm itin-mode-btn-student';
          if (studentIcon) studentIcon.innerText = '🎓';
          if (studentText) studentText.innerText = 'Student Mode: ON';
        } else {
          studentBtn.className = 'px-3.5 py-1.5 rounded-xl text-xs font-extrabold flex items-center gap-1.5 border transition shadow-sm itin-mode-btn-traveler';
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
        const budgetInfo = getAdaptedBudget(data, isStudentMode);
        const totalTripBudget = budgetInfo.totalPerDay * daysCount;
        metricBudget.innerText = `~${totalTripBudget.toLocaleString()} ${budgetInfo.curr} (${isStudentMode ? 'Student Tier' : 'Curated Tier'})`;
      }

      const subtitleEl = document.getElementById('itinerarySubtitle');
      if (subtitleEl) {
        subtitleEl.innerText = isStudentMode 
          ? '🎒 Student Explorer Edition • Youth Hostels, Concessions & Budget Slices'
          : '✨ Curated Traveler Edition • Boutique Stays, Gastronomy & Express Transit';
      }

      const tipsTitleEl = document.getElementById('itineraryTipsTitle');
      const tipsIconEl = document.getElementById('itineraryTipsIcon');
      if (tipsTitleEl) {
        tipsTitleEl.innerText = isStudentMode ? 'Essential Student Travel Hacks & Safety' : 'Essential Traveler Guidance & Local Tips';
      }
      if (tipsIconEl) {
        tipsIconEl.innerText = isStudentMode ? '🎒' : '🗺️';
      }

      const metricPhases = document.getElementById('metricPhases');
      if (metricPhases) {
        window.totalPhasesCount = parsed.phases.length;
        metricPhases.innerText = parsed.phases.length > 1 ? `${parsed.phases.length} Regional Circuits` : 'Direct Itinerary';
      }

      const mainHeading = document.getElementById('itineraryMainHeading');
      if (mainHeading && destination) {
        mainHeading.innerText = isStudentMode 
          ? `${destination} — ${daysCount} Days Blueprint (Student Explorer Edition)`
          : `${destination} — ${daysCount} Days Blueprint (Curated Traveler Edition)`;
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
          tipsContent.innerHTML = parsed.tips.map(rawTip => {
            let tip = rawTip;
            if (!isStudentMode) {
              tip = tip
                .replace(/Flash your student ID card at ticket counters for instant 30% to 50% concession discounts\./gi, 'Reserve priority admission tickets online 48 hours in advance to bypass ticketing queues.')
                .replace(/Flash your student ID at transit ticketing booths and monuments for 20% to 50% off\./gi, 'Book priority admissions online in advance to bypass main queuing lines.')
                .replace(/Stay in highly-rated youth hostels with social common areas to meet fellow explorers\./gi, 'Reserve verified boutique heritage hotels or trusted private guesthouses in advance.')
                .replace(/Stay in backpacker hostels.*$/gi, 'Book verified heritage hotels or boutique stays with private amenities.')
                .replace(/student/gi, 'traveler')
                .replace(/hostel/gi, 'hotel');
            }
            return `
              <div class="p-3 rounded-xl bg-white/[0.02] border border-white/5 flex items-start gap-2">
                <span class="text-coralPrimary text-sm leading-none">✓</span>
                <div class="text-xs text-gray-300 dark:text-gray-300 light:text-slate-700">${escapeHtml(tip)}</div>
              </div>
            `;
          }).join('');
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
          btnCards.className = 'view-mode-btn active px-3 py-1.5 rounded-lg font-bold transition flex items-center gap-1.5 bg-coralPrimary text-white shadow-sm';
        }
        if (btnDoc) {
          btnDoc.className = 'view-mode-btn inactive px-3 py-1.5 rounded-lg font-bold transition flex items-center gap-1.5 text-gray-400 hover:text-white';
        }
      } else {
        if (cardsView) cardsView.classList.add('hidden');
        if (toolbar) toolbar.classList.add('hidden');
        if (phaseNav) phaseNav.classList.add('hidden');
        if (tipsCard) tipsCard.classList.add('hidden');
        if (docView) docView.classList.remove('hidden');

        if (btnCards) {
          btnCards.className = 'view-mode-btn inactive px-3 py-1.5 rounded-lg font-bold transition flex items-center gap-1.5 text-gray-400 hover:text-white';
        }
        if (btnDoc) {
          btnDoc.className = 'view-mode-btn active px-3 py-1.5 rounded-lg font-bold transition flex items-center gap-1.5 bg-coralPrimary text-white shadow-sm';
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
              mapInstance.flyTo(marker.getLatLng(), 15, { animate: true, duration: 1.0, easeLinearity: 0.25 });
              setTimeout(() => marker.openPopup(), 600);
            });
          } else {
            mapInstance.flyTo(marker.getLatLng(), 15, { animate: true, duration: 1.0, easeLinearity: 0.25 });
            setTimeout(() => marker.openPopup(), 600);
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
      if (typeof window.triggerTopProgress === 'function') {
        window.triggerTopProgress(35);
      }
      showToast('Loading PDF engine on demand...', 'info', 2500);
      const s = document.createElement('script');
      s.src = 'https://cdnjs.cloudflare.com/ajax/libs/html2pdf.js/0.10.1/html2pdf.bundle.min.js';
      s.async = true;
      s.onload = () => {
        isPdfLibLoading = false;
        if (typeof window.triggerTopProgress === 'function') {
          window.triggerTopProgress(100);
        }
        callback();
      };
      s.onerror = () => {
        isPdfLibLoading = false;
        if (typeof window.triggerTopProgress === 'function') {
          window.triggerTopProgress(100);
        }
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

        if (typeof window.triggerTopProgress === 'function') {
          window.triggerTopProgress(50);
        }

        html2pdf().set(opt).from(container).save().then(() => {
          if (document.body.contains(container)) document.body.removeChild(container);
          if (typeof window.triggerTopProgress === 'function') {
            window.triggerTopProgress(100);
          }
          showToast('PDF downloaded successfully!', 'success');
        }).catch(err => {
          if (document.body.contains(container)) document.body.removeChild(container);
          if (typeof window.triggerTopProgress === 'function') {
            window.triggerTopProgress(100);
          }
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

        if (typeof window.triggerTopProgress === 'function') {
          window.triggerTopProgress(50);
        }

        html2pdf().set(opt).from(container).save().then(() => {
          if (document.body.contains(container)) document.body.removeChild(container);
          if (typeof window.triggerTopProgress === 'function') {
            window.triggerTopProgress(100);
          }
          showToast('PDF downloaded successfully!', 'success');
        }).catch(err => {
          if (document.body.contains(container)) document.body.removeChild(container);
          if (typeof window.triggerTopProgress === 'function') {
            window.triggerTopProgress(100);
          }
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

    // ========================================================
    // NELSON TRAVEL LUXURY MAGNETIC CURSOR ENGINE (DESKTOP ONLY)
    // ========================================================
    function initNelsonCursor() {
      if (window.innerWidth < 768 || (window.matchMedia && window.matchMedia('(hover: none)').matches)) return;

      const dot = document.getElementById('nelsonCursorDot');
      const ring = document.getElementById('nelsonCursorRing');
      if (!dot || !ring) return;

      let mouseX = -100, mouseY = -100;
      let ringX = -100, ringY = -100;
      let isVisible = false;
      let magneticEl = null;

      window.addEventListener('mousemove', (e) => {
        mouseX = e.clientX;
        mouseY = e.clientY;

        if (!isVisible) {
          isVisible = true;
          dot.classList.remove('cursor-hidden');
          ring.classList.remove('cursor-hidden');
          ringX = mouseX;
          ringY = mouseY;
        }
      }, { passive: true });

      document.addEventListener('mouseleave', () => {
        isVisible = false;
        dot.classList.add('cursor-hidden');
        ring.classList.add('cursor-hidden');
      });

      function renderCursor() {
        if (isVisible) {
          if (magneticEl) {
            const rect = magneticEl.getBoundingClientRect();
            const targetX = rect.left + rect.width / 2;
            const targetY = rect.top + rect.height / 2;
            ringX += (targetX - ringX) * 0.22;
            ringY += (targetY - ringY) * 0.22;
          } else {
            ringX += (mouseX - ringX) * 0.18;
            ringY += (mouseY - ringY) * 0.18;
          }

          dot.style.transform = `translate3d(${mouseX}px, ${mouseY}px, 0) translate(-50%, -50%)`;
          ring.style.transform = `translate3d(${ringX}px, ${ringY}px, 0) translate(-50%, -50%)`;
        }
        requestAnimationFrame(renderCursor);
      }
      requestAnimationFrame(renderCursor);

      const interactiveSelector = '.hotspot-card, .btn-gradient, .btn-secondary, .nav-tab, button, a, select, input, .chip-tag, #themeToggleBtn, #navStudentModeToggle';
      document.addEventListener('mouseover', (e) => {
        const target = e.target.closest(interactiveSelector);
        if (target) {
          ring.classList.add('cursor-hover');
          dot.classList.add('cursor-hover');
          if (target.matches('.btn-gradient, #themeToggleBtn, #navStudentModeToggle, .chip-tag')) {
            magneticEl = target;
          }
        }
      });

      document.addEventListener('mouseout', (e) => {
        const target = e.target.closest(interactiveSelector);
        if (target) {
          ring.classList.remove('cursor-hover');
          dot.classList.remove('cursor-hover');
          magneticEl = null;
        }
      });
    }

    // ========================================================
    // NELSON TRAVEL SCROLL-TRIGGERED STAGGERED REVEALS (GSAP PARITY)
    // ========================================================
    function initScrollRevealEngine() {
      const revealElements = document.querySelectorAll('.nelson-reveal, .nelson-line-reveal');
      if (!revealElements.length) return;

      if (!('IntersectionObserver' in window)) {
        revealElements.forEach(el => el.classList.add('is-revealed'));
        return;
      }

      const observer = new IntersectionObserver((entries, obs) => {
        entries.forEach(entry => {
          if (entry.isIntersecting) {
            const el = entry.target;
            const parent = el.parentElement;
            let delay = 0;
            if (parent && parent.classList.contains('grid')) {
              const siblings = Array.from(parent.children).filter(c => c.classList.contains('nelson-reveal'));
              const idx = siblings.indexOf(el);
              if (idx > 0) {
                delay = (idx % 4) * 85;
              }
            }

            setTimeout(() => {
              el.classList.add('is-revealed');
            }, delay);

            obs.unobserve(el);
          }
        });
      }, {
        root: null,
        rootMargin: '0px 0px -40px 0px',
        threshold: 0.10
      });

      revealElements.forEach(el => {
        if (!el.classList.contains('nelson-reveal') && !el.classList.contains('nelson-line-reveal')) {
          el.classList.add('nelson-reveal');
        }
        observer.observe(el);
      });
    }

    // ========================================================
    // NELSON TRAVEL SUBTLE MAGNETIC BUTTON MICRO-INTERACTIONS
    // ========================================================
    function initMagneticButtons() {
      if (window.innerWidth < 768 || (window.matchMedia && window.matchMedia('(hover: none)').matches)) return;

      const buttons = document.querySelectorAll('.btn-gradient, #themeToggleBtn, #navStudentModeToggle');
      buttons.forEach(btn => {
        btn.addEventListener('mousemove', (e) => {
          const rect = btn.getBoundingClientRect();
          const x = e.clientX - rect.left - rect.width / 2;
          const y = e.clientY - rect.top - rect.height / 2;
          btn.style.transform = `translate3d(${x * 0.16}px, ${y * 0.16}px, 0)`;
        });

        btn.addEventListener('mouseleave', () => {
          btn.style.transform = '';
          btn.style.transition = 'transform 0.45s cubic-bezier(0.16, 1, 0.3, 1)';
          setTimeout(() => {
            btn.style.transition = '';
          }, 450);
        });
      });
    }

    // ========================================================
    // VANILLA TILT 3D PERSPECTIVE PHYSICS (DESKTOP & LAPTOP PARITY)
    // ========================================================
    function initTiltPhysics() {
      const applyTilt = () => {
        if (typeof VanillaTilt !== 'undefined') {
          const cards = document.querySelectorAll('.hotspot-card[data-tilt], .glass-card[data-tilt]');
          VanillaTilt.init(cards, {
            max: 6,
            speed: 400,
            glare: false,
            perspective: 1000,
            scale: 1.01
          });
        }
      };

      if (typeof VanillaTilt !== 'undefined') {
        applyTilt();
      } else {
        let attempts = 0;
        const interval = setInterval(() => {
          attempts++;
          if (typeof VanillaTilt !== 'undefined') {
            clearInterval(interval);
            applyTilt();
          } else if (attempts > 30) {
            clearInterval(interval);
          }
        }, 100);
      }
    }

    // ========================================================
    // TOP GLOBAL EXPEDITION PROGRESS BAR (#progress) CONTROLLER
    // ========================================================
    window.triggerTopProgress = function(percent, duration = 350) {
      const prog = document.getElementById('progress');
      const fill = document.getElementById('topProgressFill');
      if (!prog || !fill) return;

      prog.classList.add('active');
      fill.style.width = Math.min(100, Math.max(0, percent)) + '%';

      if (percent >= 100) {
        setTimeout(() => {
          prog.classList.remove('active');
          setTimeout(() => {
            fill.style.width = '0%';
          }, 300);
        }, duration);
      }
    };

    // ========================================================
    // EVEREST CINEMATIC EXPEDITION PRELOADER (#veil) CONTROLLER
    // ========================================================
    window.dismissVeil = function(e) {
      if (e) e.stopPropagation();
      const veil = document.getElementById('veil');
      if (!veil || veil.classList.contains('gone')) return;
      veil.classList.add('gone');
      setTimeout(() => {
        veil.style.display = 'none';
      }, 1350);
    };

    function initVeilController() {
      const veil = document.getElementById('veil');
      if (!veil) return;

      const bar = document.getElementById('veilBar');
      const status = document.getElementById('veilStatus');

      // Ensure preloader is fully visible and primed on each load/refresh
      veil.classList.remove('gone');
      veil.classList.remove('ready');
      veil.style.display = 'flex';
      if (bar) bar.style.transform = 'scaleX(0)';

      // Theatrical 3.0-Second Progress Sequence (Paced to complete at 3.0s)
      setTimeout(() => {
        if (bar) bar.style.transform = 'scaleX(0.30)';
        if (status) status.innerText = '🧭 CALIBRATING 9-REGION DESTINATIONS & CLIMATE';
      }, 600);

      setTimeout(() => {
        if (bar) bar.style.transform = 'scaleX(0.60)';
        if (status) status.innerText = '📍 MAPPING STUDENT BUDGET HOTSPOTS & GPS PINS';
      }, 1300);

      setTimeout(() => {
        if (bar) bar.style.transform = 'scaleX(0.85)';
        if (status) status.innerText = '🗺️ COMPOSING CURATED ITINERARY BLUEPRINT · GROQ AI';
      }, 2050);

      setTimeout(() => {
        if (bar) bar.style.transform = 'scaleX(1)';
        if (status) status.innerText = '✨ EXPEDITION READY · EMBARK ON YOUR JOURNEY';
      }, 2700);

      // Reaches Ready State exactly at 3.0 seconds (3000ms)
      setTimeout(() => {
        veil.classList.add('ready');
      }, 3000);

      // Auto-triggers dramatic curtain-raiser after ~4.6s if user has not interacted
      let autoDismissTimer = setTimeout(() => {
        window.dismissVeil();
      }, 4600);

      // Click anywhere on veil or on button to dismiss immediately
      const onClickDismiss = (e) => {
        clearTimeout(autoDismissTimer);
        window.dismissVeil(e);
      };
      veil.addEventListener('click', onClickDismiss);

      // Dismiss on keydown (Enter, Space, Escape)
      const onKey = (e) => {
        if (e.key === 'Enter' || e.key === ' ' || e.key === 'Escape') {
          clearTimeout(autoDismissTimer);
          window.dismissVeil();
          window.removeEventListener('keydown', onKey);
        }
      };
      window.addEventListener('keydown', onKey);

      // Auto-dismiss on wheel / touch scroll after becoming ready
      const onScroll = () => {
        clearTimeout(autoDismissTimer);
        window.dismissVeil();
        window.removeEventListener('wheel', onScroll);
        window.removeEventListener('touchmove', onScroll);
      };
      window.addEventListener('wheel', onScroll, { passive: true });
      window.addEventListener('touchmove', onScroll, { passive: true });
    }

    // ========================================================
    // EVEREST EXPEDITION TELEMETRY DOCK (#expeditionHud) UPDATER
    // ========================================================
    function initHudTelemetry() {
      const hudTime = document.getElementById('hudTime');
      const hudRegion = document.getElementById('hudRegion');
      const hudMode = document.getElementById('hudMode');
      const hudCoords = document.getElementById('hudCoords');

      const updateClock = () => {
        const now = new Date();
        const hrs = String(now.getHours()).padStart(2, '0');
        const mins = String(now.getMinutes()).padStart(2, '0');
        const secs = String(now.getSeconds()).padStart(2, '0');
        if (hudTime) hudTime.innerText = `${hrs}:${mins}:${secs}`;
      };
      updateClock();
      setInterval(updateClock, 1000);

      window.updateExpeditionHud = function() {
        const reg = (typeof REGIONS !== 'undefined' && REGIONS[activeRegionKey]) ? REGIONS[activeRegionKey] : { sym: '₹' };
        if (hudRegion) {
          hudRegion.innerHTML = `${activeRegionKey} <small>${reg.sym}</small>`;
        }
        if (hudMode) {
          hudMode.innerText = (typeof siteWideStudentMode !== 'undefined' && siteWideStudentMode) ? 'Student' : 'Standard';
          hudMode.style.color = (typeof siteWideStudentMode !== 'undefined' && siteWideStudentMode) ? '#10B981' : '#EACF9F';
        }
        if (hudCoords) {
          const dest = window.activeExpeditionDestination;
          const coords = window.activeExpeditionCoords;
          if (dest) {
            const shortDest = dest.split(',')[0];
            hudCoords.innerHTML = `<span class="text-emerald-400 font-bold flex items-center gap-1" style="font-size:11px;">📍 ${shortDest} ${coords ? '<small class="opacity-80">(' + coords + ')</small>' : ''}</span>`;
            hudCoords.title = `Active Destination: ${dest}`;
          } else {
            // Short and sweet go note when nothing is on the planner tab yet
            hudCoords.innerHTML = `<span class="text-amber-400 font-bold flex items-center gap-1 cursor-pointer animate-pulse hover:text-amber-300" style="font-size:11px;">Ready to Roam ✈️</span>`;
            hudCoords.title = "Nothing planned yet — tap to pick your destination!";
          }
        }
      };
      window.updateExpeditionHud();

      // Listen for manual inputs on planner destination field
      const plannerDestEl = document.getElementById('plannerDest');
      if (plannerDestEl) {
        plannerDestEl.addEventListener('input', () => {
          const v = plannerDestEl.value.trim();
          window.activeExpeditionDestination = v || null;
          window.activeExpeditionCoords = null;
          window.updateExpeditionHud();
        });
      }
    }

    document.addEventListener('DOMContentLoaded', () => {
      // 0. Everest Cinematic Preloader & Live Expedition Telemetry
      initVeilController();
      initHudTelemetry();

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

      // 7. Nelson Travel Luxury Motion & Interaction Engines
      initNelsonCursor();
      initScrollRevealEngine();
      initMagneticButtons();

      // 8. 3D Card Physics & Interactive Tilt Parity
      initTiltPhysics();
    });
"""

def get_app_js() -> str:
    """Return the raw client JavaScript string."""
    return APP_JS
