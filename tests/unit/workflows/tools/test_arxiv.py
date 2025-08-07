import pytest
from unittest.mock import Mock, patch

from app.workflows.tools.arxiv import ArxivSearchTool, ArxivSearchInput


class TestArxivSearchInput:
    def test_valid_input(self):
        """Test valid ArxivSearchInput creation."""
        input_data = ArxivSearchInput(query="machine learning")

        assert input_data.query == "machine learning"


class TestArxivSearchTool:
    @pytest.fixture
    def arxiv_search_tool(self):
        return ArxivSearchTool()


    def test_tool_properties(self, arxiv_search_tool):
        """Test tool properties."""
        assert arxiv_search_tool.name == "arxiv_search"
        assert "search arxiv" in arxiv_search_tool.description.lower()
        assert arxiv_search_tool.args_schema == ArxivSearchInput


    @patch('app.workflows.tools.arxiv.ArxivAPIWrapper')
    def test_run_success(self, mock_arxiv_wrapper, arxiv_search_tool):
        """Test successful arXiv search."""
        # Mock arXiv wrapper
        mock_wrapper = Mock()
        mock_wrapper.run.return_value = "Paper 1: Title\nPaper 2: Another Title"
        mock_arxiv_wrapper.return_value = mock_wrapper
        
        result = arxiv_search_tool._run(query="machine learning")
        
        assert result == "Paper 1: Title\nPaper 2: Another Title"
        mock_wrapper.run.assert_called_once_with("machine learning")


    @patch('app.workflows.tools.arxiv.ArxivAPIWrapper')
    def test_run_exception(self, mock_arxiv_wrapper, arxiv_search_tool):
        """Test arXiv search with exception."""
        # Mock wrapper to raise exception
        mock_wrapper = Mock()
        mock_wrapper.run.side_effect = Exception("API error")
        mock_arxiv_wrapper.return_value = mock_wrapper
        
        result = arxiv_search_tool._run(query="test query")
        
        assert "Error executing arXiv search" in result
        assert "API error" in result


    def test_run_empty_query(self, arxiv_search_tool):
        """Test arXiv search with empty query."""
        with patch('app.workflows.tools.arxiv.ArxivAPIWrapper') as mock_wrapper:
            mock_wrapper.return_value.run.return_value = "No good Arxiv Result was found"
            
            result = arxiv_search_tool._run(query="")
            
            assert isinstance(result, str)
            assert result == "No good Arxiv Result was found"
