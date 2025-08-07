from app.constants import (
    DEFAULT_CHUNK_SIZE,
    DEFAULT_CHUNK_OVERLAP,
    EMBEDDING_MODEL_NAME,
    MAX_FILE_SIZE_MB,
    MAX_WORKERS,
    MIN_USERNAME_LENGTH,
    MAX_USERNAME_LENGTH,
    GEMINI_25_MAX_INPUT_TOKENS
)


class TestConstants:
    def test_embedding_constants(self):
        """Test embedding-related constants."""
        assert DEFAULT_CHUNK_SIZE == 1000
        assert DEFAULT_CHUNK_OVERLAP == 200
        assert EMBEDDING_MODEL_NAME == "text-embedding-ada-002"


    def test_file_constants(self):
        """Test file-related constants."""
        assert MAX_FILE_SIZE_MB == 5
        assert MAX_WORKERS == 5


    def test_username_length_constants(self):
        """Test username length constants."""
        assert MIN_USERNAME_LENGTH == 2
        assert MAX_USERNAME_LENGTH == 20


    def test_gemini_constants(self):
        """Test Gemini-related constants."""
        assert GEMINI_25_MAX_INPUT_TOKENS == 1_048_576


    def test_constants_types(self):
        """Test that constants have correct types."""
        assert isinstance(DEFAULT_CHUNK_SIZE, int)
        assert isinstance(DEFAULT_CHUNK_OVERLAP, int)
        assert isinstance(EMBEDDING_MODEL_NAME, str)
        assert isinstance(MAX_FILE_SIZE_MB, (int, float))
        assert isinstance(MAX_WORKERS, int)
        assert isinstance(MIN_USERNAME_LENGTH, int)
        assert isinstance(MAX_USERNAME_LENGTH, int)
