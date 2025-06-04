from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.responses import JSONResponse
import time
from typing import Dict, Optional
from dataclasses import dataclass
import asyncio

app = FastAPI(title="Rate Limited API", version="1.0.0")

@dataclass
class TokenBucket:
    """Token bucket for rate limiting"""
    capacity: int
    tokens: float
    refill_rate: float  # tokens per second
    last_refill: float
    
    def consume(self, tokens: int = 1) -> bool:
        """Try to consume tokens. Returns True if successful."""
        now = time.time()
        
        # Refill tokens based on time elapsed
        time_passed = now - self.last_refill
        self.tokens = min(self.capacity, self.tokens + time_passed * self.refill_rate)
        self.last_refill = now
        
        # Try to consume tokens
        if self.tokens >= tokens:
            self.tokens -= tokens
            return True
        return False

class RateLimiter:
    """Rate limiter using token bucket algorithm"""
    
    def __init__(self, requests_per_minute: int = 60, burst_size: Optional[int] = None):
        self.requests_per_minute = requests_per_minute
        self.burst_size = burst_size or requests_per_minute
        self.buckets: Dict[str, TokenBucket] = {}
        self.cleanup_interval = 300  # Clean up old buckets every 5 minutes
        self.last_cleanup = time.time()
    
    def _cleanup_old_buckets(self):
        """Remove buckets that haven't been used recently"""
        now = time.time()
        if now - self.last_cleanup < self.cleanup_interval:
            return
            
        cutoff_time = now - 3600  # Remove buckets older than 1 hour
        keys_to_remove = [
            key for key, bucket in self.buckets.items()
            if bucket.last_refill < cutoff_time
        ]
        
        for key in keys_to_remove:
            del self.buckets[key]
        
        self.last_cleanup = now
    
    def is_allowed(self, identifier: str) -> tuple[bool, dict]:
        """Check if request is allowed and return status info"""
        self._cleanup_old_buckets()
        
        if identifier not in self.buckets:
            self.buckets[identifier] = TokenBucket(
                capacity=self.burst_size,
                tokens=self.burst_size,
                refill_rate=self.requests_per_minute / 60.0,  # Convert to per second
                last_refill=time.time()
            )
        
        bucket = self.buckets[identifier]
        allowed = bucket.consume(1)
        
        # Calculate time until next token is available
        time_to_next_token = 0
        if not allowed:
            time_to_next_token = (1 - bucket.tokens) / bucket.refill_rate
        
        return allowed, {
            "remaining": int(bucket.tokens),
            "capacity": bucket.capacity,
            "reset_time": time.time() + time_to_next_token,
            "retry_after": int(time_to_next_token) + 1 if not allowed else 0
        }

# Create rate limiter instances for different endpoints
default_limiter = RateLimiter(requests_per_minute=6, burst_size=10)
strict_limiter = RateLimiter(requests_per_minute=2, burst_size=5)

def get_client_ip(request: Request) -> str:
    """Extract client IP address from request"""
    # Check for forwarded headers first (for reverse proxies)
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip
    
    # Fallback to direct client IP
    return request.client.host if request.client else "unknown"

def rate_limit(limiter: RateLimiter = default_limiter):
    """Dependency for rate limiting"""
    def dependency(request: Request):
        client_ip = get_client_ip(request)
        allowed, info = limiter.is_allowed(client_ip)
        
        if not allowed:
            raise HTTPException(
                status_code=429,
                detail={
                    "error": "Rate limit exceeded",
                    "message": f"Too many requests. Try again in {info['retry_after']} seconds.",
                    "retry_after": info["retry_after"]
                },
                headers={
                    "X-RateLimit-Remaining": str(info["remaining"]),
                    "X-RateLimit-Reset": str(int(info["reset_time"])),
                    "Retry-After": str(info["retry_after"])
                }
            )
        
        # Add rate limit headers to successful responses
        request.state.rate_limit_info = info
        return True
    
    return dependency

@app.middleware("http")
async def add_rate_limit_headers(request: Request, call_next):
    """Middleware to add rate limit headers to responses"""
    response = await call_next(request)
    
    # Add rate limit headers if available
    if hasattr(request.state, "rate_limit_info"):
        info = request.state.rate_limit_info
        response.headers["X-RateLimit-Remaining"] = str(info["remaining"])
        response.headers["X-RateLimit-Reset"] = str(int(info["reset_time"]))
    
    return response

# Example endpoints with different rate limits

@app.get("/")
async def root():
    """Root endpoint without rate limiting"""
    return {"message": "Welcome to the Rate Limited API"}

@app.get("/api/data")
async def get_data(request: Request, _: bool = Depends(rate_limit(default_limiter))):
    """Standard endpoint with default rate limiting (6 req/min, burst of 10)"""
    return {
        "message": "This is rate limited data",
        "timestamp": time.time(),
        "client_ip": get_client_ip(request)
    }

@app.get("/api/premium")
async def premium_endpoint(request: Request, _: bool = Depends(rate_limit(strict_limiter))):
    """Premium endpoint with strict rate limiting (2 req/min, burst of 5)"""
    return {
        "message": "This is premium content with strict rate limiting",
        "timestamp": time.time(),
        "data": {"premium": True, "value": "exclusive_content"}
    }

@app.post("/api/upload")
async def upload_data(
    request: Request, 
    data: dict,
    _: bool = Depends(rate_limit(RateLimiter(requests_per_minute=10, burst_size=2)))
):
    """Upload endpoint with very strict rate limiting (10 req/min, burst of 2)"""
    return {
        "message": "Data uploaded successfully",
        "received_data": data,
        "timestamp": time.time()
    }

@app.get("/api/status")
async def rate_limit_status(request: Request):
    """Check current rate limit status without consuming a token"""
    client_ip = get_client_ip(request)
    
    # Check status for different limiters
    status = {}
    
    for name, limiter in [("default", default_limiter), ("strict", strict_limiter)]:
        if client_ip in limiter.buckets:
            bucket = limiter.buckets[client_ip]
            # Update tokens without consuming
            now = time.time()
            time_passed = now - bucket.last_refill
            current_tokens = min(bucket.capacity, bucket.tokens + time_passed * bucket.refill_rate)
            
            status[name] = {
                "remaining_requests": int(current_tokens),
                "capacity": bucket.capacity,
                "refill_rate_per_minute": limiter.requests_per_minute
            }
        else:
            status[name] = {
                "remaining_requests": limiter.burst_size,
                "capacity": limiter.burst_size,
                "refill_rate_per_minute": limiter.requests_per_minute
            }
    
    return {
        "client_ip": client_ip,
        "rate_limit_status": status,
        "timestamp": time.time()
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)