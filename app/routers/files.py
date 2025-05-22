from os.path import splitext

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    File,
    Form,
    HTTPException,
    status,
    UploadFile
)
from fastapi.responses import JSONResponse

from app.dependencies import get_supabase
from app.pipelines.image_pipeline import ImagePipeline
from app.pipelines.pdf_pipeline import PdfPipeline


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
    MAX_FILE_SIZE_MB = 5
    file_size_mb = uploaded_file.size / 1_000_000

    if file_size_mb > MAX_FILE_SIZE_MB:
        return JSONResponse(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            content={"error": f"Exceeded 5 MB limit. Uploaded file size: {file_size_mb:.2f} MB"}
        )

    filename = uploaded_file.filename
    ext = splitext(filename)[1].lower()

    if ext in [".pdf"]:
        pipeline = PdfPipeline(uploader_id=uploader_id, chatroom_id=chatroom_id)
    elif ext in [".jpg", ".jpeg", ".png"]:
        pipeline = ImagePipeline(uploader_id=uploader_id, chatroom_id=chatroom_id)
    elif ext in [".mp3"]:
        # TODO: Audio pipeline
        pass
    else:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"error": f"Unsupported file type: {ext}"}
        )

    pipeline.handle_file(uploaded_file)                         # Synchronous
    # bg_tasks.add_task(pipeline.handle_file, uploaded_file)      # TODO: Asynchronous, but not working

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"message": "File uploaded. Processing started."}
    )
