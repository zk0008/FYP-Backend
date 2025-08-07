import logging

from fastapi import APIRouter, status
from fastapi.responses import JSONResponse

from app.models import GroupGPTRequest
from app.workflows.graph import GroupGPTGraph

router = APIRouter(
    prefix="/api/queries",
    tags=["queries"],
)

logger = logging.getLogger(__name__)


@router.post("/groupgpt")
async def invoke_groupgpt(request: GroupGPTRequest):
    try:
        logger.info(
            "POST - /groupgpt | Received GroupGPT request with the following parameters:\n" +
            f"User: {request.username}\n" +
            f"Chatroom: {request.chatroom_id}\n" +
            f"Content: {request.content[:50]}{'...' if len(request.content) > 50 else ''}"
        )

        graph = GroupGPTGraph()
        response = await graph.process_query(request)

        logger.info(f"POST - /groupgpt | Response: {response[:50]}{'...' if len(response) > 50 else ''}")

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
