from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import candidates, jobs, matches

app = FastAPI(title="AI Job Matching System")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(jobs.router, prefix="/api/v1")
app.include_router(candidates.router, prefix="/api/v1")
app.include_router(matches.router, prefix="/api/v1")

@app.get("/")
def root():
    return {"message": "AI Job Matching System API"}
