import logging
from typing import List

from fastapi import (
    APIRouter,
    BackgroundTasks,
    status
)
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.deprecated.advanced import get_advanced_answer
from app.deprecated.embed import embed_document
from app.deprecated.gpt import get_answer, Chat
from app.deprecated.pdf import get_pdf_answer
from app.deprecated.rag import get_rag_answer

from app.models import GroupGPTRequest
from app.workflows.graph import GroupGPTGraph

router = APIRouter(
    prefix="/api/queries",
    tags=["queries"],
)

logger = logging.getLogger(__name__)


class APIRequest(BaseModel):
    topic: str
    query: str

class AdvancedRequest(BaseModel):
    chats: list[Chat]
    topic: str
    query: str


@router.post("/gpt35")
async def prompt(chats: List[Chat]):
    res = get_answer(chats)
    return res


@router.post("/pdf")
async def pdf_prompt(request: APIRequest):
    res = get_pdf_answer(request.topic, request.query)
    return res


@router.post("/rag")
async def rag_prompt(request: APIRequest):
    res = get_rag_answer(request.topic, request.query)
    return res


@router.post("/embed")
async def embed(request: APIRequest, bg_tasks: BackgroundTasks):
    bg_tasks.add_task(embed_document, request.topic, request.query)
    return {"message": "Embedding process started."}


@router.post("/advanced")
async def advanced_prompt(request: AdvancedRequest):
    res = get_advanced_answer(request.chats, request.topic, request.query)
    return res


@router.post("/groupgpt")
async def invoke_groupgpt(request: GroupGPTRequest):
    try:
        graph = GroupGPTGraph()

        response = await graph.process_query(
            username=request.username,
            content=request.content,
            chatroom_id=request.chatroom_id,
            use_rag_query=request.use_rag_query,
            use_web_search=request.use_web_search
        )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"response": response}
        )
    except Exception as e:
        logger.exception(e)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"message": str(e)}
        )
