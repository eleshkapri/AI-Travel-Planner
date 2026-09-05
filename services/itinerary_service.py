# -*- coding: utf-8 -*-
"""
RoamAI Itinerary Service.
Encapsulates Object-Oriented AI Itinerary Planning, Multi-Model Failover Cascading,
and Collision-Free Landmark Pin Coordinate Dispersal.
"""
from __future__ import annotations
import os
import re
import math
import abc
import threading
from typing import List, Optional, Dict, Any, Tuple
from pydantic import BaseModel, Field
from groq import Groq

from core.config import settings
from core.security import InputSanitizer
from services.knowledge_base import geo_service, GeoLocationService


class TripRequest(BaseModel):
    """Encapsulated validation model for trip planning requests."""
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


class LandmarkCoordinatePlacer:
    """
    Mathematical spatial placement engine for map pins.
    Prevents map marker collisions and distributes unlocated landmarks in a natural spiral radius.
    """
    COLLISION_THRESHOLD: float = 0.0035

    @classmethod
    def is_too_close(cls, c1: List[float], c2: List[float], threshold: float = COLLISION_THRESHOLD) -> bool:
        """Determines if two coordinate pairs are within collision distance."""
        return abs(c1[0] - c2[0]) < threshold and abs(c1[1] - c2[1]) < threshold

    def place_markers(
        self,
        destination_clean: str,
        dest_coords: Optional[List[float]],
        must_visit_clean: Optional[str],
        raw_landmarks: List[str],
        geo: GeoLocationService
    ) -> List[Dict[str, Any]]:
        """Resolve and spatially distribute map markers with collision mitigation."""
        markers: List[Dict[str, Any]] = []

        if dest_coords:
            markers.append({
                "name": f"Destination: {destination_clean}",
                "type": "destination",
                "coords": dest_coords
            })

        mv_coords = None
        if must_visit_clean:
            mv_coords = geo.resolve_coordinates(must_visit_clean, destination_clean)
            if mv_coords:
                markers.append({
                    "name": f"Must Visit: {must_visit_clean}",
                    "type": "must_visit",
                    "coords": mv_coords
                })

        placed_coords: List[List[float]] = []
        if dest_coords:
            placed_coords.append(dest_coords)
        if mv_coords:
            placed_coords.append(mv_coords)

        for idx, landmark in enumerate(raw_landmarks):
            l_coords = geo.resolve_coordinates(landmark, destination_clean)
            need_spread = False

            if not l_coords:
                need_spread = True
            elif dest_coords and self.is_too_close(l_coords, dest_coords, threshold=0.002):
                need_spread = True

            if need_spread and dest_coords:
                angle = idx * 2.39996323
                radius = 0.015 + (idx * 0.007)
                cos_lat = max(0.2, math.cos(math.radians(dest_coords[0])))
                lat_offset = radius * math.cos(angle)
                lng_offset = (radius * math.sin(angle)) / cos_lat
                l_coords = [round(dest_coords[0] + lat_offset, 5), round(dest_coords[1] + lng_offset, 5)]

            if l_coords:
                collision_count = 0
                while any(self.is_too_close(l_coords, p) for p in placed_coords) and collision_count < 16:
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

        return markers


class BasePlannerService(abc.ABC):
    """Abstract Base Class establishing contract for Travel Planner engines."""

    @abc.abstractmethod
    def generate_itinerary(self, req: TripRequest) -> Dict[str, Any]:
        """Generate a complete itinerary dictionary from a validated TripRequest."""
        pass


class TravelPlannerService(BasePlannerService):
    """
    Concrete Travel Planner orchestrating Groq LLM API requests,
    multi-model fallback chains, and spatial coordinate mapping.
    """
    _instance: Optional[TravelPlannerService] = None
    _lock: threading.Lock = threading.Lock()

    def __new__(cls) -> TravelPlannerService:
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(TravelPlannerService, cls).__new__(cls)
                cls._instance._initialize()
            return cls._instance

    @classmethod
    def get_instance(cls) -> TravelPlannerService:
        if cls._instance is None:
            return cls()
        return cls._instance

    def _initialize(self) -> None:
        self._geo: GeoLocationService = geo_service
        self._placer: LandmarkCoordinatePlacer = LandmarkCoordinatePlacer()

    def _calculate_target_landmarks(self, days: int) -> int:
        """Dynamically scale landmark quota based on trip duration."""
        if days <= 7:
            return max(days + 1, 5)
        elif days <= 15:
            return min(days + 2, 16)
        elif days <= 30:
            return min(days + 2, 30)
        elif days <= 60:
            return min(int(days * 0.8) + 2, 48)
        else:
            return min(int(days * 0.75) + 3, 65)

    def _build_llm_prompt(
        self,
        req: TripRequest,
        dest_clean: str,
        must_visit_clean: str,
        budget_text: str,
        curr: str,
        region_info: str,
        interests_str: str,
        pace_text: str,
        accom_clean: str,
        is_student: bool,
        target_lm_count: int
    ) -> str:
        """Constructs an expert persona prompt for Groq LLMs."""
        must_visit_instruction = ""
        if must_visit_clean:
            must_visit_instruction = f"CRITICAL: You MUST feature a dedicated visit to '{must_visit_clean}' in the itinerary."

        if is_student:
            persona_text = "You are an award-winning local travel architect specializing in epic, student-friendly, budget adventures."
            budget_hdr = f"## 💰 Estimated Student Budget Breakdown ({curr})"
            savings_hdr = "- 💡 **Region-Specific Student Savings Tip:** [1 high-impact money-saving hack tailored for students]"
            tips_hdr = f"## 🎒 Essential Student Tips for {dest_clean}"
        else:
            persona_text = "You are an award-winning travel architect and cultural concierge specializing in refined, curated, immersive travel journeys."
            budget_hdr = f"## 💰 Estimated Travel Budget Breakdown ({curr})"
            savings_hdr = "- 💡 **Curated Traveler Tip:** [1 high-impact local secret or priority booking tip for travelers]"
            tips_hdr = f"## 🗺️ Essential Travel Tips & Guidance for {dest_clean}"

        return f"""
        {persona_text}
        Create a detailed {req.days}-day trip itinerary to {dest_clean}.

        Travel Parameters:
        - Destination: {dest_clean}
        - Duration: {req.days} Days
        - Traveler Region/Currency: {region_info} ({curr})
        - Budget Level: {budget_text}
        - Specific Interests: {interests_str}
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

    def _query_groq_models(self, prompt: str) -> Optional[str]:
        """Iterate through the model fallback cascade until a valid response is produced."""
        api_key = settings.groq_api_key
        if not api_key:
            return None

        try:
            client = Groq(api_key=api_key)
            for model_name in settings.groq_models:
                try:
                    completion = client.chat.completions.create(
                        messages=[{"role": "user", "content": prompt}],
                        model=model_name,
                    )
                    content = completion.choices[0].message.content
                    if content and len(content.strip()) > 50:
                        return content
                except Exception:
                    continue
        except Exception:
            pass

        return None

    def _extract_landmarks_and_itinerary(
        self,
        response_text: str,
        dest_clean: str,
        target_count: int
    ) -> Tuple[str, List[str]]:
        """Parse markdown response and extract the LANDMARKS trailer."""
        if "LANDMARKS:" in response_text:
            parts = response_text.split("LANDMARKS:")
            itinerary = parts[0].strip()
            lm_str = parts[1].strip()
            tokens = lm_str.split("|") if "|" in lm_str else lm_str.split(",")
            raw_landmarks = [
                re.sub(r'[\r\n]+', '', l).strip().rstrip('.')
                for l in tokens if l.strip()
            ][:target_count]
        else:
            itinerary = response_text.strip()
            raw_landmarks = [dest_clean]

        return itinerary, raw_landmarks

    def generate_itinerary(self, req: TripRequest) -> Dict[str, Any]:
        """
        Main itinerary orchestrator:
        1. Sanitizes user parameters.
        2. Queries Groq AI with multi-model failover.
        3. Cascades to offline KnowledgeBase fallback if necessary.
        4. Extracts landmarks and calculates collision-free coordinates.
        """
        destination_clean = InputSanitizer.sanitize_string(req.destination, 100)
        if not destination_clean:
            raise ValueError("Invalid destination provided.")

        must_visit_clean = InputSanitizer.sanitize_string(req.must_visit, 100)
        budget_amount_clean = InputSanitizer.sanitize_string(req.budget_amount, 30)
        curr = InputSanitizer.sanitize_string(req.currency, 10) or "USD"
        region_info = InputSanitizer.sanitize_string(req.region, 50) or "Global"
        budget_level_clean = InputSanitizer.sanitize_string(req.budget_level, 40) or "Student (Low)"
        pace_clean = InputSanitizer.sanitize_string(req.travel_pace, 30) or "Balanced"
        accom_clean = InputSanitizer.sanitize_string(req.accommodation_style, 40) or "Hostel"

        sanitized_interests = InputSanitizer.sanitize_list(req.interests, max_items=15, max_item_len=40)
        interests_string = ", ".join(sanitized_interests) if sanitized_interests else "Local street food, culture, secret budget spots"

        target_lm_count = self._calculate_target_landmarks(req.days)
        is_student = bool(req.student_mode if req.student_mode is not None else True)

        budget_text = f"{budget_level_clean} Tier ({curr}) for {region_info} traveler"
        if budget_amount_clean:
            budget_text += f" with strict limit of {budget_amount_clean} {curr}"

        pace_text = f"Pace: {pace_clean}. Accommodation: {accom_clean}."

        prompt = self._build_llm_prompt(
            req=req,
            dest_clean=destination_clean,
            must_visit_clean=must_visit_clean,
            budget_text=budget_text,
            curr=curr,
            region_info=region_info,
            interests_str=interests_string,
            pace_text=pace_text,
            accom_clean=accom_clean,
            is_student=is_student,
            target_lm_count=target_lm_count
        )

        response_text = self._query_groq_models(prompt)

        if not response_text:
            response_text = self._geo.build_fallback_itinerary(
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

        itinerary, raw_landmarks = self._extract_landmarks_and_itinerary(
            response_text, destination_clean, target_lm_count
        )

        dest_coords = self._geo.resolve_coordinates(destination_clean)

        markers = self._placer.place_markers(
            destination_clean=destination_clean,
            dest_coords=dest_coords,
            must_visit_clean=must_visit_clean,
            raw_landmarks=raw_landmarks,
            geo=self._geo
        )

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


# Singleton Planner Instance
travel_planner = TravelPlannerService.get_instance()

# Backward-compatible function export
def generate_trip_itinerary(req: TripRequest) -> Dict[str, Any]:
    return travel_planner.generate_itinerary(req)
