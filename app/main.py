import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

from app.dependencies import get_settings
from app.logger import setup_logging
from app.middlewares import auth_middleware
from app.routers import chats, queries, users

settings = get_settings()

setup_logging()
logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.title,
    summary=settings.summary,
    description=settings.description
)
logging.info("Successfully started application")

app.add_middleware(
    CORSMiddleware,
    allow_origins=['http://localhost:3000'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*']
)
app.add_middleware(BaseHTTPMiddleware, dispatch=auth_middleware)

app.include_router(queries.router)
app.include_router(chats.router)
app.include_router(users.router)


@app.get('/')
async def root():
    return {'message': 'Server is running'}
