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
    NEXT_PUBLIC_SUPABASE_URL: str
    NEXT_PUBLIC_SUPABASE_ANON_KEY: str
    SUPABASE_JWT_SECRET_KEY: str
    OPENAI_API_KEY: str

    model_config = SettingsConfigDict(env_file="../.env", extra="ignore")
