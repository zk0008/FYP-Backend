from typing import List

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends
)
from pydantic import BaseModel

# from app.dependencies import get_current_user
from app.models.advanced import get_advanced_answer
from app.models.embed import embed_document
from app.models.gpt import get_answer, Chat
from app.models.pdf import get_pdf_answer
from app.models.rag import get_rag_answer

router = APIRouter(
    prefix='/api/queries',
    tags=['queries'],
)

class APIRequest(BaseModel):
    topic: str
    query: str


class AdvancedRequest(BaseModel):
    chats: list[Chat]
    topic: str
    query: str

# TODO: Streamline flow and retrieve chat history & documents from DB instead of client

@router.post('/gpt35')
async def prompt(chats: List[Chat]):
    print(chats)
    res = get_answer(chats)
    return res


@router.post('/pdf')
async def pdf_prompt(request: APIRequest):
    res = get_pdf_answer(request.topic, request.query)
    return res


@router.post('/rag')
async def rag_prompt(request: APIRequest):
    res = get_rag_answer(request.topic, request.query)
    return res


@router.post('/embed')
async def embed(request: APIRequest, background_tasks: BackgroundTasks):
    background_tasks.add_task(embed_document, request.topic, request.query)
    return {'message': 'Embedding process started.'}


@router.post('/advanced')
async def advanced_prompt(request: AdvancedRequest):
    res = get_advanced_answer(request.chats, request.topic, request.query)
    return res
