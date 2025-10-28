from fastapi import FastAPI
from app.api.routes.stats import router as stats_router
app = FastAPI()

app.include_router(stats_router)
@app.get("/")
async def root():
    return {"message": "done"}