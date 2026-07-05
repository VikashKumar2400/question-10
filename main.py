import time
import uuid
from collections import defaultdict, deque

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

app = FastAPI()

# ==========================================
# YOUR IITM EMAIL
# ==========================================
EMAIL = "23f3003537@ds.study.iitm.ac.in"

# ==========================================
# CORS
# ==========================================
# Replace the second origin with the actual
# exam page origin if you know it.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://app-e43t0y.example.com",
        # "https://<exam-origin>",
    ],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==========================================
# RATE LIMITER
# ==========================================
RATE_LIMIT = 13
WINDOW = 10

clients = defaultdict(deque)


@app.middleware("http")
async def request_context_and_rate_limit(request: Request, call_next):

    # ---------- Request ID ----------
    request_id = request.headers.get("X-Request-ID")
    if not request_id:
        request_id = str(uuid.uuid4())

    request.state.request_id = request_id

    # Skip rate limiting for OPTIONS (CORS preflight)
    if request.method != "OPTIONS":

        client_id = request.headers.get("X-Client-Id", "anonymous")

        now = time.time()

        q = clients[client_id]

        while q and now - q[0] >= WINDOW:
            q.popleft()

        if len(q) >= RATE_LIMIT:
            response = JSONResponse(
                status_code=429,
                content={"detail": "Rate limit exceeded"},
            )
            response.headers["X-Request-ID"] = request_id
            return response

        q.append(now)

    response = await call_next(request)

    response.headers["X-Request-ID"] = request_id

    return response


@app.get("/")
async def home():
    return {"status": "running"}


@app.get("/ping")
async def ping(request: Request):
    return {
        "email": EMAIL,
        "request_id": request.state.request_id,
    }
