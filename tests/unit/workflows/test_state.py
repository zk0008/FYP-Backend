import pytest
from langchain_core.messages import HumanMessage

from app.workflows.state import ChatState


class TestChatState:
    def test_chat_state_type_hints(self):
        """
        Given a ChatState class
        When checking type annotations
        Then it should have correct type hints for all fields
        """
        annotations = ChatState.__annotations__

        assert 'username' in annotations
        assert 'chatroom_id' in annotations
        assert 'query' in annotations
        assert 'chat_history' in annotations
        assert 'final_response' in annotations


    def test_valid_chat_state_creation(self):
        """
        Given valid data for ChatState
        When creating an instance of ChatState
        Then it should successfully create the instance with correct values
        """
        state = ChatState(
            username="test_username",
            chatroom_id="test_chatroom_id",
            query="test query",
            chat_history=[HumanMessage(content="Hello")],
            final_response="Test response"
        )
        
        assert state["username"] == "test_username"
        assert state["chatroom_id"] == "test_chatroom_id"
        assert state["query"] == "test query"

        assert len(state["chat_history"]) == 1
        assert isinstance(state["chat_history"][0], HumanMessage)
        assert state["chat_history"][0].content == "Hello"

        assert state["final_response"] == "Test response"
