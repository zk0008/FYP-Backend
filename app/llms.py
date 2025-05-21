import logging

from langchain.chat_models import init_chat_model
from langchain_openai.chat_models.base import ChatOpenAI
from langchain_google_vertexai.chat_models import ChatVertexAI

logger = logging.getLogger(__name__)


def safe_init_chat_model(model_name: str, temperature: float = 0) -> ChatOpenAI | ChatVertexAI:
    try:
        return init_chat_model(model_name, temperature=temperature)
    except Exception as e:
        logger.exception(f"Initialization of LLM '{model_name}' with error: {e}")
        return None

gemini_2_flash_lite = safe_init_chat_model("gemini-2.0-flash-lite")
gpt_41_nano = safe_init_chat_model("gpt-4.1-nano")
