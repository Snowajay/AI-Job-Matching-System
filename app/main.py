from fastapi import FastAPI
from app.routers import candidates, jobs, matches

app = FastAPI(title="AI Job Matching System")

app.include_router(jobs.router, prefix="/api/v1")
app.include_router(candidates.router, prefix="/api/v1")
app.include_router(matches.router, prefix="/api/v1")

@app.get("/")
def root():
    return {"message": "AI Job Matching System API"}
