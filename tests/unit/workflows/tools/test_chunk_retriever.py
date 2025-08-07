import pytest
from unittest.mock import Mock, patch

from app.workflows.tools.chunk_retriever import ChunkRetrieverTool, ChunkRetrieverInput


class TestChunkRetrieverInput:
    def test_valid_input(self):
        """Test valid ChunkRetrieverInput creation."""
        input_data = ChunkRetrieverInput(
            chatroom_id="test_chatroom_id",
            query="test query",
            num_chunks=5
        )

        assert input_data.chatroom_id == "test_chatroom_id"
        assert input_data.query == "test query"
        assert input_data.num_chunks == 5


class TestChunkRetrieverTool:
    @pytest.fixture
    def chunk_retriever_tool(self):
        return ChunkRetrieverTool()

    def test_tool_properties(self, chunk_retriever_tool):
        """Test tool properties."""
        assert chunk_retriever_tool.name == "chunk_retriever"
        assert "retrieve relevant document chunks" in chunk_retriever_tool.description.lower()
        assert chunk_retriever_tool.args_schema == ChunkRetrieverInput


    @patch('app.workflows.tools.chunk_retriever.get_supabase')
    @patch('app.workflows.tools.chunk_retriever.OpenAIEmbeddings')
    def test_run_success(self, mock_embeddings, mock_supabase, chunk_retriever_tool):
        """Test successful chunk retrieval."""
        # Mock embeddings and Supabase
        mock_embedding_model = Mock()
        mock_embedding_model.embed_query.return_value = [0.1, 0.2, 0.3]
        mock_embeddings.return_value = mock_embedding_model

        mock_supabase_instance = Mock()
        mock_supabase_instance.rpc.return_value.execute.return_value.data = [
            {"filename": "doc1.txt", "rrf_score": 0.9, "content": "Content of doc1"},
            {"filename": "doc2.txt", "rrf_score": 0.8, "content": "Content of doc2"}
        ]
        mock_supabase.return_value = mock_supabase_instance

        result = chunk_retriever_tool._run(
            chatroom_id="test_chatroom_id",
            query="test query",
            num_chunks=2
        )

        expected_result = (
            "Filename: doc1.txt\nRRF score: 0.9\nContent: Content of doc1\n\n"
            "Filename: doc2.txt\nRRF score: 0.8\nContent: Content of doc2"
        )
        assert result == expected_result
        mock_embedding_model.embed_query.assert_called_once_with("test query")


    @patch('app.workflows.tools.chunk_retriever.get_supabase')
    @patch('app.workflows.tools.chunk_retriever.OpenAIEmbeddings')
    def test_run_exception(self, mock_embeddings, mock_supabase, chunk_retriever_tool):
        """Test chunk retrieval with exception."""
        # Mock embeddings and Supabase
        mock_embedding_model = Mock()
        mock_embedding_model.embed_query.return_value = [0.1, 0.2, 0.3]
        mock_embeddings.return_value = mock_embedding_model

        mock_supabase_instance = Mock()
        mock_supabase_instance.rpc.return_value.execute.side_effect = Exception("Supabase error")
        mock_supabase.return_value = mock_supabase_instance

        result = chunk_retriever_tool._run(
            chatroom_id="test_chatroom_id",
            query="test query",
            num_chunks=2
        )

        assert "Error retrieving chunks" in result
        assert "Supabase error" in result


    def test_run_empty_query(self, chunk_retriever_tool):
        """Test chunk retrieval with empty query."""
        with patch('app.workflows.tools.chunk_retriever.get_supabase') as mock_supabase:
            mock_supabase_instance = Mock()
            mock_supabase_instance.rpc.return_value.execute.return_value.data = []
            mock_supabase.return_value = mock_supabase_instance

            result = chunk_retriever_tool._run(
                chatroom_id="test_chatroom_id",
                query="",
                num_chunks=5
            )

            assert result == "No relevant document chunks found."
