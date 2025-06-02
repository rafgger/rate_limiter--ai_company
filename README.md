# FastAPI rate limiter + test (and Express ver.)

A simple limiter in FastAPI to test rate limits of endpoints.
## Install dependencies
```pip install fastapi uvicorn```

## Usage in VS Code – Python:
- Install dependencies: ```pip install fastapi uvicorn```
- Run with: ```python main.py``` or ```uvicorn main:app --reload```
- Test the endpoints and observe rate limiting in action

The rate limiter handles proxy headers (X-Forwarded-For, X-Real-IP) for proper IP detection behind reverse proxies, and returns proper HTTP 429 responses when limits are exceeded.

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
