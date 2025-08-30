import base64
import logging
from typing import List, Optional

from fastapi import (
    APIRouter,
    File,
    Form,
    status,
    UploadFile
)
from fastapi.responses import JSONResponse

from app.workflows.graph import GroupGPTGraph

router = APIRouter(
    prefix="/api/queries",
    tags=["queries"],
)

logger = logging.getLogger(__name__)


@router.post("/groupgpt")
async def invoke_groupgpt(
    username: str = Form(...),
    chatroom_id: str = Form(...),
    content: str = Form(...),
    files: Optional[List[UploadFile]] = File(None)
):
    try:
        logger.info(
            "POST - {router.prefix}/groupgpt\nReceived GroupGPT request with the following parameters:\n" +
            f"User: {username}\n" +
            f"Chatroom: {chatroom_id}\n" +
            f"Content: {content[:50]}{'...' if len(content) > 50 else ''}\n" +
            f"Files: {len(files) if files else 0} file(s)"
        )

        files_data = []
        if files:
            for file in files:
                file_content = await file.read()
                base64_content = base64.b64encode(file_content).decode("utf-8")
                # Expected format by Gemini models
                files_data.append({
                    "type": "media",
                    "source_type": "base64",
                    "mime_type": file.content_type,
                    "data": base64_content
                })

        graph = GroupGPTGraph()
        response = await graph.process_query(
            username=username,
            chatroom_id=chatroom_id,
            content=content,
            files_data=files_data
        )

        logger.info(f"POST - {router.prefix}/groupgpt\nResponse: {response[:50]}{'...' if len(response) > 50 else ''}")

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
