import pytest
from unittest.mock import Mock
from fastapi.testclient import TestClient
from langchain_core.messages import AIMessage, HumanMessage

from app.main import app
from app.config import Settings


@pytest.fixture
def mock_settings():
    """Mock settings for testing."""
    return Settings(
        SUPABASE_URL="http://test.supabase.co",
        SUPABASE_SERVICE_ROLE_KEY="test_service_key",
        SUPABASE_JWT_SECRET_KEY="test_jwt_secret",
        GROUPGPT_USER_ID="test_groupgpt_id",
        ANTHROPIC_API_KEY="test_anthropic_key",
        GEMINI_API_KEY="test_gemini_key",
        OPENAI_API_KEY="test_openai_key",
        LANGSMITH_TRACING=False,
        LANGSMITH_ENDPOINT="http://test.langsmith.com",
        LANGSMITH_API_KEY="test_langsmith_key",
        LANGSMITH_PROJECT="test_project",
        GOOGLE_API_KEY="test_google_key",
        GOOGLE_CSE_ID="test_cse_id"
    )


@pytest.fixture
def mock_supabase():
    """Mock Supabase client."""
    mock = Mock()
    mock.table.return_value = mock
    mock.insert.return_value = mock
    mock.execute.return_value = Mock(data=[])
    mock.rpc.return_value = mock
    return mock


@pytest.fixture
def mock_llm():
    """Mock LLM for testing."""
    mock = Mock()
    mock.invoke.return_value = AIMessage(content="Test response")
    mock.bind_tools.return_value = mock
    return mock


@pytest.fixture
def client():
    """Test client for FastAPI app."""
    return TestClient(app)


@pytest.fixture
def sample_chat_state():
    """Sample ChatState for testing."""
    return {
        "username": "test_username",
        "chatroom_id": "test_chatroom_id",
        "query": "test query",
        "chat_history": [
            HumanMessage(content="Hello"),
            AIMessage(content="Hi there!")
        ],
        "document_chunks": [
            {
                "filename": "test.pdf",
                "content": "Test content",
                "rrf_score": 0.8
            }
        ],
        "final_response": ""
    }
