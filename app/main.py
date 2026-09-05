from fastapi import FastAPI

from app.routes.jobs import router as jobs_router


app = FastAPI(title="AI Job Matching System")

app.include_router(jobs_router)


@app.get("/")
def root():
    return {"message": "AI Job Matching System API"}
