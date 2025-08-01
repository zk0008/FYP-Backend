import logging

from langchain_core.tools import BaseTool
from langchain_experimental.utilities import PythonREPL
from pydantic import BaseModel, Field


class PythonREPLInput(BaseModel):
    """
    Input schema for Python REPL tool.
    """
    code: str = Field(..., description="The Python code to execute. Input must be a valid Python command. Use the `print()` function to see the output of a value.")


class PythonREPLTool(BaseTool):
    """
    Tool for executing Python code in a REPL environment.
    """

    name: str = "python_repl"
    description: str = "Execute Python code in a REPL environment. Use this when you need to run Python code to compute values or perform calculations."
    args_schema: type[BaseModel] = PythonREPLInput

    def _run(self, code: str) -> str:
        """Execute the provided Python code and return the output."""
        logger = logging.getLogger(self.__class__.__name__)
        repl = PythonREPL()

        try:
            result = repl.run(code)

            logger.debug(f"Executed Python code: {code}")
            logger.debug(f"Python REPL result: {result}")

            return result
        except Exception as e:
            logger.exception(f"Error executing Python code: {e}")
            return f"Error executing Python code: {str(e)}"
