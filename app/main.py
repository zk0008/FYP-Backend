import logging

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

load_dotenv()       # Load environment variables before all other imports

from app.dependencies import get_settings
from app.logger import setup_logging
from app.middlewares import auth_middleware
from app.routers import files, queries

settings = get_settings()

setup_logging()
logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.title,
    summary=settings.summary,
    description=settings.description
)
logger.info("Successfully started application")

app.add_middleware(
    CORSMiddleware,
    allow_origins=['http://localhost:3000'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*']
)
app.add_middleware(BaseHTTPMiddleware, dispatch=auth_middleware)

app.include_router(files.router)
app.include_router(queries.router)


@app.get('/')
async def root():
    return {'message': 'Server is running'}
