import logging
from typing import Any, Dict, List

from langchain_core.tools import BaseTool
from langchain_google_community.search import GoogleSearchAPIWrapper
from pydantic import BaseModel, Field

from app.dependencies import get_settings


class WebSearchInput(BaseModel):
    """
    Input schema for web search tool.
    """
    query: str = Field(..., description="The search query to perform on the web.")
    num_results: int = Field(default=5, description="Number of search results to return. Default is 5. Adjust based on the query complexity and expected results.")


class WebSearchTool(BaseTool):
    """
    Tool for searching the web using Google Search API.
    """
    name: str = "web_search"
    description: str = "Search the web for current information on any topic. Use this when you need up-to-date information that might not be in the provided context or when the user asks about recent events, news, or current information."
    args_schema: type[BaseModel] = WebSearchInput


    def _run(self, query: str, num_results: int = 5) -> List[Dict[str, Any]]:
        """Search the web and return the results."""
        settings = get_settings()
        search = GoogleSearchAPIWrapper(
            google_api_key=settings.GOOGLE_API_KEY,
            google_cse_id=settings.GOOGLE_CSE_ID,
        )
        logger = logging.getLogger(self.__class__.__name__)

        try:
            web_results = search.results(query, num_results)
            web_results_text = "\n\n".join([
                f"Title: {result['title']}\nLink: {result['link']}\nSnippet: {result['snippet']}"
                for result in web_results
            ])

            logger.debug(f"Web search executed with the following parameters:\n"
                         f"Query: {query}\n"
                         f"Number of Results: {num_results}")
            logger.debug(f"Web search results:\n{web_results_text}")

            return web_results_text
        except Exception as e:
            logger.exception(f"Error executing web search: {e}")
            return f"Error executing web search: {str(e)}"
