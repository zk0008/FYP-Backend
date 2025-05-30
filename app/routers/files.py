import logging
from os.path import splitext
from pathlib import Path
import shutil
from uuid import uuid4

from fastapi import (
    APIRouter,
    BackgroundTasks,
    File,
    Form,
    status,
    UploadFile
)
from fastapi.responses import JSONResponse

from app.pipelines.image_pipeline import ImagePipeline
from app.pipelines.pdf_pipeline import PdfPipeline

router = APIRouter(
    prefix='/api/files',
    tags=['files'],
)

logger = logging.getLogger(__name__)

# Create tmp_files directory
PROJECT_ROOT = Path(__file__).resolve().parents[2]
TMP_FILES_DIR = PROJECT_ROOT / "tmp_files"
TMP_FILES_DIR.mkdir(exist_ok=True)
logger.info("Successfully created tmp_files directory")


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
            content={"error": f"Exceeded {MAX_FILE_SIZE_MB} MB limit. Uploaded file size: {file_size_mb:.2f} MB"}
        )

    original_filename = uploaded_file.filename
    ext = splitext(original_filename)[1].lower()
    document_id = uuid4()       # Generate random UUID v4 for document's DB entry

    # Save a copy of uploaded file to disk
    tmp_filename = f"{document_id.hex}{ext}"
    tmp_filepath = TMP_FILES_DIR / tmp_filename
    with open(tmp_filepath, "wb") as buffer:
        shutil.copyfileobj(uploaded_file.file, buffer)

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

    bg_tasks.add_task(
        pipeline.handle_file,
        document_id=str(document_id),
        filename=original_filename,
        path=tmp_filepath
    )

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "message": "File uploaded. Processing started.",
            "document_id": str(document_id)
        }
    )
