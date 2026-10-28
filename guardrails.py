import re
import time
import base64
from collections import deque

INJECTION_PATTERNS = [
    r'ignore\s+(all\s+)?(previous|prior|above)\s+instructions',
    r'disregard\s+(all\s+)?(the\s+)?(instructions|rules)',
    r'forget\s+everything',
    r'you\s+are\s+now\s+a',
    r'system\s*(override|message|prompt)',
    r'new\s+priority',
    r'(set\s+aside|override|bypass)\s+(all\s+|any\s+)?(the\s+)?(rules|instructions|restrictions)',
    r'(no|without)\s+(rules|restrictions|limits|filters)',
    r"(i\s*am|i'm)\s+(the|your)\s+(developer|admin|creator)",
    r'(print|show|reveal|display|repeat)\s+your\s+(system\s+)?(configuration|config|instructions|prompt|rules)',
    r'puuza\s+maagizo',
]

PII_PATTERNS = {
    'email': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b',
    'kenya_phone': r'(?:\+254|\b0)[17]\d{8}\b',
    'credit_card': r'\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b',
}


def _normalize(text):
    text = re.sub(r'[\u200b\u200c\u200d]', '', text.lower())
    return re.sub(r'\s+', ' ', text)


def _variants(text):
    variants = [_normalize(text)]
    for token in re.findall(r'[A-Za-z0-9+/=]{16,}', text):
        try:
            decoded = base64.b64decode(token, validate=True).decode('utf-8')
            if decoded.isprintable():
                variants.append(_normalize(decoded))
        except Exception:
            pass
    return variants


def is_injection(text):
    if len(text) > 2000:
        return True
    return any(re.search(p, v) for v in _variants(text) for p in INJECTION_PATTERNS)


def redact_pii(text):
    found = []
    for name, pattern in PII_PATTERNS.items():
        if re.search(pattern, text):
            found.append(name)
            text = re.sub(pattern, f'[REDACTED_{name.upper()}]', text)
    return text, found


class RateLimiter:
    def __init__(self, max_requests=10, window_seconds=60):
        self.max_requests = max_requests
        self.window = window_seconds
        self.requests = {}

    def allow(self, user_id):
        now = time.time()
        q = self.requests.setdefault(user_id, deque())
        while q and now - q[0] > self.window:
            q.popleft()
        if len(q) >= self.max_requests:
            return False
        q.append(now)
        return True
