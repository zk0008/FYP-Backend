import logging

from langchain_community.utilities import ArxivAPIWrapper
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field


class ArxivSearchInput(BaseModel):
    """
    Input schema for arXiv search tool.
    """
    query: str = Field(..., description="The search query to perform on arXiv. Can include keywords, authors, titles, or arXiv IDs.")


class ArxivSearchTool(BaseTool):
    """
    Tool for searching arXiv papers using the arXiv API.
    """
    name: str = "arxiv_search"
    description: str = "Search arXiv for academic papers related to the query. Use this when you need to find relevant research papers or articles on a specific topic."
    args_schema: type[BaseModel] = ArxivSearchInput

    def _run(self, query: str) -> str:
        """Search arXiv and return the results."""
        logger = logging.getLogger(self.__class__.__name__)
        arxiv_search = ArxivAPIWrapper()

        try:
            results = arxiv_search.run(query)

            logger.debug(f"arXiv search executed for query: {query}")
            logger.debug(f"arXiv search results:\n{results}")

            return results
        except Exception as e:
            logger.exception(f"Error executing arXiv search: {e}")
            return f"Error executing arXiv search: {str(e)}"
