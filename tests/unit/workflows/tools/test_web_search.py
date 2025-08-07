import pytest
from unittest.mock import Mock, patch

from app.workflows.tools.web_search import WebSearchTool, WebSearchInput


class TestWebSearchInput:
    def test_valid_input(self):
        """Test valid WebSearchInput creation."""
        input_data = WebSearchInput(query="test query", num_results=3)
        
        assert input_data.query == "test query"
        assert input_data.num_results == 3

    def test_default_num_results(self):
        """Test default num_results value."""
        input_data = WebSearchInput(query="test query")
        
        assert input_data.query == "test query"
        assert input_data.num_results == 5


class TestWebSearchTool:
    @pytest.fixture
    def web_search_tool(self):
        return WebSearchTool()


    def test_tool_properties(self, web_search_tool):
        """Test tool properties."""
        assert web_search_tool.name == "web_search"
        assert "search the web" in web_search_tool.description.lower()
        assert web_search_tool.args_schema == WebSearchInput


    @patch('app.workflows.tools.web_search.GoogleSearchAPIWrapper')
    @patch('app.workflows.tools.web_search.get_settings')
    def test_successful_web_search(self, mock_get_settings, mock_google_search, web_search_tool):
        """Test successful web search."""
        # Mock settings
        mock_settings = Mock()
        mock_settings.GOOGLE_API_KEY = "test_api_key"
        mock_settings.GOOGLE_CSE_ID = "test_cse_id"
        mock_get_settings.return_value = mock_settings

        # Mock search results
        mock_search = Mock()
        mock_search.results.return_value = [
            {
                "title": "Test Title 1",
                "link": "https://example.com/1",
                "snippet": "Test snippet 1"
            },
            {
                "title": "Test Title 2", 
                "link": "https://example.com/2",
                "snippet": "Test snippet 2"
            }
        ]
        mock_google_search.return_value = mock_search

        result = web_search_tool._run(query="test query", num_results=2)

        assert isinstance(result, str)
        assert "Test Title 1" in result
        assert "https://example.com/1" in result
        assert "Test snippet 1" in result


    @patch('app.workflows.tools.web_search.GoogleSearchAPIWrapper')
    @patch('app.workflows.tools.web_search.get_settings')
    def test_web_search_exception(self, mock_get_settings, mock_google_search, web_search_tool):
        """Test web search with exception."""
        mock_settings = Mock()
        mock_get_settings.return_value = mock_settings
        
        mock_search = Mock()
        mock_search.results.side_effect = Exception("API error")
        mock_google_search.return_value = mock_search
        
        result = web_search_tool._run(query="test query")
        
        assert "Error executing web search" in result


    @patch('app.workflows.tools.web_search.GoogleSearchAPIWrapper')
    @patch('app.workflows.tools.web_search.get_settings')
    def test_web_search_empty_query(self, mock_get_settings, mock_google_search, web_search_tool):
        """Test web search with empty query."""
        mock_settings = Mock()
        mock_get_settings.return_value = mock_settings

        mock_search = Mock()
        mock_search.results.return_value = []
        mock_google_search.return_value = mock_search

        result = web_search_tool._run(query="", num_results=5)

        assert isinstance(result, str)
        assert result == "No results found."


    @patch('app.workflows.tools.web_search.GoogleSearchAPIWrapper')
    @patch('app.workflows.tools.web_search.get_settings')
    def test_web_search_no_results(self, mock_get_settings, mock_google_search, web_search_tool):
        """Test web search with no results."""
        mock_settings = Mock()
        mock_get_settings.return_value = mock_settings
        
        mock_search = Mock()
        mock_search.results.return_value = []
        mock_google_search.return_value = mock_search
        
        result = web_search_tool._run(query="test query")
        
        assert isinstance(result, str)
        assert result == "No results found."
