from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.dependencies import get_settings
from app.routers import auth, queries

settings = get_settings()
app = FastAPI(
    title=settings.title,
    summary=settings.summary,
    description=settings.description
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(queries.router)


@app.get("/")
async def root():
    return {"message": "Server is running"}
