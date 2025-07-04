from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # App variables
    title: str = "GroupGPT API"
    summary: str = "API calls for the GroupGPT application"
    description: str = """
    # GroupGPT API
    Work in progress
    """

    # Environment variables
    SUPABASE_URL: str
    SUPABASE_SERVICE_ROLE_KEY: str
    SUPABASE_JWT_SECRET_KEY: str

    GROUPGPT_USER_ID: str

    ANTHROPIC_API_KEY: str
    GEMINI_API_KEY: str
    OPENAI_API_KEY: str

    LANGSMITH_TRACING: bool
    LANGSMITH_ENDPOINT: str
    LANGSMITH_API_KEY: str
    LANGSMITH_PROJECT: str

    GOOGLE_API_KEY: str
    GOOGLE_CSE_ID: str

    model_config = SettingsConfigDict(env_file='../.env', extra='ignore')
