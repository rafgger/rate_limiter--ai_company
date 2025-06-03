# FastAPI rate limiter + test (and Express ver.)

A simple limiter in FastAPI to test rate limits of endpoints.
## Install dependencies
```pip install fastapi uvicorn```

## Usage in VS Code – Python:
- Install dependencies: ```pip install fastapi uvicorn```
- Run with:  ```uvicorn main:app --reload```
- Test the endpoints and observe rate limiting in action

The rate limiter handles proxy headers (X-Forwarded-For, X-Real-IP) for proper IP detection behind reverse proxies, and returns proper HTTP 429 responses when limits are exceeded.

Listening on port ```http://127.0.0.1:8000/docs```
Visit `http://localhost:8000/test` for the testing interface

## Test – Python (uses requests library)

# Install requests if you don't have it
```pip install requests```

# Run full test suite
```python simple_rate_test.py```

# Or run normal or quick burst test
python ```simple_rate_test.py``` 
or: ```python simple_rate_test.py quick```

## Express – Node.js
- Go into ```cd NodeJS```
- Install dependencies: ```npm install express```
- Run with: ```node app.js``` or ```nodemon app.js```
- Test the endpoints and observe rate limiting in action with previous ```python simple_rate_test.py```

# FastAPI Rate Limiter on Vercel

A production-ready rate limiter built with FastAPI and deployed on Vercel's serverless platform.

## Features

- 🚀 **Serverless Deployment**: Runs on Vercel's edge network
- 🛡️ **Token Bucket Algorithm**: Smooth rate limiting with burst capacity
- 🌐 **Multiple Endpoints**: Different rate limits for different use cases
- 🧪 **Built-in Testing**: Web interface for easy testing
- 📊 **Real-time Status**: Check current rate limit status
- 🔧 **Easy to Configure**: Customizable rate limits per endpoint

## Endpoints

- `GET /` - Welcome page with API information
- `GET /api/data` - Standard rate limit (60 req/min, burst 10)
- `GET /api/premium` - Strict rate limit (20 req/min, burst 5)
- `POST /api/upload` - Upload rate limit (10 req/min, burst 2)
- `GET /api/status` - Check rate limit status
- `GET /test` - Web-based testing interface
- `GET /health` - Health check endpoint

## Local Development

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Run locally:
   ```bash
   uvicorn api.main:app --reload
   ```

3. Visit `http://localhost:8000/test` for the testing interface

## Deployment on Vercel

1. Fork/clone this repository
2. Connect your GitHub repo to Vercel
3. Deploy automatically - Vercel will detect the configuration

## Testing

Visit `/test` endpoint on your deployed URL for an interactive testing interface, or use curl:

```bash
# Test rate limiting
curl https://your-app.vercel.app/api/data

# Check status
curl https://your-app.vercel.app/api/status

# Test upload
curl -X POST https://your-app.vercel.app/api/upload \
  -H "Content-Type: application/json" \
  -d '{"test": "data"}'
```

## Rate Limit Headers

The API returns standard rate limiting headers:
- `X-RateLimit-Remaining`: Requests remaining in current window
- `X-RateLimit-Reset`: Unix timestamp when rate limit resets
- `Retry-After`: Seconds to wait before next request (when rate limited)

## Customization

Edit `api/main.py` to customize:
- Rate limits per endpoint
- Burst capacities
- IP extraction logic
- Add new endpoints with different limits

Built with ❤️ using FastAPI and deployed on Vercel.
