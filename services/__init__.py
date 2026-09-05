# -*- coding: utf-8 -*-
"""
RoamAI Services Package.
Provides GeoLocation intelligence and AI-powered Travel Planning services.
"""
from services.knowledge_base import (
    GeoLocationService,
    geo_service,
    get_coordinates,
    get_destination_key,
    generate_fallback_itinerary,
    COORD_CACHE,
    DESTINATION_DB
)
from services.itinerary_service import (
    TripRequest,
    BasePlannerService,
    LandmarkCoordinatePlacer,
    TravelPlannerService,
    travel_planner,
    generate_trip_itinerary
)

__all__ = [
    "GeoLocationService",
    "geo_service",
    "get_coordinates",
    "get_destination_key",
    "generate_fallback_itinerary",
    "COORD_CACHE",
    "DESTINATION_DB",
    "TripRequest",
    "BasePlannerService",
    "LandmarkCoordinatePlacer",
    "TravelPlannerService",
    "travel_planner",
    "generate_trip_itinerary"
]
