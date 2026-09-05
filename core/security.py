# -*- coding: utf-8 -*-
"""
RoamAI Security Suite.
Encapsulates Object-Oriented Input Sanitization, Memory-Safe Rate Limiting,
and Hardened HTTP Security Headers Middleware.
"""
from __future__ import annotations
import re
import time
import threading
from typing import Optional, Dict, List, Pattern
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from core.config import settings


class InputSanitizer:
    """
    Encapsulates input validation, sanitization rules, and boundary checks.
    Guards against XSS, control character injections, and buffer overflows.
    """
    _SCRIPT_OR_STYLE: Pattern = re.compile(r'<(script|style)[^>]*?>.*?</\1>', re.IGNORECASE | re.DOTALL)
    _HTML_TAGS: Pattern = re.compile(r'<[^>]*?>')
    _CONTROL_CHARS: Pattern = re.compile(r'[\x00-\x1f\x7f-\x9f]')
    _EXCESS_WHITESPACE: Pattern = re.compile(r'\s+')

    @classmethod
    def strip_html_tags(cls, val: str) -> str:
        """Strip dangerous script/style blocks and remaining HTML tags."""
        if not val:
            return ""
        no_scripts = cls._SCRIPT_OR_STYLE.sub('', val)
        return cls._HTML_TAGS.sub('', no_scripts)

    @classmethod
    def sanitize_string(cls, val: Optional[str], max_len: int = 120) -> str:
        """
        Sanitize string input:
        1. Convert to string and strip outer whitespace.
        2. Remove raw HTML tags.
        3. Remove non-printable control characters.
        4. Normalize inner whitespace sequences.
        5. Enforce max character limit.
        """
        if val is None:
            return ""
        text = str(val).strip()
        text = cls.strip_html_tags(text)
        text = cls._CONTROL_CHARS.sub('', text)
        text = cls._EXCESS_WHITESPACE.sub(' ', text)
        return text[:max_len].strip()

    @classmethod
    def sanitize_query(cls, val: Optional[str], max_len: int = 120) -> str:
        """Sanitizes search and geocoding queries."""
        return cls.sanitize_string(val, max_len=max_len)

    @classmethod
    def sanitize_list(cls, items: Optional[List[str]], max_items: int = 15, max_item_len: int = 40) -> List[str]:
        """Sanitizes an array of input strings with bounded quantity and length."""
        if not items:
            return []
        cleaned: List[str] = []
        for item in items:
            s = cls.sanitize_string(item, max_len=max_item_len)
            if s and s not in cleaned:
                cleaned.append(s)
            if len(cleaned) >= max_items:
                break
        return cleaned


class RateLimiter:
    """
    Thread-safe, sliding-window rate limiter per client IP with 
    active stale-entry eviction to prevent memory exhaustion DoS attacks.
    """
    def __init__(
        self,
        max_requests: int = settings.rate_limit_requests,
        window_seconds: int = settings.rate_limit_window_seconds,
        max_tracked_ips: int = 5000
    ) -> None:
        self._max_requests: int = max_requests
        self._window_seconds: int = window_seconds
        self._max_tracked_ips: int = max_tracked_ips
        self._requests: Dict[str, List[float]] = {}
        self._lock: threading.Lock = threading.Lock()
        self._last_eviction: float = time.time()

    @property
    def max_requests(self) -> int:
        return self._max_requests

    @property
    def window_seconds(self) -> int:
        return self._window_seconds

    @property
    def tracked_ips_count(self) -> int:
        with self._lock:
            return len(self._requests)

    def _evict_stale_records(self, now: float) -> None:
        """Purge IP buckets that have no timestamps within the active sliding window."""
        cutoff = now - self._window_seconds
        stale_keys = [
            ip for ip, timestamps in self._requests.items()
            if not timestamps or timestamps[-1] < cutoff
        ]
        for ip in stale_keys:
            self._requests.pop(ip, None)
        self._last_eviction = now

    def is_rate_limited(self, client_ip: str) -> bool:
        """
        Check whether the client IP has exceeded the allowed request quota.
        Returns True if rate limited, False if allowed.
        """
        now = time.time()
        client_key = client_ip.strip() if client_ip else "unknown"

        with self._lock:
            # Periodically or on table overflow, purge stale records to avoid unbounded growth
            if (now - self._last_eviction > self._window_seconds * 2) or (len(self._requests) > self._max_tracked_ips):
                self._evict_stale_records(now)

            timestamps = self._requests.get(client_key, [])
            # Prune timestamps outside current window
            valid_timestamps = [t for t in timestamps if now - t < self._window_seconds]

            if len(valid_timestamps) >= self._max_requests:
                self._requests[client_key] = valid_timestamps
                return True

            valid_timestamps.append(now)
            self._requests[client_key] = valid_timestamps
            return False

    def reset(self) -> None:
        """Reset rate limiter cache."""
        with self._lock:
            self._requests.clear()


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Production-grade HTTP response security headers middleware.
    Mitigates Clickjacking, MIME sniffing, XSS, and Cross-Site leaks.
    """
    _CSP_POLICY: str = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.tailwindcss.com https://unpkg.com https://cdnjs.cloudflare.com; "
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com https://unpkg.com https://cdnjs.cloudflare.com; "
        "font-src 'self' https://fonts.gstatic.com data:; "
        "img-src 'self' data: https: blob:; "
        "connect-src 'self' https://nominatim.openstreetmap.org https://*.tile.openstreetmap.org; "
        "frame-ancestors 'self';"
    )

    async def dispatch(self, request: Request, call_next):
        response: Response = await call_next(request)
        headers = response.headers
        headers["X-Content-Type-Options"] = "nosniff"
        headers["X-Frame-Options"] = "SAMEORIGIN"
        headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        headers["X-XSS-Protection"] = "1; mode=block"
        headers["Permissions-Policy"] = "geolocation=(), camera=(), microphone=()"
        headers["Content-Security-Policy"] = self._CSP_POLICY
        return response


# Global Security Instances
sanitizer = InputSanitizer()
rate_limiter = RateLimiter()

# Backward-compatible function aliases
def sanitize_str(val: Optional[str], max_len: int = 120) -> str:
    return InputSanitizer.sanitize_string(val, max_len)

def sanitize_query(val: Optional[str], max_len: int = 120) -> str:
    return InputSanitizer.sanitize_query(val, max_len)
