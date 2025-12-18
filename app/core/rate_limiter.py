import time
from fastapi import HTTPException, status, Request

RATE_LIMIT = 10
WINDOW = 10
requests_log = {}


async def rate_limiter(request: Request):
    client_ip = request.client.host
    now = time.time()

    timestamps = requests_log.get(client_ip, [])
    timestamps = [t for t in timestamps if now - t < WINDOW]

    if len(timestamps) >= RATE_LIMIT:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded. Try again after {WINDOW} seconds.",
        )

    timestamps.append(now)
    requests_log[client_ip] = timestamps
