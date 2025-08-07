import pytest
from unittest.mock import Mock, patch
from datetime import datetime

from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, ToolMessage

from app.workflows.nodes.response_generator import ResponseGenerator


class TestResponseGenerator:
    @pytest.fixture
    def mock_supabase(self):
        mock = Mock()
        mock.table.return_value = mock
        mock.insert.return_value = mock
        mock.execute.return_value = Mock(data=[{"id": "test_id"}])
        return mock


    @pytest.fixture
    def mock_llm(self):
        mock = Mock()
        mock.bind_tools.return_value = mock
        mock.invoke.return_value = AIMessage(content="Test response")
        return mock


    @pytest.fixture
    def response_generator(self, mock_supabase, mock_llm):
        return ResponseGenerator(supabase=mock_supabase, llm=mock_llm)


    def test_initialization(self, mock_supabase, mock_llm):
        """Test ResponseGenerator initialization."""
        generator = ResponseGenerator(supabase=mock_supabase, llm=mock_llm)

        assert generator.supabase == mock_supabase
        assert generator.llm == mock_llm
        assert generator.logger is not None
        assert isinstance(generator.system_message, SystemMessage)
        assert generator.MAX_TOOL_CALLS == 10


    def test_system_message_content(self, response_generator):
        """Test that system message contains required instructions."""
        content = response_generator.system_message.content

        assert "GroupGPT" in content
        assert "citation" in content.lower()
        assert "tool" in content.lower()
        assert datetime.now().strftime("%A") in content  # Current day should be in message


    @patch('app.workflows.nodes.response_generator.get_settings')
    def test_insert_response_success(self, mock_get_settings, response_generator):
        """Test successful response insertion."""
        mock_settings = Mock()
        mock_settings.GROUPGPT_USER_ID = "groupgpt_id"
        mock_get_settings.return_value = mock_settings

        result = response_generator._insert_response("chatroom_123", "Test content")

        response_generator.supabase.table.assert_called_once_with("messages")
        response_generator.supabase.insert.assert_called_once_with({
            "sender_id": "groupgpt_id",
            "chatroom_id": "chatroom_123",
            "content": "Test content"
        })


    @patch('app.workflows.nodes.response_generator.get_settings')
    def test_insert_response_exception(self, mock_get_settings, response_generator):
        """Test response insertion with exception."""
        mock_get_settings.return_value = Mock(GROUPGPT_USER_ID="groupgpt_id")
        response_generator.supabase.table.side_effect = Exception("Database error")

        # Should not raise exception, just log it
        result = response_generator._insert_response("chatroom_123", "Test content")
        assert result is None


    def test_execute_tool_calls_web_search(self, response_generator):
        """Test web search tool execution."""
        tool_call = {
            'id': 'tool_123',
            'name': 'web_search',
            'args': {'query': 'test query', 'num_results': 3}
        }
        
        response_generator.web_search_tool._run = Mock(return_value="Search results")

        result = response_generator._execute_tool_calls(tool_call, "chatroom_123")

        assert isinstance(result, ToolMessage)
        assert result.content == "Search results"
        assert result.tool_call_id == "tool_123"
        response_generator.web_search_tool._run.assert_called_once_with(
            query="test query", num_results=3
        )


    def test_execute_tool_calls_python_repl(self, response_generator):
        """Test Python REPL tool execution."""
        tool_call = {
            'id': 'tool_456',
            'name': 'python_repl',
            'args': {'code': 'print(2 + 2)'}
        }

        response_generator.python_repl_tool._run = Mock(return_value="4")

        result = response_generator._execute_tool_calls(tool_call, "chatroom_123")

        assert isinstance(result, ToolMessage)
        assert result.content == "4"
        assert result.tool_call_id == "tool_456"
        response_generator.python_repl_tool._run.assert_called_once_with(code="print(2 + 2)")


    def test_execute_tool_calls_arxiv_search(self, response_generator):
        """Test arXiv search tool execution."""
        tool_call = {
            'id': 'tool_789',
            'name': 'arxiv_search',
            'args': {'query': 'machine learning'}
        }

        response_generator.arxiv_search_tool._run = Mock(return_value="arXiv results")

        result = response_generator._execute_tool_calls(tool_call, "chatroom_123")

        assert isinstance(result, ToolMessage)
        assert result.content == "arXiv results"
        assert result.tool_call_id == "tool_789"
        response_generator.arxiv_search_tool._run.assert_called_once_with(query="machine learning")


    def test_execute_tool_calls_chunk_retriever(self, response_generator):
        """Test chunk retriever tool execution."""
        tool_call = {
            'id': 'tool_101',
            'name': 'chunk_retriever',
            'args': {'query': 'test query', 'num_chunks': 3}
        }

        response_generator.chunk_retriever_tool._run = Mock(return_value="Retrieved chunks")

        result = response_generator._execute_tool_calls(tool_call, "chatroom_123")

        assert isinstance(result, ToolMessage)
        assert result.content == "Retrieved chunks"
        assert result.tool_call_id == "tool_101"
        response_generator.chunk_retriever_tool._run.assert_called_once_with(
            chatroom_id="chatroom_123", query="test query", num_chunks=3
        )


    def test_execute_tool_calls_unknown_tool(self, response_generator):
        """Test execution of unknown tool."""
        tool_call = {
            'id': 'tool_unknown',
            'name': 'unknown_tool',
            'args': {}
        }

        result = response_generator._execute_tool_calls(tool_call, "chatroom_123")

        assert isinstance(result, ToolMessage)
        assert "Unknown tool call: unknown_tool" in result.content
        assert result.tool_call_id == "tool_unknown"


    def test_execute_tool_calls_exception(self, response_generator):
        """Test tool execution with exception."""
        tool_call = {
            'id': 'tool_error',
            'name': 'web_search',
            'args': {'query': 'test'}
        }

        response_generator.web_search_tool._run = Mock(side_effect=Exception("Tool error"))

        result = response_generator._execute_tool_calls(tool_call, "chatroom_123")

        assert isinstance(result, ToolMessage)
        assert "Error executing web_search: Tool error" in result.content
        assert result.tool_call_id == "tool_error"


    def test_handle_tool_calls_no_tools(self, response_generator):
        """Test handling messages with no tool calls."""
        messages = [HumanMessage(content="Hello")]
        response_generator.llm.invoke.return_value = AIMessage(content="Hi there!")

        result_messages, final_response = response_generator._handle_tool_calls(messages, "chatroom_123")

        assert len(result_messages) == 2  # Original + response
        assert isinstance(final_response, AIMessage)
        assert final_response.content == "Hi there!"


    def test_handle_tool_calls_with_tools(self, response_generator):
        """Test handling messages with tool calls."""
        messages = [HumanMessage(content="Search for something")]

        # Mock tool call response
        tool_call_response = AIMessage(
            content="I'll search for that",
            tool_calls=[{
                'id': 'tool_123',
                'name': 'web_search',
                'args': {'query': 'test'}
            }]
        )

        final_response = AIMessage(content="Here are the results")


        response_generator.llm.invoke.side_effect = [tool_call_response, final_response]
        response_generator.web_search_tool._run = Mock(return_value="Search results")

        result_messages, final_response_actual = response_generator._handle_tool_calls(messages, "chatroom_123")

        assert len(result_messages) == 4  # Original + tool response + tool message + final response
        assert final_response_actual.content == "Here are the results"

    def test_handle_tool_calls_max_iterations(self, response_generator):
        """Test tool calls reaching maximum iterations."""
        messages = [HumanMessage(content="Test")]

        # Always return tool calls to trigger max iterations
        tool_call_response = AIMessage(
            content="Tool call",
            tool_calls=[{
                'id': 'tool_123',
                'name': 'web_search',
                'args': {'query': 'test'}
            }]
        )

        response_generator.llm.invoke.return_value = tool_call_response
        response_generator.web_search_tool._run = Mock(return_value="Results")

        result_messages, final_response = response_generator._handle_tool_calls(messages, "chatroom_123")

        # Should stop at MAX_TOOL_CALLS
        assert response_generator.llm.invoke.call_count == response_generator.MAX_TOOL_CALLS


    @patch('app.workflows.nodes.response_generator.get_settings')
    def test_call_success(self, mock_get_settings, response_generator):
        """Test successful response generation."""
        mock_get_settings.return_value = Mock(GROUPGPT_USER_ID="groupgpt_id")

        state = {
            "chatroom_id": "chatroom_123",
            "chat_history": [HumanMessage(content="Hello")]
        }

        response_generator.llm.invoke.return_value = AIMessage(content="Hi there!")
        response_generator._handle_tool_calls = Mock(return_value=([], AIMessage(content="Hi there!")))

        result = response_generator(state)

        assert result["final_response"] == "Hi there!"
        response_generator.supabase.table.assert_called_with("messages")


    @patch('app.workflows.nodes.response_generator.get_settings')
    def test_call_removes_groupgpt_prefix(self, mock_get_settings, response_generator):
        """Test that GroupGPT prefix is removed from response."""
        mock_get_settings.return_value = Mock(GROUPGPT_USER_ID="groupgpt_id")

        state = {
            "chatroom_id": "chatroom_123",
            "chat_history": []
        }

        response_generator._handle_tool_calls = Mock(
            return_value=([], AIMessage(content="GroupGPT: Hello there!"))
        )

        result = response_generator(state)

        assert result["final_response"] == "Hello there!"


    @patch('app.workflows.nodes.response_generator.get_settings')
    def test_call_handles_empty_response(self, mock_get_settings, response_generator):
        """Test handling of empty response."""
        mock_get_settings.return_value = Mock(GROUPGPT_USER_ID="groupgpt_id")

        state = {
            "chatroom_id": "chatroom_123",
            "chat_history": []
        }

        response_generator._handle_tool_calls = Mock(return_value=([], AIMessage(content="")))

        result = response_generator(state)

        assert "I apologize" in result["final_response"]
        assert "error" in result["final_response"]


    @patch('app.workflows.nodes.response_generator.get_settings')
    def test_call_exception_handling(self, mock_get_settings, response_generator):
        """Test exception handling in response generation."""
        mock_get_settings.return_value = Mock(GROUPGPT_USER_ID="groupgpt_id")

        state = {
            "chatroom_id": "chatroom_123",
            "chat_history": []
        }

        response_generator._handle_tool_calls = Mock(side_effect=Exception("Generation error"))

        result = response_generator(state)

        assert "I apologize" in result["final_response"]
        assert "error" in result["final_response"]
