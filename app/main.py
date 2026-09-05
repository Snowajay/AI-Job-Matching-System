from fastapi import FastAPI

from app.routers import candidates, matches

app = FastAPI(title="Job Matching System")

app.include_router(candidates.router, prefix="/api/v1")
app.include_router(matches.router, prefix="/api/v1")
