import time
import uuid
from collections import defaultdict, deque

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

app = FastAPI()

# ===========================
# CHANGE THIS TO YOUR EMAIL
# ===========================
EMAIL = "23f3003537@ds.study.iitm.ac.in"

# Allowed origins
ALLOWED_ORIGINS = [
    "https://app-e43t0y.example.com",

    # IMPORTANT:
    # Replace this with the origin of the exam page if different.
    # Example:
    # "https://exam.example.com"
]

# ---------------------------
# CORS Middleware
# ---------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------
# Rate Limiter
# ---------------------------

RATE_LIMIT = 13
WINDOW = 10  # seconds

client_requests = defaultdict(deque)


@app.middleware("http")
async def middleware(request: Request, call_next):
    # -------------------------
    # Request Context
    # -------------------------
    request_id = request.headers.get("X-Request-ID")

    if not request_id:
        request_id = str(uuid.uuid4())

    request.state.request_id = request_id

    # -------------------------
    # Rate Limiting
    # -------------------------
    client_id = request.headers.get("X-Client-Id", "anonymous")

    now = time.time()
    bucket = client_requests[client_id]

    while bucket and now - bucket[0] > WINDOW:
        bucket.popleft()

    if len(bucket) >= RATE_LIMIT:
        response = JSONResponse(
            status_code=429,
            content={
                "detail": "Rate limit exceeded"
            }
        )
        response.headers["X-Request-ID"] = request_id
        return response

    bucket.append(now)

    # Continue request
    response = await call_next(request)

    response.headers["X-Request-ID"] = request_id

    return response


# ---------------------------
# Endpoint
# ---------------------------

@app.get("/ping")
async def ping(request: Request):
    return {
        "email": EMAIL,
        "request_id": request.state.request_id
    }