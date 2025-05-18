from functools import lru_cache

from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_anthropic import ChatAnthropic
from supabase import create_client, Client

from app.config import Settings


@lru_cache
def get_settings() -> Settings:
    return Settings()


def get_supabase() -> Client:
    settings = get_settings()

    supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY)
    return supabase


def get_graph():
    pass


def get_openai_client():
    settings = get_settings()

    return ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0,
        api_key=settings.OPENAI_API_KEY
    )


def get_anthropic_client():
    settings = get_settings()

    return ChatAnthropic(
        model="claude-3-haiku-20240307",
        temperature=0,
        api_key=settings.ANTHROPIC_API_KEY
    )
