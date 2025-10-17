"""
Abuse Detection Middleware

Detecta e registra padrões suspeitos de uso:
- Múltiplas requisições idênticas
- Padrões de bot/scraping
- IPs com alto volume de erros
"""

import logging
from collections import defaultdict
from typing import Dict, List
from datetime import datetime, timedelta
from fastapi import Request
import hashlib

logger = logging.getLogger(__name__)


class AbuseDetector:
    def __init__(self):
        # Store request signatures per IP
        self.request_signatures: Dict[str, List[tuple]] = defaultdict(list)

        # Store error counts per IP
        self.error_counts: Dict[str, int] = defaultdict(int)

        # Blacklisted IPs
        self.blacklist: set = set()

        # Suspicious patterns
        self.suspicious_ips: set = set()

    def _generate_signature(self, request: Request) -> str:
        """Generate a signature for the request based on path + body"""
        path = request.url.path
        # Use method + path as simple signature
        return hashlib.md5(f"{request.method}:{path}".encode()).hexdigest()

    def check_request(self, request: Request) -> dict:
        """
        Check if request looks suspicious.

        Returns:
            dict: {
                "suspicious": bool,
                "reason": str,
                "should_block": bool
            }
        """
        client_ip = request.client.host if request.client else "unknown"

        # Check blacklist
        if client_ip in self.blacklist:
            logger.warning(f"🚫 Blocked request from blacklisted IP: {client_ip}")
            return {
                "suspicious": True,
                "reason": "IP is blacklisted",
                "should_block": True,
            }

        # Generate request signature
        signature = self._generate_signature(request)
        now = datetime.now()

        # Clean old signatures (keep last 10 minutes)
        cutoff = now - timedelta(minutes=10)
        self.request_signatures[client_ip] = [
            (sig, timestamp)
            for sig, timestamp in self.request_signatures[client_ip]
            if timestamp > cutoff
        ]

        # Check for duplicate requests (same signature > 20 times in 10 min)
        recent_signatures = [sig for sig, _ in self.request_signatures[client_ip]]
        duplicate_count = recent_signatures.count(signature)

        if duplicate_count > 20:
            logger.warning(
                f"⚠️ Suspicious pattern detected: IP {client_ip} sent same request {duplicate_count} times in 10 min"
            )
            self.suspicious_ips.add(client_ip)
            return {
                "suspicious": True,
                "reason": f"Duplicate requests: {duplicate_count} times",
                "should_block": False,  # Just log, don't block yet
            }

        # Check for bot-like user agents
        user_agent = request.headers.get("user-agent", "").lower()
        bot_patterns = ["bot", "crawler", "spider", "scraper", "curl", "wget"]
        if any(pattern in user_agent for pattern in bot_patterns):
            logger.info(f"🤖 Bot detected: {client_ip} - {user_agent}")
            return {
                "suspicious": True,
                "reason": f"Bot user-agent: {user_agent}",
                "should_block": False,  # Allow bots, just log
            }

        # Add to signatures
        self.request_signatures[client_ip].append((signature, now))

        return {"suspicious": False, "reason": None, "should_block": False}

    def record_error(self, client_ip: str, status_code: int):
        """Record error for IP (used to detect malicious scanning)"""
        if status_code >= 400:
            self.error_counts[client_ip] += 1

            # If too many errors (>50 in recent history), blacklist
            if self.error_counts[client_ip] > 50:
                logger.error(f"🚫 Blacklisting IP due to excessive errors: {client_ip}")
                self.blacklist.add(client_ip)

    def get_stats(self) -> dict:
        """Get abuse detection statistics"""
        return {
            "blacklisted_ips": len(self.blacklist),
            "suspicious_ips": len(self.suspicious_ips),
            "monitored_ips": len(self.request_signatures),
            "blacklist": list(self.blacklist),
            "suspicious": list(self.suspicious_ips),
        }


# Global instance
abuse_detector = AbuseDetector()
