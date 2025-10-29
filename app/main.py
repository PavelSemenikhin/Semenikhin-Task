from fastapi import FastAPI
from app.api.routes.stats import router as stats_router
from app.api.routes.events import router as events_router
app = FastAPI()

app.include_router(stats_router)
app.include_router(events_router)
@app.get("/")
async def root():
    return {"message": "done"}