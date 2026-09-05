from fastapi import FastAPI
from app.routes.jobs import router as jobs_router
from app.routers import candidates, matches

app = FastAPI(title="AI Job Matching System")

app.include_router(jobs_router)
app.include_router(candidates.router, prefix="/api/v1")
app.include_router(matches.router, prefix="/api/v1")

@app.get("/")
def root():
    return {"message": "AI Job Matching System API"}
