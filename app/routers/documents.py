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
    HTTPException,
    Request,
    status,
    UploadFile
)
from fastapi.responses import JSONResponse

from app.constants import MAX_FILE_SIZE_MB
from app.dependencies import get_supabase
from app.pipelines import ImagePipeline, PdfPipeline

router = APIRouter(
    prefix="/api/documents",
    tags=["documents"],
)

logger = logging.getLogger(__name__)

# Create tmp_files directory
PROJECT_ROOT = Path(__file__).resolve().parents[2]
TMP_FILES_DIR = PROJECT_ROOT / "tmp_files"
TMP_FILES_DIR.mkdir(exist_ok=True)
logger.info("Successfully created tmp_files directory")


@router.post("")
async def upload_document(
    request: Request,
    uploaded_document: UploadFile = File(...),
    chatroom_id: str = Form(...),
    bg_tasks: BackgroundTasks = BackgroundTasks()
) -> JSONResponse:
    """Uploads a document to the specified chatroom."""
    file_size_mb = uploaded_document.size / 1_000_000

    if file_size_mb > MAX_FILE_SIZE_MB:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Exceeded {MAX_FILE_SIZE_MB} MB limit. Uploaded file size: {file_size_mb:.2f} MB"
        )

    original_filename = uploaded_document.filename
    ext = splitext(original_filename)[1].lower()
    document_id = uuid4()  # Generate a random UUID v4 for document DB entry

    # Save a copy of uploaded file to disk
    tmp_filename = f"{document_id.hex}{ext}"
    tmp_filepath = TMP_FILES_DIR / tmp_filename
    with open(tmp_filepath, "wb") as buffer:
        shutil.copyfileobj(uploaded_document.file, buffer)

    if ext in {".pdf"}:
        pipeline = PdfPipeline(uploader_id=request.state.user_id, chatroom_id=chatroom_id)
    elif ext in {".jpg", ".jpeg", ".png"}:
        pipeline = ImagePipeline(uploader_id=request.state.user_id, chatroom_id=chatroom_id)
    elif ext in {".mp3"}:
        # TODO: Audio pipeline
        pass
    elif ext in {".txt", ".md"}:
        # TODO: Text pipeline
        pass
    elif ext in {".csv", ".xls", ".xlsx"}:
        # TODO: Spreadsheet pipeline
        pass
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type: {ext}"
        )

    logger.debug(f"POST - {router.prefix}\nReceived file: {original_filename} with ID: {document_id}")

    bg_tasks.add_task(
        pipeline.handle_document,
        document_id=str(document_id),
        filename=original_filename,
        path=tmp_filepath
    )

    return JSONResponse(
        status_code=status.HTTP_201_CREATED,
        content={
            "message": "Document uploaded. Processing started.",
            "document_id": str(document_id)
        }
    )

@router.get("")
async def get_documents(chatroom_id: str) -> JSONResponse:
    """Retrieves all documents for a specific chatroom."""
    try:
        supabase = get_supabase()

        response = supabase.rpc("get_chatroom_documents", {"p_chatroom_id": chatroom_id}).execute()

        if response.data is None:
            response.data = []

        logger.debug(f"GET - {router.prefix}\nRetrieved {len(response.data)} document{'s' if len(response.data) != 1 else ''}")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=response.data
        )
    except Exception as e:
        logger.error(f"GET - {router.prefix}\nError: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=e.detail if hasattr(e, 'detail') else str(e)
        )

@router.delete("/{document_id}")
async def delete_document(document_id: str) -> JSONResponse:
    """Deletes a document (both the DB entry and the raw file)."""
    try:
        supabase = get_supabase()

        # Delete document entry in DB
        document_response = (
            supabase.table("documents")
            .delete()
            .eq("document_id", document_id)
            .execute()
        )

        # Delete raw document file from storage
        (
            supabase.storage
            .from_("knowledge-bases")
            .remove([f"{document_response.data[0]['chatroom_id']}/{document_id}"])
        )

        logger.debug(f"DELETE - {router.prefix}/{document_id}\nDeleted document")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "message": "Document deleted",
                "document_id": document_id
            }
        )
    except Exception as e:
        logger.error(f"DELETE - {router.prefix}/{document_id}\nError: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=e.detail if hasattr(e, 'detail') else str(e)
        )
