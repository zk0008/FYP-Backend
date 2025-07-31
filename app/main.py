from contextlib import asynccontextmanager
import logging
import os

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware

load_dotenv()       # Load environment variables before all other imports

from app.dependencies import get_settings
from app.logger import setup_logging
from app.middlewares import auth_middleware
from app.routers import files, legacy, queries
from app.workflows import GroupGPTGraph

settings = get_settings()

setup_logging()
logger = logging.getLogger(__name__)
os.makedirs("static", exist_ok=True)  # Ensure static directory exists

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup tasks
    logger.info("Starting application...")
    try:
        compiled_graph = GroupGPTGraph().graph
        graph_repr = compiled_graph.get_graph()
        graph_image = graph_repr.draw_mermaid_png()

        with open("static/graph.png", "wb") as f:
            f.write(graph_image)

        logger.info("GroupGPT graph visualization saved to static/graph.png")
    except Exception as e:
        print(f"Failed to generate GroupGPT graph visualization: {e}")

    yield

    # Shutdown tasks
    logger.info("Shutting down application...")
    pass

app = FastAPI(
    title=settings.title,
    summary=settings.summary,
    description=settings.description,
    lifespan=lifespan
)
logger.info("Successfully started application")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)
app.add_middleware(BaseHTTPMiddleware, dispatch=auth_middleware)

app.include_router(files.router)
app.include_router(legacy.router)
app.include_router(queries.router)

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def root():
    return {"message": "Server is running"}
