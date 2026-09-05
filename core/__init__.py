# -*- coding: utf-8 -*-
"""
RoamAI Core Package.
Provides centralized configuration, input sanitization, rate limiting, and security middleware.
"""
from core.config import (
    Settings,
    settings,
    APP_TITLE,
    APP_DESCRIPTION,
    APP_VERSION,
    GROQ_MODELS,
    BASE_DIR,
    STATIC_DIR,
    TEMPLATES_DIR,
    RATE_LIMIT_REQUESTS,
    RATE_LIMIT_WINDOW_SECONDS,
    DEFAULT_HOST,
    DEFAULT_PORT
)
from core.security import (
    InputSanitizer,
    RateLimiter,
    SecurityHeadersMiddleware,
    sanitizer,
    rate_limiter,
    sanitize_str,
    sanitize_query
)

__all__ = [
    "Settings",
    "settings",
    "APP_TITLE",
    "APP_DESCRIPTION",
    "APP_VERSION",
    "GROQ_MODELS",
    "BASE_DIR",
    "STATIC_DIR",
    "TEMPLATES_DIR",
    "RATE_LIMIT_REQUESTS",
    "RATE_LIMIT_WINDOW_SECONDS",
    "DEFAULT_HOST",
    "DEFAULT_PORT",
    "InputSanitizer",
    "RateLimiter",
    "SecurityHeadersMiddleware",
    "sanitizer",
    "rate_limiter",
    "sanitize_str",
    "sanitize_query"
]
