# -*- coding: utf-8 -*-
"""
RoamAI Responsive Design & Theme Stylesheet Module.
Pure Python representation of application styles, responsive breakpoints,
and print media rules.
"""

APP_CSS = r""":root {
      --ink: #070B12;
      --pearl: #F3F6FA;
      --silver: #AEBBCD;
      --faint: #98A6BB;
      --gold: #D8B787;
      --gold-bright: #EACF9F;
      --gold-line: rgba(216, 183, 135, 0.32);
      --orange: #FF8347;
      --cyan: #8FD8EC;
      --danger: #E0565C;
      --panel: rgba(15, 22, 36, 0.82);
      --panel-line: rgba(174, 187, 205, 0.16);
      --disp: 'Playfair Display', Didot, 'Neue Protest', Georgia, serif;
      --sans: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
      --mono: ui-monospace, 'SF Mono', Menlo, Consolas, monospace;
    }

    html {
      background-color: var(--ink);
    }
    html.light-theme {
      background-color: #EEF4FB !important;
      --ink: #F4F7FB;
      --pearl: #0B132B;
      --silver: #475569;
      --faint: #64748B;
      --gold: #B48448;
      --gold-bright: #C89758;
      --gold-line: rgba(180, 132, 72, 0.35);
      --orange: #EA580C;
      --panel: rgba(255, 255, 255, 0.95);
      --panel-line: rgba(226, 232, 240, 0.8);
    }
    body {
      background-color: var(--ink);
      color: var(--pearl);
      font-family: var(--sans);
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
       CLASSIC MINIMALIST SCROLLBAR WITH DIRECTIONAL ARROWS
       (Matching user reference: 14px track, 7px pill thumb,
       discrete top/bottom triangle scroll buttons)
       ======================================================== */
    /* Firefox */
    * {
      scrollbar-width: thin;
      scrollbar-color: #475569 #080C14;
    }
    html.light-theme * {
      scrollbar-color: #C8C8C8 #F9F9F9;
    }

    /* WebKit (Chrome, Edge, Safari, Brave, Opera) */
    ::-webkit-scrollbar {
      width: 14px;
      height: 14px;
    }
    ::-webkit-scrollbar-track {
      background: #080C14;
      border-left: 1px solid rgba(255, 255, 255, 0.06);
    }
    html.light-theme ::-webkit-scrollbar-track {
      background: #F9F9F9;
      border-left: 1px solid #E6E6E6;
    }

    /* Centered Rounded Capsule Thumb */
    ::-webkit-scrollbar-thumb {
      background-color: #475569;
      border-radius: 9999px;
      border: 3.5px solid #080C14;
      background-clip: padding-box;
      transition: background-color 0.2s ease;
    }
    ::-webkit-scrollbar-thumb:hover {
      background-color: #D8B787;
    }
    ::-webkit-scrollbar-thumb:active {
      background-color: #EACF9F;
    }

    html.light-theme ::-webkit-scrollbar-thumb {
      background-color: #C8C8C8;
      border: 3.5px solid #F9F9F9;
      background-clip: padding-box;
    }
    html.light-theme ::-webkit-scrollbar-thumb:hover {
      background-color: #94A3B8;
    }
    html.light-theme ::-webkit-scrollbar-thumb:active {
      background-color: #64748B;
    }

    /* Scrollbar Directional Arrow Buttons */
    ::-webkit-scrollbar-button {
      display: block;
      height: 14px;
      width: 14px;
      background-size: 9px 6px;
      background-position: center;
      background-repeat: no-repeat;
      background-color: #080C14;
      border-left: 1px solid rgba(255, 255, 255, 0.06);
    }
    html.light-theme ::-webkit-scrollbar-button {
      background-color: #F9F9F9;
      border-left: 1px solid #E6E6E6;
    }

    /* Vertical Decrement (Top Arrow ▲) */
    ::-webkit-scrollbar-button:single-button:vertical:decrement {
      background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 10 6' fill='%2364748B'%3E%3Cpolygon points='5,0 0,6 10,6'/%3E%3C/svg%3E");
    }
    ::-webkit-scrollbar-button:single-button:vertical:decrement:hover {
      background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 10 6' fill='%23EACF9F'%3E%3Cpolygon points='5,0 0,6 10,6'/%3E%3C/svg%3E");
    }
    html.light-theme ::-webkit-scrollbar-button:single-button:vertical:decrement {
      background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 10 6' fill='%23C8C8C8'%3E%3Cpolygon points='5,0 0,6 10,6'/%3E%3C/svg%3E");
    }
    html.light-theme ::-webkit-scrollbar-button:single-button:vertical:decrement:hover {
      background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 10 6' fill='%23555555'%3E%3Cpolygon points='5,0 0,6 10,6'/%3E%3C/svg%3E");
    }

    /* Vertical Increment (Bottom Arrow ▼) */
    ::-webkit-scrollbar-button:single-button:vertical:increment {
      background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 10 6' fill='%2364748B'%3E%3Cpolygon points='0,0 10,0 5,6'/%3E%3C/svg%3E");
    }
    ::-webkit-scrollbar-button:single-button:vertical:increment:hover {
      background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 10 6' fill='%23EACF9F'%3E%3Cpolygon points='0,0 10,0 5,6'/%3E%3C/svg%3E");
    }
    html.light-theme ::-webkit-scrollbar-button:single-button:vertical:increment {
      background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 10 6' fill='%23C8C8C8'%3E%3Cpolygon points='0,0 10,0 5,6'/%3E%3C/svg%3E");
    }
    html.light-theme ::-webkit-scrollbar-button:single-button:vertical:increment:hover {
      background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 10 6' fill='%23555555'%3E%3Cpolygon points='0,0 10,0 5,6'/%3E%3C/svg%3E");
    }

    /* Horizontal Buttons (◀ and ▶) */
    ::-webkit-scrollbar-button:single-button:horizontal:decrement {
      background-size: 6px 9px;
      background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 6 10' fill='%2364748B'%3E%3Cpolygon points='6,0 6,10 0,5'/%3E%3C/svg%3E");
    }
    ::-webkit-scrollbar-button:single-button:horizontal:decrement:hover {
      background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 6 10' fill='%23EACF9F'%3E%3Cpolygon points='6,0 6,10 0,5'/%3E%3C/svg%3E");
    }
    html.light-theme ::-webkit-scrollbar-button:single-button:horizontal:decrement {
      background-size: 6px 9px;
      background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 6 10' fill='%23C8C8C8'%3E%3Cpolygon points='6,0 6,10 0,5'/%3E%3C/svg%3E");
    }
    html.light-theme ::-webkit-scrollbar-button:single-button:horizontal:decrement:hover {
      background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 6 10' fill='%23555555'%3E%3Cpolygon points='6,0 6,10 0,5'/%3E%3C/svg%3E");
    }

    ::-webkit-scrollbar-button:single-button:horizontal:increment {
      background-size: 6px 9px;
      background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 6 10' fill='%2364748B'%3E%3Cpolygon points='0,0 0,10 6,5'/%3E%3C/svg%3E");
    }
    ::-webkit-scrollbar-button:single-button:horizontal:increment:hover {
      background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 6 10' fill='%23EACF9F'%3E%3Cpolygon points='0,0 0,10 6,5'/%3E%3C/svg%3E");
    }
    html.light-theme ::-webkit-scrollbar-button:single-button:horizontal:increment {
      background-size: 6px 9px;
      background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 6 10' fill='%23C8C8C8'%3E%3Cpolygon points='0,0 0,10 6,5'/%3E%3C/svg%3E");
    }
    html.light-theme ::-webkit-scrollbar-button:single-button:horizontal:increment:hover {
      background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 6 10' fill='%23555555'%3E%3Cpolygon points='0,0 0,10 6,5'/%3E%3C/svg%3E");
    }

    ::-webkit-scrollbar-corner {
      background: #080C14;
    }
    html.light-theme ::-webkit-scrollbar-corner {
      background: #F9F9F9;
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
    .theme-icon {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      line-height: 1;
      font-size: 0px !important;
      user-select: none;
      overflow: visible;
    }
    .theme-icon::before {
      content: '🌙';
      display: inline-block;
      font-size: 15px !important;
      line-height: 1;
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
      border-color: rgba(216, 183, 135, 0.45);
      box-shadow: 0 20px 45px rgba(0, 0, 0, 0.4), 0 0 25px rgba(216, 183, 135, 0.15), inset 0 1px 0 rgba(255, 255, 255, 0.15);
      transform: translateY(-4px);
    }
    .hotspot-card:hover {
      border-color: var(--gold-bright);
      box-shadow: 0 20px 45px rgba(0, 0, 0, 0.45), 0 0 25px rgba(216, 183, 135, 0.22), inset 0 1px 0 rgba(255, 255, 255, 0.15);
      transform: translateY(-6px) translateZ(0);
    }
    .btn-gradient {
      background: linear-gradient(135deg, #D9BD85 0%, #FF8347 100%);
      color: #1A1208;
      font-weight: 700;
      transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
      box-shadow: 0 6px 25px rgba(217, 189, 133, 0.35), inset 0 1px rgba(255, 255, 255, 0.4);
    }
    .btn-gradient:hover {
      background: linear-gradient(135deg, #EACF9F 0%, #FFA066 100%);
      transform: translateY(-2px) scale(1.02);
      box-shadow: 0 10px 30px rgba(217, 189, 133, 0.55), inset 0 1px rgba(255, 255, 255, 0.6);
      color: #1A1208;
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
      background: linear-gradient(135deg, rgba(255, 255, 255, 0.92) 0%, rgba(255, 255, 255, 0.82) 100%) !important;
      backdrop-filter: blur(16px);
      -webkit-backdrop-filter: blur(16px);
      border: 1px solid #E2E8F0 !important;
      box-shadow: 0 15px 35px -10px rgba(11, 19, 43, 0.07), 0 0 0 1px rgba(226, 232, 240, 0.8) !important;
    }
    .light-theme .glass-card:hover {
      border-color: rgba(180, 132, 72, 0.5) !important;
      box-shadow: 0 20px 40px -10px rgba(180, 132, 72, 0.18), 0 0 0 1px rgba(180, 132, 72, 0.3) !important;
      transform: translateY(-4px);
    }
    .light-theme .hotspot-card {
      background: #FFFFFF !important;
      backdrop-filter: blur(16px);
      -webkit-backdrop-filter: blur(16px);
      border: 1.5px solid #E2E8F0 !important;
      box-shadow: 0 10px 25px -5px rgba(11, 19, 43, 0.05), 0 1px 3px rgba(0, 0, 0, 0.02) !important;
    }
    .light-theme .hotspot-card:hover {
      border-color: #B48448 !important;
      box-shadow: 0 20px 40px -10px rgba(180, 132, 72, 0.22), 0 0 0 1px rgba(180, 132, 72, 0.4) !important;
      transform: translateY(-6px) translateZ(0);
    }
    .light-theme .hotspot-card:hover h3 {
      color: #B48448 !important;
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
      background-color: #FFFFFF !important;
      border-color: #CBD5E1 !important;
      color: #0B132B !important;
      box-shadow: 0 1px 4px rgba(0, 0, 0, 0.08) !important;
    }
    .light-theme #themeToggleBtn:hover {
      background-color: #F8FAFC !important;
      border-color: #94A3B8 !important;
    }
    .light-theme #heroMainHeading,
    .light-theme h1,
    .light-theme h1 span:first-child {
      color: #0F172A !important;
    }
    .light-theme #heroBadgeText {
      color: #0F172A !important;
    }
    .light-theme #heroDescText {
      color: #334155 !important;
      font-weight: 500;
    }
    .light-theme #heroDestInput {
      background-color: #FFFFFF !important;
      color: #0F172A !important;
      border-color: #CBD5E1 !important;
      box-shadow: 0 2px 8px rgba(15, 23, 42, 0.06) !important;
    }
    .light-theme #heroDestInput::placeholder {
      color: #64748B !important;
    }
    .light-theme #heroDestInput:focus {
      border-color: #FF5E36 !important;
      box-shadow: 0 0 0 3px rgba(255, 94, 54, 0.2) !important;
    }
    .light-theme [class*="bg-white/5"] {
      background-color: #F8FAFC !important;
      border-color: #E2E8F0 !important;
    }
    .light-theme #navRegionSelector {
      background-color: #FFFFFF !important;
      color: #0B132B !important;
      border-color: #CBD5E1 !important;
      box-shadow: 0 1px 4px rgba(0, 0, 0, 0.06) !important;
    }
    .light-theme .nav-tab {
      color: #475569 !important;
      font-weight: 600;
    }
    .light-theme .nav-tab:hover {
      color: #FF5E36 !important;
    }
    .light-theme .nav-tab.active {
      color: #FF5E36 !important;
      font-weight: 800;
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

    /* Glass Cards & Hotspots Smooth Elevation & Glow */
    .glass-card {
      transition: transform 0.35s cubic-bezier(0.16, 1, 0.3, 1), 
                  box-shadow 0.35s cubic-bezier(0.16, 1, 0.3, 1), 
                  border-color 0.25s ease, 
                  background 0.35s ease !important;
      will-change: transform, box-shadow;
      transform: translateZ(0);
    }
    .glass-card:hover {
      transform: translateY(-4px) translateZ(0);
    }

    .hotspot-card {
      transition: transform 0.35s cubic-bezier(0.16, 1, 0.3, 1), 
                  box-shadow 0.35s cubic-bezier(0.16, 1, 0.3, 1), 
                  border-color 0.25s ease !important;
      will-change: transform, box-shadow;
      transform: translateZ(0);
    }
    .hotspot-card:hover {
      transform: translateY(-6px) translateZ(0);
    }

    .hotspot-card img {
      transition: transform 0.5s cubic-bezier(0.16, 1, 0.3, 1);
      will-change: transform;
    }
    .hotspot-card:hover img {
      transform: scale(1.05);
    }
    .hotspot-card:hover h3 {
      color: var(--gold-bright) !important;
    }
    .hotspot-card:hover span[class*="translate-x"],
    .hotspot-card:hover .group-hover\:translate-x-1 {
      transform: translateX(4px);
      color: var(--gold-bright) !important;
    }
    .chip-tag:hover,
    .hotspot-filter-btn:hover {
      border-color: var(--gold-line) !important;
      color: var(--pearl) !important;
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

  
    /* ========================================================
       THEME CONTRAST & ACCENT POLISH: STUDENT MODE & BLUEPRINT
       ======================================================== */
    /* Student Mode Form Card */
    .student-card-active {
      background: linear-gradient(135deg, rgba(255, 107, 74, 0.12), rgba(245, 158, 11, 0.08));
      border-color: rgba(255, 107, 74, 0.35);
    }
    .light-theme .student-card-active {
      background: linear-gradient(135deg, rgba(255, 107, 74, 0.08), rgba(245, 158, 11, 0.05)) !important;
      border-color: rgba(255, 107, 74, 0.3) !important;
    }

    .student-card-inactive {
      background: linear-gradient(135deg, rgba(59, 130, 246, 0.12), rgba(99, 102, 241, 0.08));
      border-color: rgba(59, 130, 246, 0.35);
    }
    .light-theme .student-card-inactive {
      background: linear-gradient(135deg, rgba(59, 130, 246, 0.08), rgba(99, 102, 241, 0.05)) !important;
      border-color: rgba(59, 130, 246, 0.3) !important;
    }

    /* Student Mode Badges */
    .student-mode-badge-on {
      background: #10B981 !important;
      color: #FFFFFF !important;
      border: 1px solid rgba(16, 185, 129, 0.5) !important;
    }
    .light-theme .student-mode-badge-on {
      background: #059669 !important;
      color: #FFFFFF !important;
    }

    .student-mode-badge-off {
      background: #334155 !important;
      color: #F1F5F9 !important;
      border: 1px solid #475569 !important;
    }
    .light-theme .student-mode-badge-off {
      background: #E2E8F0 !important;
      color: #1E293B !important;
      border: 1.5px solid #CBD5E1 !important;
    }

    /* Light Theme Toggle Track when unchecked */
    .light-theme #plannerStudentMode:not(:checked) + div {
      background-color: #CBD5E1 !important;
    }

    /* Blueprint Itinerary Mode Switcher Button */
    .itin-mode-btn-student {
      background: rgba(16, 185, 129, 0.15) !important;
      color: #34D399 !important;
      border: 1px solid rgba(16, 185, 129, 0.35) !important;
    }
    .itin-mode-btn-student:hover {
      background: rgba(16, 185, 129, 0.25) !important;
    }
    .light-theme .itin-mode-btn-student {
      background: #ECFDF5 !important;
      color: #047857 !important;
      border: 1.5px solid #6EE7B7 !important;
    }
    .light-theme .itin-mode-btn-student:hover {
      background: #D1FAE5 !important;
    }

    .itin-mode-btn-traveler {
      background: rgba(59, 130, 246, 0.15) !important;
      color: #60A5FA !important;
      border: 1px solid rgba(59, 130, 246, 0.35) !important;
    }
    .itin-mode-btn-traveler:hover {
      background: rgba(59, 130, 246, 0.25) !important;
    }
    .light-theme .itin-mode-btn-traveler {
      background: #EFF6FF !important;
      color: #1D4ED8 !important;
      border: 1.5px solid #93C5FD !important;
    }
    .light-theme .itin-mode-btn-traveler:hover {
      background: #DBEAFE !important;
    }

    /* View Mode Switcher Container (Cards / Document) */
    .light-theme #viewModeSwitcherContainer {
      background: #F1F5F9 !important;
      border: 1px solid #CBD5E1 !important;
    }
    .light-theme .view-mode-btn.inactive {
      color: #475569 !important;
    }
    .light-theme .view-mode-btn.inactive:hover {
      color: #0F172A !important;
    }

    /* Tip Boxes: Student Hack & Traveler Pro Tip (Dark Mode) */
    .tip-box-student {
      background: rgba(245, 158, 11, 0.12) !important;
      border: 1px solid rgba(245, 158, 11, 0.30) !important;
    }
    .tip-box-student .tip-title {
      color: #FBBF24 !important;
    }
    .tip-box-student .tip-content {
      color: #F8FAFC !important;
    }

    .tip-box-traveler {
      background: rgba(14, 165, 233, 0.12) !important;
      border: 1px solid rgba(14, 165, 233, 0.30) !important;
    }
    .tip-box-traveler .tip-title {
      color: #38BDF8 !important;
    }
    .tip-box-traveler .tip-content {
      color: #F8FAFC !important;
    }

    /* Tip Boxes: High-Contrast Light Theme */
    .light-theme .tip-box-student {
      background: #FFFBEB !important;
      border: 1.5px solid #FCD34D !important;
      box-shadow: 0 1px 3px rgba(245, 158, 11, 0.08) !important;
    }
    .light-theme .tip-box-student .tip-title {
      color: #B45309 !important;
    }
    .light-theme .tip-box-student .tip-content {
      color: #78350F !important;
      font-weight: 500 !important;
    }

    .light-theme .tip-box-traveler {
      background: #F0F9FF !important;
      border: 1.5px solid #BAE6FD !important;
      box-shadow: 0 1px 3px rgba(14, 165, 233, 0.08) !important;
    }
    .light-theme .tip-box-traveler .tip-title {
      color: #0284C7 !important;
    }
    .light-theme .tip-box-traveler .tip-content {
      color: #0C4A6E !important;
      font-weight: 500 !important;
    }

    /* ========================================================
       RESPONSIVE DESIGN ENHANCEMENTS FOR DIVERSE SCREEN SIZES
       ======================================================== */
    /* Root prevention of unwanted horizontal scrolling on mobile devices */
    html, body {
      max-width: 100vw;
      overflow-x: hidden;
      overflow-x: clip;
    }

    /* Ultra-small mobile phones (< 380px) */
    @media (max-width: 380px) {
      .hero-title {
        font-size: 1.75rem !important;
        line-height: 1.2 !important;
      }
      .brand-logo-title {
        font-size: 0.95rem !important;
      }
      .chip-tag {
        font-size: 0.72rem !important;
        padding: 0.35rem 0.65rem !important;
      }
      .glass-card {
        padding: 0.85rem !important;
      }
    }

    /* Mobile Phones & Phablets (< 640px) */
    @media (max-width: 640px) {
      input, select, textarea, button {
        font-size: 16px !important; /* Prevents auto-zoom on iOS Safari */
      }
      .day-card-header {
        flex-direction: column;
        align-items: flex-start !important;
        gap: 0.5rem;
      }
      .day-budget-pill {
        align-self: flex-start;
      }
      #mapViewContainer {
        height: 340px !important;
      }
      #toastContainer {
        bottom: 1rem !important;
        left: 0.75rem !important;
        right: 0.75rem !important;
        max-width: calc(100vw - 1.5rem) !important;
      }
      .modal-dialog {
        margin: 0.75rem !important;
        max-width: calc(100vw - 1.5rem) !important;
      }
    }

    /* Tablets & Small Laptops (641px to 1024px) */
    @media (min-width: 641px) and (max-width: 1024px) {
      #mapViewContainer {
        height: 440px !important;
      }
      .itinerary-grid {
        grid-template-columns: repeat(2, 1fr) !important;
      }
    }

    /* Ultra-Wide Monitors (> 1536px) */
    @media (min-width: 1536px) {
      .max-screen-container {
        max-width: 1440px !important;
        margin-left: auto !important;
        margin-right: auto !important;
      }
    }
    /* ========================================================
       NELSON TRAVEL LUXURY ANIMATION & MAGNETIC EFFECT ENGINE
       ======================================================== */
    /* 1. Custom Magnetic Cursor (Desktop Only) */
    #nelsonCursorDot {
      width: 7px;
      height: 7px;
      background-color: #FF5E36;
      border-radius: 50%;
      position: fixed;
      top: 0;
      left: 0;
      pointer-events: none;
      z-index: 99999;
      transform: translate(-50%, -50%);
      transition: width 0.2s ease, height 0.2s ease, background-color 0.2s ease, opacity 0.25s ease;
      will-change: transform;
    }
    #nelsonCursorRing {
      width: 36px;
      height: 36px;
      border: 1.5px solid rgba(255, 94, 54, 0.45);
      border-radius: 50%;
      position: fixed;
      top: 0;
      left: 0;
      pointer-events: none;
      z-index: 99998;
      transform: translate(-50%, -50%);
      transition: width 0.3s cubic-bezier(0.16, 1, 0.3, 1), 
                  height 0.3s cubic-bezier(0.16, 1, 0.3, 1), 
                  border-color 0.25s ease, 
                  background-color 0.25s ease,
                  opacity 0.25s ease;
      will-change: transform;
      background-color: transparent;
      backdrop-filter: blur(1px);
    }
    /* Cursor hover state over interactive elements (cards, buttons, nav items) */
    #nelsonCursorRing.cursor-hover {
      width: 64px;
      height: 64px;
      border-color: rgba(255, 94, 54, 0.75);
      background-color: rgba(255, 94, 54, 0.08);
      box-shadow: 0 0 24px rgba(255, 94, 54, 0.25);
    }
    #nelsonCursorDot.cursor-hover {
      transform: translate(-50%, -50%) scale(1.6);
      background-color: #FFA000;
    }
    #nelsonCursorRing.cursor-hidden,
    #nelsonCursorDot.cursor-hidden {
      opacity: 0;
    }
    /* Light theme cursor adjustments */
    .light-theme #nelsonCursorDot {
      background-color: #EA580C;
    }
    .light-theme #nelsonCursorRing {
      border-color: rgba(234, 88, 12, 0.45);
    }
    .light-theme #nelsonCursorRing.cursor-hover {
      border-color: rgba(234, 88, 12, 0.85);
      background-color: rgba(234, 88, 12, 0.08);
    }
    /* Disable custom cursor completely on touch devices & mobile */
    @media (hover: none), (pointer: coarse), (max-width: 768px) {
      #nelsonCursorDot, #nelsonCursorRing {
        display: none !important;
      }
    }

    /* 2. Scroll-Triggered Staggered Reveals (GSAP/ScrollTrigger Parity) */
    .nelson-reveal {
      opacity: 0;
      transform: translateY(35px);
      transition: opacity 0.85s cubic-bezier(0.16, 1, 0.3, 1), transform 0.85s cubic-bezier(0.16, 1, 0.3, 1);
      will-change: opacity, transform;
    }
    .nelson-reveal.is-revealed {
      opacity: 1 !important;
      transform: none;
    }
    .nelson-reveal-left {
      opacity: 0;
      transform: translateX(-35px);
      transition: opacity 0.85s cubic-bezier(0.16, 1, 0.3, 1), transform 0.85s cubic-bezier(0.16, 1, 0.3, 1);
      will-change: opacity, transform;
    }
    .nelson-reveal-left.is-revealed {
      opacity: 1 !important;
      transform: none;
    }
    .nelson-reveal-scale {
      opacity: 0;
      transform: scale(0.94);
      transition: opacity 0.85s cubic-bezier(0.16, 1, 0.3, 1), transform 0.85s cubic-bezier(0.16, 1, 0.3, 1) !important;
      will-change: opacity, transform;
    }
    .nelson-reveal-scale.is-revealed {
      opacity: 1 !important;
      transform: scale(1) !important;
    }

    /* 3. Subtle Animated Accent Line / Divider Flourishes */
    .nelson-line-reveal {
      position: relative;
    }
    .nelson-line-reveal::after {
      content: '';
      position: absolute;
      bottom: -6px;
      left: 0;
      width: 0%;
      height: 2px;
      background: linear-gradient(90deg, #FF5E36, #FFA000, transparent);
      transition: width 1.1s cubic-bezier(0.16, 1, 0.3, 1);
      border-radius: 2px;
    }
    .nelson-line-reveal.is-revealed::after {
      width: 100%;
    }

    /* 4. Luxury Card Image Overflow Zoom & Masking */
    .hotspot-card .relative {
      overflow: hidden;
      border-radius: 1rem;
    }
    .hotspot-card img {
      transition: transform 0.65s cubic-bezier(0.16, 1, 0.3, 1), filter 0.65s ease !important;
      will-change: transform;
    }
    .hotspot-card:hover img {
      transform: scale(1.08) !important;
    }

    /* ========================================================
       TOP GLOBAL EXPEDITION PROGRESS BAR (#progress)
       Visible & Vibrant across both Dark & Light Themes
       ======================================================== */
    #progress {
      position: fixed;
      top: 0;
      left: 0;
      width: 100%;
      height: 3px;
      z-index: 99999;
      pointer-events: none;
      background: rgba(255, 255, 255, 0.05);
      opacity: 0;
      transition: opacity 0.3s ease;
    }
    #progress.active {
      opacity: 1;
    }
    #progress i {
      display: block;
      height: 100%;
      width: 0%;
      background: linear-gradient(90deg, #D8B787, #FF8347, #EACF9F);
      box-shadow: 0 0 10px rgba(216, 183, 135, 0.75);
      transition: width 0.35s cubic-bezier(0.16, 1, 0.3, 1);
      position: relative;
      overflow: visible;
      border-radius: 0 4px 4px 0;
    }
    #progress i::before {
      content: "";
      position: absolute;
      right: -2px;
      top: 50%;
      transform: translateY(-50%);
      width: 7px;
      height: 7px;
      border-radius: 50%;
      background: #FFFFFF;
      box-shadow: 0 0 8px #FFA000, 0 0 14px #FF5E36;
    }
    #progress i::after {
      content: "";
      position: absolute;
      top: 0; bottom: 0; width: 70px;
      background: linear-gradient(90deg, transparent, #FFFBF0, transparent);
      animation: barSheen 1.5s linear infinite;
    }

    /* Light Theme Top Progress Bar (Ultra-Visible, Bold, High-Contrast Neon-Coral) */
    html.light-theme #progress {
      height: 4px;
      background: rgba(0, 0, 0, 0.08);
      box-shadow: 0 1px 4px rgba(0, 0, 0, 0.08);
    }
    html.light-theme #progress i {
      background: linear-gradient(90deg, #EA580C 0%, #FF5E36 45%, #FFA000 80%, #FF3366 100%) !important;
      box-shadow: 0 2px 10px rgba(234, 88, 12, 0.85), 0 0 16px rgba(255, 94, 54, 0.8) !important;
    }
    html.light-theme #progress i::before {
      background: #FFFFFF;
      box-shadow: 0 0 6px #FFFFFF, 0 0 12px #EA580C, 0 0 18px #FF3366;
      width: 8px;
      height: 8px;
    }
    html.light-theme #progress i::after {
      background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.95), transparent);
    }

    /* ========================================================
       THEATRICAL DRAMA CURTAIN-RAISER PRELOADER (#veil)
       ======================================================== */
    #veil {
      position: fixed;
      inset: 0;
      z-index: 10000;
      background: transparent;
      display: flex;
      align-items: center;
      justify-content: center;
      flex-direction: column;
      color: #AEBBCD;
      cursor: default;
      user-select: none;
      -webkit-user-select: none;
      overflow: hidden;
      perspective: 1000px;
    }

    /* Theatrical Drama Curtain Panels */
    #veil .veil-curtain {
      position: absolute;
      top: 0;
      bottom: 0;
      width: 50.5%;
      z-index: 1;
      will-change: transform;
      transition: transform 1.25s cubic-bezier(0.76, 0, 0.24, 1);
      box-shadow: 0 0 60px rgba(0, 0, 0, 0.5);
    }
    #veil .veil-curtain-left {
      left: 0;
      transform: translateX(0);
      background: radial-gradient(ellipse at 85% 45%, #0F172A 0%, #090E17 60%, #04060A 100%);
      border-right: 1px solid rgba(216, 183, 135, 0.25);
    }
    #veil .veil-curtain-right {
      right: 0;
      transform: translateX(0);
      background: radial-gradient(ellipse at 15% 45%, #0F172A 0%, #090E17 60%, #04060A 100%);
      border-left: 1px solid rgba(216, 183, 135, 0.25);
    }

    /* Light Theme Theatrical Curtain Panels (Warm Italian Parchment) */
    html.light-theme #veil .veil-curtain-left {
      background:
        radial-gradient(ellipse at 85% 42%, rgba(255, 255, 255, 0.75) 0%, rgba(248, 242, 233, 0.6) 45%, rgba(235, 222, 206, 0.9) 100%),
        radial-gradient(circle at 18% 18%, rgba(216, 183, 135, 0.25) 0%, transparent 45%),
        repeating-linear-gradient(0deg, transparent, transparent 47px, rgba(180, 132, 72, 0.05) 48px),
        repeating-linear-gradient(90deg, transparent, transparent 47px, rgba(180, 132, 72, 0.05) 48px),
        linear-gradient(155deg, #FAF4EB 0%, #F4EAD8 30%, #EADBCA 65%, #DFCDAE 100%);
      border-right: 1.5px solid rgba(180, 132, 72, 0.45);
      box-shadow: 12px 0 35px rgba(120, 80, 30, 0.12);
    }
    html.light-theme #veil .veil-curtain-right {
      background:
        radial-gradient(ellipse at 15% 42%, rgba(255, 255, 255, 0.75) 0%, rgba(248, 242, 233, 0.6) 45%, rgba(235, 222, 206, 0.9) 100%),
        radial-gradient(circle at 82% 82%, rgba(255, 131, 71, 0.15) 0%, transparent 45%),
        repeating-linear-gradient(0deg, transparent, transparent 47px, rgba(180, 132, 72, 0.05) 48px),
        repeating-linear-gradient(90deg, transparent, transparent 47px, rgba(180, 132, 72, 0.05) 48px),
        linear-gradient(155deg, #FAF4EB 0%, #F4EAD8 30%, #EADBCA 65%, #DFCDAE 100%);
      border-left: 1.5px solid rgba(180, 132, 72, 0.45);
      box-shadow: -12px 0 35px rgba(120, 80, 30, 0.12);
    }

    /* Dramatic Theatrical Curtain Fringe Seam */
    #veil .curtain-fringe {
      position: absolute;
      top: 0;
      bottom: 0;
      width: 4px;
      background: linear-gradient(180deg, transparent, rgba(216, 183, 135, 0.5), transparent);
    }
    #veil .veil-curtain-left .curtain-fringe { right: -2px; }
    #veil .veil-curtain-right .curtain-fringe { left: -2px; }
    html.light-theme #veil .curtain-fringe {
      background: linear-gradient(180deg, transparent, rgba(180, 132, 72, 0.7), transparent);
    }

    /* THE DRAMATIC CURTAIN-RAISER ACTION */
    #veil.gone .veil-curtain-left {
      transform: translateX(-102%) !important;
    }
    #veil.gone .veil-curtain-right {
      transform: translateX(102%) !important;
    }
    #veil.gone .veil-card {
      transform: scale(1.08);
      opacity: 0 !important;
      transition: transform 0.65s cubic-bezier(0.16, 1, 0.3, 1), opacity 0.5s ease;
    }
    #veil.gone .veil-decor,
    #veil.gone .veil-rings,
    #veil.gone .veil-glow {
      opacity: 0 !important;
      transition: opacity 0.45s ease;
    }
    #veil.gone {
      pointer-events: none !important;
    }

    /* Four-Corner Vintage Expedition Telemetry Decor */
    #veil .veil-decor {
      position: absolute;
      font-family: var(--mono);
      font-size: 10px;
      font-weight: 600;
      letter-spacing: 0.24em;
      color: rgba(174, 187, 205, 0.55);
      pointer-events: none;
      z-index: 2;
      user-select: none;
      text-transform: uppercase;
    }
    html.light-theme #veil .veil-decor {
      color: rgba(130, 92, 44, 0.65);
    }
    #veil .veil-decor-tl { top: 28px; left: 32px; }
    #veil .veil-decor-tr { top: 28px; right: 32px; }
    #veil .veil-decor-bl { bottom: 28px; left: 32px; }
    #veil .veil-decor-br { bottom: 28px; right: 32px; }
    @media (max-width: 768px) {
      #veil .veil-decor { display: none; }
    }

    /* Atmospheric Ambient Glow */
    #veil .veil-glow {
      position: absolute;
      width: min(520px, 90vw);
      height: min(520px, 90vw);
      border-radius: 50%;
      background: radial-gradient(circle, rgba(216, 183, 135, 0.16) 0%, rgba(255, 131, 71, 0.08) 40%, transparent 70%);
      top: 50%;
      left: 50%;
      transform: translate(-50%, -50%);
      animation: veilGlowPulse 4s ease-in-out infinite;
      pointer-events: none;
      z-index: 1;
    }
    html.light-theme #veil .veil-glow {
      background: radial-gradient(circle, rgba(216, 183, 135, 0.26) 0%, rgba(180, 132, 72, 0.14) 45%, transparent 70%);
    }

    /* Celestial Astrolabe Orbital Rings */
    #veil .veil-rings {
      position: absolute;
      width: min(640px, 92vw);
      height: min(640px, 92vw);
      top: 50%;
      left: 50%;
      transform: translate(-50%, -50%);
      border-radius: 50%;
      border: 1px solid rgba(216, 183, 135, 0.16);
      pointer-events: none;
      animation: veilOrbitSpin 36s linear infinite;
      z-index: 1;
    }
    #veil .veil-rings::before {
      content: '';
      position: absolute;
      inset: 44px;
      border-radius: 50%;
      border: 1px dashed rgba(216, 183, 135, 0.12);
      animation: veilOrbitSpin 22s linear infinite reverse;
    }
    #veil .veil-rings::after {
      content: '';
      position: absolute;
      inset: 88px;
      border-radius: 50%;
      border: 1px solid rgba(216, 183, 135, 0.08);
    }
    html.light-theme #veil .veil-rings {
      border-color: rgba(180, 132, 72, 0.28);
      box-shadow: 0 0 80px rgba(180, 132, 72, 0.08);
    }
    html.light-theme #veil .veil-rings::before {
      border-color: rgba(180, 132, 72, 0.22);
    }
    html.light-theme #veil .veil-rings::after {
      border-color: rgba(180, 132, 72, 0.16);
    }

    /* Architectural Frosted Glass Central Card */
    #veil .veil-card {
      position: relative;
      z-index: 3;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      padding: clamp(34px, 5vw, 50px) clamp(30px, 6vw, 64px);
      border-radius: 28px;
      background: rgba(13, 20, 34, 0.72);
      border: 1px solid rgba(216, 183, 135, 0.25);
      box-shadow: 0 25px 70px rgba(0, 0, 0, 0.65), inset 0 1px 0 rgba(255, 255, 255, 0.15);
      backdrop-filter: blur(24px);
      -webkit-backdrop-filter: blur(24px);
      text-align: center;
      max-width: min(480px, 90vw);
    }
    html.light-theme #veil .veil-card {
      background: rgba(255, 253, 248, 0.92);
      border: 1.5px solid rgba(180, 132, 72, 0.38);
      box-shadow: 0 28px 75px rgba(130, 90, 36, 0.16), 0 6px 20px rgba(0, 0, 0, 0.04), inset 0 1px 2px rgba(255, 255, 255, 0.95);
    }

    /* Signature RoamAI Travel Flight Emblem inside Veil */
    #veil .veil-emblem {
      display: flex;
      align-items: center;
      justify-content: center;
      margin-bottom: 14px;
    }
    #veil .veil-emblem-box {
      width: 52px;
      height: 52px;
      border-radius: 18px;
      background: linear-gradient(135deg, #FF5E36 0%, #FFA000 100%);
      padding: 2.5px;
      box-shadow: 0 12px 28px rgba(255, 94, 54, 0.35);
      display: flex;
      align-items: center;
      justify-content: center;
      animation: veilPlaneFloat 3.2s ease-in-out infinite;
    }
    #veil .veil-emblem-inner {
      width: 100%;
      height: 100%;
      background: #0B0F19;
      border-radius: 15.5px;
      display: flex;
      align-items: center;
      justify-content: center;
    }
    html.light-theme #veil .veil-emblem-inner {
      background: #FFFFFF;
      box-shadow: inset 0 1px 2px rgba(0, 0, 0, 0.06);
    }
    #veil .veil-plane {
      display: inline-block;
      font-size: 24px;
      transform: rotate(-45deg);
      filter: drop-shadow(0 2px 6px rgba(0, 0, 0, 0.25));
    }

    #veil .mark {
      font-family: var(--mono);
      font-size: 9.5px;
      font-weight: 700;
      letter-spacing: 0.26em;
      text-indent: 0.26em;
      color: #EACF9F;
      margin-bottom: 6px;
      text-transform: uppercase;
    }
    html.light-theme #veil .mark {
      color: #A87028;
    }
    #veil .t {
      font-family: var(--disp);
      font-weight: 600;
      font-size: clamp(38px, 6.5vw, 68px);
      line-height: 1;
      color: #F3F6FA;
      letter-spacing: 0.06em;
      text-align: center;
    }
    html.light-theme #veil .t {
      color: #0B132B;
    }
    #veil .st {
      font-family: var(--disp);
      font-style: italic;
      font-weight: 500;
      font-size: clamp(17px, 2.8vw, 24px);
      color: #EACF9F;
      margin: 6px 0 24px;
      letter-spacing: 0.16em;
      text-align: center;
    }
    html.light-theme #veil .st {
      color: #8C6028;
    }
    #veil .bar {
      width: clamp(200px, 36vw, 270px);
      height: 2px;
      background: rgba(174, 187, 205, 0.18);
      overflow: hidden;
      margin-bottom: 16px;
      border-radius: 2px;
      position: relative;
    }
    html.light-theme #veil .bar {
      background: rgba(148, 163, 184, 0.32);
    }
    #veil .bar i {
      display: block;
      position: relative;
      overflow: hidden;
      height: 100%;
      width: 100%;
      background: linear-gradient(90deg, var(--gold), var(--orange));
      transform: scaleX(0);
      transform-origin: 0 50%;
      transition: transform 0.6s cubic-bezier(0.16, 1, 0.3, 1);
    }
    html.light-theme #veil .bar i {
      background: linear-gradient(90deg, #A87635, #EA580C);
    }
    #veil .bar i::after {
      content: "";
      position: absolute;
      top: 0; bottom: 0; width: 70px;
      background: linear-gradient(90deg, transparent, #FFFBF0, transparent);
      animation: barSheen 2.2s linear infinite;
    }
    html.light-theme #veil .bar i::after {
      background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.95), transparent);
    }
    #veil .s {
      font-family: var(--mono);
      font-size: 9.5px;
      letter-spacing: 0.26em;
      text-indent: 0.26em;
      color: rgba(174, 187, 205, 0.75);
      transition: opacity 0.5s ease;
      text-align: center;
      max-width: 90vw;
    }
    html.light-theme #veil .s {
      color: #475569;
      font-weight: 600;
    }
    #veil .go {
      display: inline-flex;
      align-items: center;
      gap: 12px;
      font-family: var(--sans);
      font-weight: 700;
      font-size: 11px;
      letter-spacing: 0.22em;
      text-indent: 0.22em;
      color: #1E160A;
      background: linear-gradient(135deg, #D9BD85 0%, #EACF9F 100%);
      border: none;
      border-radius: 9999px;
      padding: 14px 32px;
      margin-top: 22px;
      cursor: pointer;
      box-shadow: inset 0 1px rgba(255, 248, 230, 0.7), 0 12px 30px rgba(216, 183, 135, 0.25);
      opacity: 0;
      transform: translateY(12px);
      pointer-events: none;
      transition: opacity 0.6s ease, transform 0.6s cubic-bezier(0.16, 1, 0.3, 1), background 0.3s ease, box-shadow 0.3s ease;
    }
    #veil .go:hover {
      background: linear-gradient(135deg, #E6CC99 0%, #F5DEB3 100%);
      transform: translateY(10px) scale(1.02);
      box-shadow: inset 0 1px rgba(255, 248, 230, 0.8), 0 16px 36px rgba(216, 183, 135, 0.4);
    }
    html.light-theme #veil .go {
      color: #FFFFFF;
      background: linear-gradient(135deg, #182030 0%, #0B132B 100%);
      border: 1px solid rgba(180, 132, 72, 0.5);
      box-shadow: 0 12px 30px rgba(11, 19, 43, 0.28), inset 0 1px 0 rgba(255, 255, 255, 0.2);
    }
    html.light-theme #veil .go:hover {
      background: linear-gradient(135deg, #242E45 0%, #121C38 100%);
      transform: translateY(10px) scale(1.02);
      box-shadow: 0 16px 36px rgba(11, 19, 43, 0.36), inset 0 1px 0 rgba(255, 255, 255, 0.3);
    }
    #veil .go .pi {
      font-size: 14px;
      line-height: 1;
      display: inline-block;
      transform: rotate(-35deg);
    }
    #veil.ready .s {
      opacity: 0;
      height: 0;
      margin: 0;
      overflow: hidden;
    }
    #veil.ready .go {
      opacity: 1;
      transform: translateY(0);
      pointer-events: auto;
    }
    #veil .sndh {
      margin-top: 16px;
      font-family: var(--mono);
      font-size: 9px;
      letter-spacing: 0.22em;
      color: rgba(174, 187, 205, 0.55);
      opacity: 0;
      transition: opacity 0.8s ease 0.2s;
      text-align: center;
    }
    html.light-theme #veil .sndh {
      color: rgba(90, 68, 38, 0.65);
    }
    #veil.ready .sndh {
      opacity: 0.85;
    }

    /* ========================================================
       EVEREST EXPEDITION TELEMETRY DOCK (#expeditionHud)
       ======================================================== */
    #expeditionHud {
      position: fixed;
      right: 18px;
      bottom: 18px;
      z-index: 45;
      display: flex;
      align-items: center;
      border-radius: 16px;
      overflow: hidden;
      background: linear-gradient(160deg, rgba(13, 20, 32, 0.88), rgba(7, 11, 19, 0.82));
      border: 1px solid rgba(243, 246, 250, 0.12);
      backdrop-filter: blur(16px);
      -webkit-backdrop-filter: blur(16px);
      box-shadow: 0 15px 35px rgba(0, 0, 0, 0.5), inset 0 1px 0 rgba(255, 255, 255, 0.1);
      transition: opacity 0.4s ease, transform 0.4s cubic-bezier(0.16, 1, 0.3, 1);
    }
    #expeditionHud .cell {
      padding: 10px 16px;
      border-right: 1px solid rgba(243, 246, 250, 0.08);
      display: flex;
      flex-direction: column;
      justify-content: center;
    }
    #expeditionHud .cell:last-child {
      border-right: none;
    }
    #expeditionHud .k {
      font-family: var(--mono);
      font-size: 8.5px;
      font-weight: 600;
      letter-spacing: 0.18em;
      color: var(--faint);
      margin-bottom: 2px;
      white-space: nowrap;
    }
    #expeditionHud .v {
      font-family: var(--sans);
      font-size: 12px;
      font-weight: 700;
      color: var(--pearl);
      white-space: nowrap;
      display: flex;
      align-items: center;
      gap: 5px;
    }
    #expeditionHud .v small {
      font-size: 10px;
      color: var(--gold);
    }
    .light-theme #expeditionHud {
      background: rgba(255, 255, 255, 0.94);
      border: 1px solid #E2E8F0;
      box-shadow: 0 10px 30px rgba(11, 19, 43, 0.08), inset 0 1px 0 rgba(255, 255, 255, 1);
    }
    .light-theme #expeditionHud .cell {
      border-right-color: #E2E8F0;
    }
    .light-theme #expeditionHud .k {
      color: #64748B;
    }
    .light-theme #expeditionHud .v {
      color: #0F172A;
    }
    @media (max-width: 768px) {
      #expeditionHud {
        bottom: 74px;
        right: 12px;
        left: 12px;
        justify-content: space-around;
        border-radius: 14px;
        padding: 3px 6px;
        box-shadow: 0 10px 25px rgba(0, 0, 0, 0.45);
      }
      #expeditionHud .cell {
        padding: 6px 8px;
        flex: 1;
        text-align: center;
        align-items: center;
      }
      #expeditionHud .cell.hide-mob {
        display: none !important;
      }
      #expeditionHud .k {
        font-size: 7.5px;
        letter-spacing: 0.12em;
      }
      #expeditionHud .v {
        font-size: 11px;
      }
    }

    /* ========================================================
       EVEREST EDITORIAL & KEYFRAME SUITE
       ======================================================== */
    .font-serif {
      font-family: var(--disp) !important;
    }
    .eyebrow-tracked {
      font-family: var(--mono);
      font-size: 10px;
      font-weight: 700;
      letter-spacing: 0.24em;
      text-transform: uppercase;
      color: var(--gold);
    }
    .star-mark {
      color: var(--gold);
      display: inline-block;
      margin-right: 4px;
    }

    @keyframes pulseStar {
      0%, 100% { opacity: 0.7; transform: scale(1); filter: drop-shadow(0 0 2px rgba(216, 183, 135, 0.4)); }
      50% { opacity: 1; transform: scale(1.22); filter: drop-shadow(0 0 8px rgba(216, 183, 135, 0.8)); }
    }
    @keyframes barSheen {
      0% { transform: translateX(-80px); }
      100% { transform: translateX(340px); }
    }
    @keyframes riseBlur {
      0% { opacity: 0; transform: translateY(16px); filter: blur(5px); }
      100% { opacity: 1; transform: translateY(0); filter: blur(0); }
    }
    @keyframes trackIn {
      0% { opacity: 0; letter-spacing: 0.45em; }
      100% { opacity: 1; letter-spacing: 0.24em; }
    }
    @keyframes veilOrbitSpin {
      0% { transform: translate(-50%, -50%) rotate(0deg); }
      100% { transform: translate(-50%, -50%) rotate(360deg); }
    }
    @keyframes veilGlowPulse {
      0%, 100% { opacity: 0.5; transform: translate(-50%, -50%) scale(1); }
      50% { opacity: 1; transform: translate(-50%, -50%) scale(1.15); }
    }
    @keyframes veilPlaneFloat {
      0%, 100% { transform: translateY(0) rotate(0deg); }
      50% { transform: translateY(-5px) rotate(4deg); }
    }
    @media print {
      /* Hide dynamic navigation, canvas, floating buttons, toasts & modals */
      #mainHeader,
      #bgParticleCanvas,
      #toastContainer,
      #confirmModal,
      .action-dock,
      .floating-controls,
      .no-print,
      footer {
        display: none !important;
      }

      /* Clean page formatting */
      @page {
        size: A4 portrait;
        margin: 12mm 10mm 12mm 10mm;
      }

      body {
        background: #ffffff !important;
        color: #0f172a !important;
        font-size: 11pt !important;
        line-height: 1.5 !important;
      }

      /* High contrast card borders and zero shadow for clean vector prints */
      .glass-card, .itinerary-day-card, .blueprint-card {
        background: #ffffff !important;
        border: 1px solid #cbd5e1 !important;
        box-shadow: none !important;
        backdrop-filter: none !important;
        -webkit-backdrop-filter: none !important;
        break-inside: avoid !important;
        page-break-inside: avoid !important;
        margin-bottom: 1rem !important;
      }

      /* Day cards clean break avoidance */
      .day-card {
        break-inside: avoid !important;
        page-break-inside: avoid !important;
      }

      /* Force show student hack / traveler advice with clean borders */
      .tip-box-student {
        background: #fffbeb !important;
        border: 1px solid #f59e0b !important;
        color: #92400e !important;
      }
      .tip-box-traveler {
        background: #f0f9ff !important;
        border: 1px solid #0284c7 !important;
        color: #075985 !important;
      }
    }
"""

def get_app_css() -> str:
    """Return the raw CSS stylesheet string."""
    return APP_CSS
