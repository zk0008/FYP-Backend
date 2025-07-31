import logging

from google import genai

from langchain.chat_models import init_chat_model
from langchain_google_vertexai.chat_models import ChatVertexAI
from langchain_openai.chat_models.base import ChatOpenAI

from openai import OpenAI

from app.dependencies import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)


def safe_init_chat_model(model_name: str, temperature: float = 0) -> ChatOpenAI | ChatVertexAI:
    try:
        return init_chat_model(model_name, temperature=temperature, disable_streaming=True)     # No need for streaming since responses are directly written to DB
    except Exception as e:
        logger.exception(f"Initialization of LLM '{model_name}' with error: {e}")
        return None

# LangChain LLM wrappers
gemini_2_flash_lite = safe_init_chat_model("gemini-2.0-flash-lite")
gemini_25_flash = safe_init_chat_model("gemini-2.5-flash")
gemini_25_pro = safe_init_chat_model("gemini-2.5-pro")

gpt_41_nano = safe_init_chat_model("gpt-4.1-nano")
gpt_41_mini = safe_init_chat_model("gpt-4.1-mini")
gpt_4o_mini = safe_init_chat_model("gpt-4o-mini")

# Direct API clients
google_client = genai.Client(api_key=settings.GEMINI_API_KEY)
openai_client = OpenAI(api_key=settings.OPENAI_API_KEY)
