import pytest
from unittest.mock import Mock, patch, AsyncMock

from app.workflows.graph import GroupGPTGraph

pytest_plugins = ('pytest_asyncio')


class TestGroupGPTGraph:
    @pytest.fixture
    def mock_supabase(self):
        return Mock()


    @pytest.fixture
    def mock_llm(self):
        return Mock()


    @pytest.fixture
    @patch('app.workflows.graph.get_supabase')
    @patch('app.workflows.graph.gemini_25_flash')
    def graph(self, mock_get_supabase, mock_supabase):
        mock_get_supabase.return_value = mock_supabase
        return GroupGPTGraph()


    @patch('app.workflows.graph.get_supabase')
    def test_initialization(self, mock_get_supabase):
        """Test GroupGPTGraph initialization."""
        mock_supabase = Mock()
        mock_get_supabase.return_value = mock_supabase

        graph = GroupGPTGraph()

        assert graph.supabase == mock_supabase
        assert graph.history_fetcher is not None
        assert graph.response_generator is not None
        assert graph.graph is not None
        assert graph.logger is not None


    @pytest.mark.asyncio
    async def test_process_query_success(self, graph):
        """Test successful query processing."""
        graph.graph.ainvoke = AsyncMock(return_value={
            "final_response": "I'm doing well, thank you!"
        })

        result = await graph.process_query(
            username="test_user",
            chatroom_id="test_chatroom_id",
            content="Hello, how are you?"
        )

        assert result == "I'm doing well, thank you!"
        graph.graph.ainvoke.assert_called_once()


    @pytest.mark.asyncio
    async def test_process_query_initial_state(self, graph):
        """Test that initial state is properly constructed."""
        graph.graph.ainvoke = AsyncMock(return_value={"final_response": "Response"})

        await graph.process_query(
            username="alice",
            chatroom_id="test_chatroom_id",
            content="What's the weather like?"
        )

        # Verify the initial state passed to graph
        call_args = graph.graph.ainvoke.call_args[0][0]
        assert call_args["username"] == "alice"
        assert call_args["chatroom_id"] == "test_chatroom_id"
        assert call_args["query"] == "What's the weather like?"
        assert call_args["chat_history"] == []


    @pytest.mark.asyncio
    async def test_process_query_exception(self, graph):
        """Test query processing with exception."""
        graph.graph.ainvoke = AsyncMock(side_effect=Exception("Graph execution failed"))

        with pytest.raises(Exception, match="Graph execution failed"):
            await graph.process_query(
                username="test_user",
                chatroom_id="test_chatroom_id",
                content="Test query"
            )


    @pytest.mark.asyncio
    async def test_process_query_missing_final_response(self, graph):
        """Test handling when final_response is missing from state."""
        # Return state without final_response
        graph.graph.ainvoke = AsyncMock(return_value={
            "username": "test_user",
            "chatroom_id": "test_chatroom_id"
        })

        with pytest.raises(KeyError):
            await graph.process_query(
                username="test_user",
                chatroom_id="test_chatroom_id",
                content="Test query"
            )


    def test_graph_nodes_initialization(self, graph):
        """Test that graph nodes are properly initialized."""
        assert hasattr(graph, 'history_fetcher')
        assert hasattr(graph, 'response_generator')

        # Verify nodes have required attributes
        assert hasattr(graph.history_fetcher, 'supabase')
        assert hasattr(graph.response_generator, 'supabase')
        assert hasattr(graph.response_generator, 'llm')
