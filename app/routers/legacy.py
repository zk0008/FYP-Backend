import logging

from fastapi import APIRouter, BackgroundTasks
from pydantic import BaseModel

from app.legacy.advanced import get_advanced_answer
from app.legacy.embed import embed_document
from app.legacy.gpt import get_answer, Chat
from app.legacy.pdf import get_pdf_answer
from app.legacy.rag import get_rag_answer


router = APIRouter(
    prefix='/api/legacy',
    tags=['legacy'],
)

logger = logging.getLogger(__name__)


class APIRequest(BaseModel):
    topic: str
    query: str

class AdvancedRequest(BaseModel):
    chats: list[Chat]
    topic: str
    query: str


@router.post('/advanced')
async def advanced_prompt(request: AdvancedRequest):
    logger.info(
        "POST - /advanced | Received advanced request with the following parameters:\n" + 
        f"Topic: {request.topic}\n" +
        f"Query: {request.query[:50]}{'...' if len(request.query) > 50 else ''}"
    )

    res = get_advanced_answer(request.chats, request.topic, request.query)

    logger.info(f"POST - /advanced | Response: {res[:50]}{'...' if len(res) > 50 else ''}")

    return res


@router.post('/embed')
async def embed(request: APIRequest, bg_tasks: BackgroundTasks):
    logger.info(
        "POST - /embed | Received embedding request with the following parameters:\n" +
        f"Topic: {request.topic}\n" +
        f"Query: {request.query[:50]}{'...' if len(request.query) > 50 else ''}"
    )
    bg_tasks.add_task(embed_document, request.topic, request.query)
    return {"message": "Embedding process started."}


@router.post('/gpt')
async def gpt_prompt(request: APIRequest):
    logger.info(
        "POST - /gpt | Received GPT request with the following parameters:\n" +
        f"Topic: {request.topic}\n" +
        f"Query: {request.query[:50]}{'...' if len(request.query) > 50 else ''}"
    )

    res = get_answer(request.topic, request.query)

    logger.info(f"POST - /gpt | Response: {res[:50]}{'...' if len(res) > 50 else ''}")

    return res


@router.post('/pdf')
async def pdf_prompt(request: APIRequest):
    logger.info(
        "POST - /pdf | Received PDF request with the following parameters:\n" +
        f"Topic: {request.topic}\n" +
        f"Query: {request.query[:50]}{'...' if len(request.query) > 50 else ''}"
    )

    res = get_pdf_answer(request.topic, request.query)

    logger.info(f"POST - /pdf | Response: {res[:50]}{'...' if len(res) > 50 else ''}")

    return res


@router.post('/rag')
async def rag_prompt(request: APIRequest):
    logger.info(
        "POST - /rag | Received RAG request with the following parameters:\n" +
        f"Topic: {request.topic}\n" +
        f"Query: {request.query[:50]}{'...' if len(request.query) > 50 else ''}"
    )

    res = get_rag_answer(request.topic, request.query)

    logger.info(f"POST - /rag | Response: {res[:50]}{'...' if len(res) > 50 else ''}")

    return res
