# -*- coding: utf-8 -*-
"""
RoamAI Application Entry Point.
Encapsulates FastAPI Application Factory, Security Middleware Pipelines,
Defensive Exception Handlers, and Route Registrations using Object-Oriented Design.
"""
from __future__ import annotations
import time
from typing import Optional
from fastapi import FastAPI, Request, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import HTMLResponse, JSONResponse

from core.config import settings
from core.security import (
    SecurityHeadersMiddleware,
    rate_limiter,
    InputSanitizer
)
from services.knowledge_base import geo_service
from services.itinerary_service import (
    TripRequest,
    travel_planner
)
from ui.layout import get_page_html


class RoamAIApplication:
    """
    Object-Oriented Application Builder & Lifecycle Manager.
    Encapsulates ASGI setup, middleware pipelines, error sanitization, and routing.
    """
    def __init__(self) -> None:
        self._settings = settings
        self._geo = geo_service
        self._planner = travel_planner
        self._rate_limiter = rate_limiter

        self._app = FastAPI(
            title=self._settings.app_title,
            description=self._settings.app_description,
            version=self._settings.app_version,
            docs_url="/api/docs",
            redoc_url=None
        )

        self._configure_middlewares()
        self._register_exception_handlers()
        self._register_routes()

    @property
    def app(self) -> FastAPI:
        """Accessor for the underlying FastAPI ASGI instance."""
        return self._app

    def _configure_middlewares(self) -> None:
        """Bind security headers, compression, and CORS middleware."""
        # 1. Hardened Security & CSP Headers
        self._app.add_middleware(SecurityHeadersMiddleware)

        # 2. Performance: GZip Compression for payloads exceeding 1000 bytes
        self._app.add_middleware(GZipMiddleware, minimum_size=1000)

        # 3. Controlled Cross-Origin Access
        self._app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["GET", "POST", "OPTIONS", "HEAD"],
            allow_headers=["*"],
        )

    def _register_exception_handlers(self) -> None:
        """Defensive exception masking to prevent internal server traceback leaks."""
        @self._app.exception_handler(Exception)
        async def generic_exception_handler(request: Request, exc: Exception):
            # Internal server error masked for client safety
            return JSONResponse(
                status_code=500,
                content={
                    "error": "Internal Server Error",
                    "message": "An unexpected error occurred while processing your request. Please try again later."
                }
            )

    def _register_routes(self) -> None:
        """Register application routes and REST API endpoints."""

        @self._app.api_route("/", methods=["GET", "HEAD"], response_class=HTMLResponse)
        async def serve_index():
            """Serve the single-page application with caching headers directly from Python memory."""
            html = get_page_html()
            response = HTMLResponse(content=html, status_code=200)
            response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"
            return response

        @self._app.get("/api/health")
        def health_check():
            """Service health status and secure configuration telemetry."""
            return {
                "status": "healthy",
                "version": self._settings.app_version,
                "groq_configured": self._settings.is_groq_configured,
                "groq_key_masked": self._settings.masked_groq_key,
                "models_available": list(self._settings.groq_models),
                "cached_destinations": self._geo.destination_count,
                "active_rate_limited_ips": self._rate_limiter.tracked_ips_count,
                "timestamp": time.time()
            }

        @self._app.post("/api/generate")
        async def api_generate_itinerary(req: TripRequest, request: Request):
            """Generate an AI-powered travel itinerary with rate limiting and security checks."""
            client_ip = request.client.host if request.client else "unknown"
            if self._rate_limiter.is_rate_limited(client_ip):
                raise HTTPException(
                    status_code=429,
                    detail="Rate limit exceeded. Please wait a moment before generating another trip."
                )

            try:
                result = self._planner.generate_itinerary(req)
                return JSONResponse(content=result)
            except ValueError as ve:
                raise HTTPException(status_code=400, detail=str(ve))
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Planning service error: {str(e)}")

        @self._app.get("/api/geocode")
        def geocode_destination(q: str = Query(..., min_length=1, max_length=120)):
            """Fast geocoding lookup for destinations with cache-first resolution."""
            cleaned = InputSanitizer.sanitize_query(q, max_len=100)
            if not cleaned:
                raise HTTPException(status_code=400, detail="Invalid destination query.")

            coords = self._geo.resolve_coordinates(cleaned)
            if not coords:
                coords = [20.5937, 78.9629]

            return {
                "destination": cleaned,
                "lat": coords[0],
                "lon": coords[1],
                "is_default": (coords[0] == 20.5937 and coords[1] == 78.9629 and cleaned.lower() not in ["india", "bharat"])
            }


# Instantiate Application Factory
roamai_app = RoamAIApplication()
app = roamai_app.app

# Direct execution entry point
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app:app",
        host=settings.default_host,
        port=settings.default_port,
        reload=True
    )
