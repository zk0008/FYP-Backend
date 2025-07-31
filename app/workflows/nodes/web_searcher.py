import logging
import re

from langchain_google_community.search import GoogleSearchAPIWrapper

from app.dependencies import get_settings
from app.workflows.state import ChatState


class WebSearcher:
    def __init__(self, num_results: int = 5):
        settings = get_settings()
        self.search = GoogleSearchAPIWrapper(
            google_api_key=settings.GOOGLE_API_KEY,
            google_cse_id=settings.GOOGLE_CSE_ID,
        )
        self.num_results = num_results
        self.logger = logging.getLogger(self.__class__.__name__)

    def __call__(self, state: ChatState) -> dict:
        query_text = re.sub(r"(?i)@GroupGPT", "", state["query"]).strip()       # Remove "@GroupGPT" mention from query

        # TODO: Fix extremely limited search capabilities
        try:
            web_results = self.search.results(query_text, self.num_results)
            self.logger.debug("Successfully retrieved web search results")
        except Exception as e:
            self.logger.exception(e)
            web_results = []

        return {"web_results": web_results}
