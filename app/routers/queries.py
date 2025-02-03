from typing import List

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends
)

from app.dependencies import get_current_user
from app.models.advanced import get_advanced_answer
from app.models.embed import embed_document
from app.models.gpt import get_answer, Chat
from app.models.pdf import get_pdf_answer
from app.models.rag import get_rag_answer

router = APIRouter(
    prefix="/api/queries",
    tags=["queries"],
    dependencies=[Depends(get_current_user)]
)

# TODO: Streamline entire flow

@router.post("/gpt35")
async def prompt(chats: List[Chat]):
    res = get_answer(chats)
    return res


@router.post("/pdf")
async def pdf_prompt(topic: str, query: str):
    res = get_pdf_answer(topic, query)
    return res


@router.post("/rag")
async def rag_prompt(topic: str, query: str):
    res = get_rag_answer(topic, query)
    return res


@router.post("/embed")
async def embed(topic: str, query: str, background_tasks: BackgroundTasks):
    background_tasks.add_task(embed_document, topic, query)
    return {"message": "Embedding process started."}


@router.post("/advanced")
async def advanced_prompt(chats: List[Chat], topic: str, query: str):
    res = get_advanced_answer(chats, topic, query)
    return res
