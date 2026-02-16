
# billing/rate_limit.py
import time
from collections import deque
from dataclasses import dataclass
from typing import Deque, Dict, Tuple

@dataclass
class RateLimitConfig:
    max_requests: int
    window_seconds: int

class SlidingWindowLimiter:
    """
    Limiteur simple 'sliding window' en mémoire.
    Stocke les timestamps des requêtes par (scope, key).
    """
    def __init__(self):
        self._hits: Dict[Tuple[str, str], Deque[float]] = {}

    def allow(self, scope: str, key: str, cfg: RateLimitConfig) -> bool:
        now = time.time()
        bucket_key = (scope, key)
        q = self._hits.get(bucket_key)
        if q is None:
            q = deque()
            self._hits[bucket_key] = q

        # purge des hits hors fenêtre
        cutoff = now - cfg.window_seconds
        while q and q[0] < cutoff:
            q.popleft()

        if len(q) >= cfg.max_requests:
            return False

        q.append(now)
        return True

limiter = SlidingWindowLimiter()
