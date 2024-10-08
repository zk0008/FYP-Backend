from fastapi import FastAPI, BackgroundTasks
from models.advanced import get_advanced_answer
from models.pdf import get_pdf_answer
from models.rag import get_rag_answer
from models.gpt import get_answer, Chat
from models.embed import embed_document
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware


app = FastAPI()


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class APIRequest(BaseModel):
    topic: str
    query: str


class AdvancedRequest(BaseModel):
    chats: list[Chat]
    topic: str
    query: str


@app.post("/api/gpt35")
def prompt(chats: list[Chat]):
    res = get_answer(chats)
    return res


@app.post("/api/pdf")
async def pdf_prompt(request: APIRequest):
    res = get_pdf_answer(request.topic, request.query)
    return res


@app.post("/api/rag")
async def rag_prompt(request: APIRequest):
    res = get_rag_answer(request.topic, request.query)
    return res


@app.post("/api/embed")
async def embed(request: APIRequest, background_tasks: BackgroundTasks):
    background_tasks.add_task(embed_document, request.topic, request.query)
    return {"message": "Embedding process started."}


@app.post("/api/advanced")
async def advanced_promp(request: AdvancedRequest):
    res = get_advanced_answer(request.chats, request.topic, request.query)
    return res


# Status Check Endpoint
@app.get("/api/status")
async def status_check():
    return {"status": "OK", "message": "API is running."}
