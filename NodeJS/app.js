// npm install express
// run with: node app.js or nodemon app.js
const express = require('express');
const app = express();

app.use(express.json()); // for parsing JSON body
const PORT = process.env.PORT || 8000;

// Token Bucket class
class TokenBucket {
    constructor(capacity, refillRate) {
        this.capacity = capacity;
        this.tokens = capacity;
        this.refillRate = refillRate; // tokens per second
        this.lastRefill = Date.now() / 1000;
    }

    refill() {
        const now = Date.now() / 1000;
        const elapsed = now - this.lastRefill;
        this.tokens = Math.min(this.capacity, this.tokens + elapsed * this.refillRate);
        this.lastRefill = now;
    }

    consume(tokens = 1) {
        this.refill();
        if (this.tokens >= tokens) {
            this.tokens -= tokens;
            return true;
        }
        return false;
    }

    timeToNextToken() {
        if (this.tokens >= 1) return 0;
        return (1 - this.tokens) / this.refillRate;
    }
}

// Rate limiter manager
class RateLimiter {
    constructor(requestsPerMinute = 60, burstSize = null) {
        this.requestsPerMinute = requestsPerMinute;
        this.burstSize = burstSize || requestsPerMinute;
        this.refillRate = requestsPerMinute / 60;
        this.buckets = new Map();
        this.cleanupInterval = 300000; // 5 mins
        this.lastCleanup = Date.now();
    }

    getBucket(ip) {
        if (!this.buckets.has(ip)) {
            this.buckets.set(ip, new TokenBucket(this.burstSize, this.refillRate));
        }
        return this.buckets.get(ip);
    }

    cleanupOldBuckets() {
        const now = Date.now();
        if (now - this.lastCleanup < this.cleanupInterval) return;
        const cutoff = (now - 3600000) / 1000;
        for (const [ip, bucket] of this.buckets) {
            if (bucket.lastRefill < cutoff) {
                this.buckets.delete(ip);
            }
        }
        this.lastCleanup = now;
    }

    isAllowed(ip) {
        this.cleanupOldBuckets();
        const bucket = this.getBucket(ip);
        const allowed = bucket.consume(1);
        const info = {
            remaining: Math.floor(bucket.tokens),
            capacity: bucket.capacity,
            reset_time: Math.floor(Date.now() / 1000 + bucket.timeToNextToken()),
            retry_after: allowed ? 0 : Math.ceil(bucket.timeToNextToken())
        };
        return { allowed, info };
    }
}

// Middleware factory
function rateLimitMiddleware(limiter) {
    return (req, res, next) => {
        const ip = req.headers['x-forwarded-for']?.split(',')[0] || req.socket.remoteAddress;
        const { allowed, info } = limiter.isAllowed(ip);

        res.setHeader('X-RateLimit-Remaining', info.remaining);
        res.setHeader('X-RateLimit-Reset', info.reset_time);

        if (!allowed) {
            res.setHeader('Retry-After', info.retry_after);
            return res.status(429).json({
                error: "Rate limit exceeded",
                message: `Too many requests. Try again in ${info.retry_after} seconds.`,
                retry_after: info.retry_after
            });
        }

        // Attach info for other handlers if needed
        req.rateLimitInfo = info;
        next();
    };
}

// Limiter instances
const defaultLimiter = new RateLimiter(6, 10);
const strictLimiter = new RateLimiter(2, 5);
const uploadLimiter = new RateLimiter(10, 2);

// Routes
app.get('/', (req, res) => {
    res.json({ message: 'Welcome to the Rate Limited API' });
});

app.get('/api/data', rateLimitMiddleware(defaultLimiter), (req, res) => {
    res.json({
        message: "This is rate limited data",
        timestamp: Date.now() / 1000,
        client_ip: req.socket.remoteAddress
    });
});

app.get('/api/premium', rateLimitMiddleware(strictLimiter), (req, res) => {
    res.json({
        message: "This is premium content with strict rate limiting",
        timestamp: Date.now() / 1000,
        data: { premium: true, value: "exclusive_content" }
    });
});

app.post('/api/upload', rateLimitMiddleware(uploadLimiter), (req, res) => {
    res.json({
        message: "Data uploaded successfully",
        received_data: req.body,
        timestamp: Date.now() / 1000
    });
});

app.get('/api/status', (req, res) => {
    const ip = req.headers['x-forwarded-for']?.split(',')[0] || req.socket.remoteAddress;
    const status = {};

    for (const [name, limiter] of [["default", defaultLimiter], ["strict", strictLimiter]]) {
        const bucket = limiter.buckets.get(ip);
        if (bucket) {
            bucket.refill();
            status[name] = {
                remaining_requests: Math.floor(bucket.tokens),
                capacity: bucket.capacity,
                refill_rate_per_minute: limiter.requestsPerMinute
            };
        } else {
            status[name] = {
                remaining_requests: limiter.burstSize,
                capacity: limiter.burstSize,
                refill_rate_per_minute: limiter.requestsPerMinute
            };
        }
    }

    res.json({
        client_ip: ip,
        rate_limit_status: status,
        timestamp: Date.now() / 1000
    });
});

app.listen(PORT, () => {
    console.log(`Server is running on port ${PORT}`);
});
