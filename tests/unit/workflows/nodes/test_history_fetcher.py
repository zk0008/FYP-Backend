import pytest
from langchain_core.messages import AIMessage, HumanMessage

from app.workflows.nodes.history_fetcher import HistoryFetcher


class TestHistoryFetcher:
    @pytest.fixture
    def history_fetcher(self, mock_supabase):
        return HistoryFetcher(supabase=mock_supabase)


    def test_initialization(self, mock_supabase):
        """Test HistoryFetcher initialization."""
        fetcher = HistoryFetcher(supabase=mock_supabase)

        assert fetcher.supabase == mock_supabase
        assert fetcher.logger is not None


    def test_fetch_history_success(self, history_fetcher, mock_supabase):
        """
        Given a valid chatroom ID
        When fetching chat history
        Then it should return a list of messages with correct types
        """
        # Mock response data
        mock_supabase.rpc.return_value.execute.return_value.data = [
            {"username": "Alice", "content": "@GroupGPT Hello"},
            {"username": "GroupGPT", "content": "Hi Alice!"},
            {"username": "Bob", "content": "How are you?"}
        ]

        state = {"chatroom_id": "test_chatroom_id"}
        result = history_fetcher(state)

        assert "chat_history" in result
        assert len(result["chat_history"]) == 3
        assert isinstance(result["chat_history"][0], HumanMessage)
        assert result["chat_history"][0].content == "Alice: @GroupGPT Hello"
        assert isinstance(result["chat_history"][1], AIMessage)
        assert result["chat_history"][1].content == "GroupGPT: Hi Alice!"
        assert isinstance(result["chat_history"][2], HumanMessage)
        assert result["chat_history"][2].content == "Bob: How are you?"

        mock_supabase.rpc.assert_called_once_with(
            "get_chatroom_messages", 
            {"p_chatroom_id": "test_chatroom_id"}
        )


    def test_fetch_history_empty_response(self, history_fetcher, mock_supabase):
        """Test history fetching with empty response."""
        mock_supabase.rpc.return_value.execute.return_value.data = []

        state = {"chatroom_id": "test_chatroom_id"}
        result = history_fetcher(state)

        assert result["chat_history"] == []


    def test_fetch_history_exception(self, history_fetcher, mock_supabase):
        """Test history fetching with exception."""
        mock_supabase.rpc.side_effect = Exception("Database error")
        
        state = {"chatroom_id": "test_chatroom_id"}
        result = history_fetcher(state)
        print(result)
        
        # Should handle exception gracefully
        assert "chat_history" in result


    def test_message_grouping(self, history_fetcher, mock_supabase):
        """Test correct grouping of user and GroupGPT messages."""
        mock_supabase.rpc.return_value.execute.return_value.data = [
            {"username": "Alice", "content": "Hello"},
            {"username": "Alice", "content": "@GroupGPT How are you?"},
            {"username": "GroupGPT", "content": "I'm doing well, thanks!"},
            {"username": "Bob", "content": "Great to hear"}
        ]
        
        state = {"chatroom_id": "test_room"}
        result = history_fetcher(state)
        
        chat_history = result["chat_history"]
        assert len(chat_history) == 3

        # First message should combine Alice's messages
        assert isinstance(chat_history[0], HumanMessage)
        assert "Alice: Hello" in chat_history[0].content
        assert "Alice: @GroupGPT How are you?" in chat_history[0].content

        # Second should be GroupGPT's response
        assert isinstance(chat_history[1], AIMessage)
        assert chat_history[1].content == "GroupGPT: I'm doing well, thanks!"

        # Third should be Bob's message
        assert isinstance(chat_history[2], HumanMessage)
        assert chat_history[2].content == "Bob: Great to hear"