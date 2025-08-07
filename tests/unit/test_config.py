from app.config import Settings


class TestSettings:
    def test_settings_initialization(self):
        """
        Given environment variables to be set
        When the Settings class is initialized
        Then all required settings are correctly loaded
        """
        settings = Settings(
            SUPABASE_URL="http://test.supabase.co",
            SUPABASE_SERVICE_ROLE_KEY="test_key",
            SUPABASE_JWT_SECRET_KEY="test_jwt",
            GROUPGPT_USER_ID="test_id",
            ANTHROPIC_API_KEY="test_anthropic",
            GEMINI_API_KEY="test_gemini",
            OPENAI_API_KEY="test_openai",
            LANGSMITH_TRACING=False,
            LANGSMITH_ENDPOINT="http://test.langsmith.com",
            LANGSMITH_API_KEY="test_langsmith",
            LANGSMITH_PROJECT="test_project",
            GOOGLE_API_KEY="test_google",
            GOOGLE_CSE_ID="test_cse"
        )

        # Default values
        assert settings.title == "GroupGPT API"
        assert settings.summary == "API calls for the GroupGPT application"
        assert "GroupGPT API" in settings.description

        # Environment variables
        assert settings.SUPABASE_URL == "http://test.supabase.co"
        assert settings.SUPABASE_SERVICE_ROLE_KEY == "test_key"
        assert settings.SUPABASE_JWT_SECRET_KEY == "test_jwt"
        assert settings.GROUPGPT_USER_ID == "test_id"
        assert settings.ANTHROPIC_API_KEY == "test_anthropic"
        assert settings.GEMINI_API_KEY == "test_gemini"
        assert settings.OPENAI_API_KEY == "test_openai"
        assert settings.LANGSMITH_ENDPOINT == "http://test.langsmith.com"
        assert settings.LANGSMITH_TRACING is False
        assert settings.LANGSMITH_ENDPOINT == "http://test.langsmith.com"
        assert settings.LANGSMITH_API_KEY == "test_langsmith"
        assert settings.LANGSMITH_PROJECT == "test_project"
        assert settings.GOOGLE_API_KEY == "test_google"
        assert settings.GOOGLE_CSE_ID == "test_cse"
