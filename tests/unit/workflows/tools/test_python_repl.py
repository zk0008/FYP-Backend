import pytest
from unittest.mock import Mock, patch

from app.workflows.tools.python_repl import PythonREPLTool, PythonREPLInput


class TestPythonREPLInput:
    def test_valid_input(self):
        """Test valid PythonREPLInput creation."""
        input_data = PythonREPLInput(code="print('Hello, World!')")
        
        assert input_data.code == "print('Hello, World!')"

    def test_empty_code(self):
        """Test input with empty code."""
        input_data = PythonREPLInput(code="")
        
        assert input_data.code == ""


class TestPythonREPLTool:
    @pytest.fixture
    def python_repl_tool(self):
        return PythonREPLTool()


    def test_tool_properties(self, python_repl_tool):
        """Test tool properties."""
        assert python_repl_tool.name == "python_repl"
        assert "execute python code" in python_repl_tool.description.lower()
        assert python_repl_tool.args_schema == PythonREPLInput


    @patch('app.workflows.tools.python_repl.PythonREPL')
    def test_run_success(self, mock_python_repl, python_repl_tool):
        """Test successful code execution."""
        # Mock REPL
        mock_repl = Mock()
        mock_repl.run.return_value = "Hello, World!"
        mock_python_repl.return_value = mock_repl

        result = python_repl_tool._run(code="print('Hello, World!')")

        assert result == "Hello, World!"
        mock_repl.run.assert_called_once_with("print('Hello, World!')")


    @patch('app.workflows.tools.python_repl.PythonREPL')
    def test_run_exception(self, mock_python_repl, python_repl_tool):
        """Test code execution with exception."""
        # Mock REPL to raise exception
        mock_repl = Mock()
        mock_repl.run.side_effect = Exception("Syntax error")
        mock_python_repl.return_value = mock_repl

        result = python_repl_tool._run(code="invalid code")

        assert "Error executing Python code" in result
        assert "Syntax error" in result

    @patch('app.workflows.tools.python_repl.PythonREPL')
    def test_run_empty_result(self, mock_python_repl, python_repl_tool):
        """Test code execution with empty result."""
        mock_repl = Mock()
        mock_repl.run.return_value = ""
        mock_python_repl.return_value = mock_repl

        result = python_repl_tool._run(code="x = 5")

        assert result == ""
