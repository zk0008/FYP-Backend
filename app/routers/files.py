from io import BytesIO
from time import sleep
from typing import Annotated

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    File,
    Form,
    HTTPException,
    Response,
    status,
    UploadFile
)

from app.pipelines.image_pipeline import ImagePipeline


router = APIRouter(
    prefix='/api/files',
    tags=['files'],
)


@router.post('/upload')
async def upload_file(
    uploaded_file: UploadFile = File(...),
    uploader_id: str = Form(...),
    chatroom_id: str = Form(...),
    bg_tasks: BackgroundTasks = BackgroundTasks()
):
    pipeline = ImagePipeline(uploader_id=uploader_id, chatroom_id=chatroom_id)

    pipeline.handle_file(uploaded_file)                         # Synchronous
    # bg_tasks.add_task(pipeline.handle_file, uploaded_file)      # TODO: Asynchronous, but not working

    return {"message": "File uploaded. Processing started."}

# @router.post('/delete')
