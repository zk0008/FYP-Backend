# TODO: Rewrite user queries to be more succinct
import logging

from pydantic import BaseModel, Field
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_google_vertexai.chat_models import ChatVertexAI
from langchain_openai.chat_models.base import ChatOpenAI
from langchain.output_parsers import PydanticOutputParser

from app.workflows.state import ChatState


class QueryRewriterOutput(BaseModel):
    rewritten_query: str = Field(description="Rewritten query that improves on the original unclear query")


class QueryRewriter:
    def __init__(self, llm: ChatOpenAI | ChatVertexAI):
        self.llm = llm
        self.output_parser = PydanticOutputParser(pydantic_object=QueryRewriterOutput)
        self.system_message = SystemMessage(
            content=f"""
                You are a query rewriter. Your task is to improve unclear queries for more accurate processing later on.
                Refer to the following criteria and format instructions to guide your response.

                <criteria>
                If the query is clear and well-written, return it as-is.
                If the query has grammar issues, unclear language, or broken English, rewrite it to make it clear and understandable.
                </criteria>

                <format_instructions>
                You must begin your response with an open curly brace: {{
                {self.output_parser.get_format_instructions()}
                </format_instructions>
            """
        )
        self.logger = logging.getLogger(self.__class__.__name__)
        
    def __call__(self, state: ChatState) -> ChatState:
        original_query = state["original_query"]
        prompt = f"The original query is delimited by backticks as follows: `{original_query}`"

        try:
            response = self.llm.invoke([
                self.system_message,
                HumanMessage(content=prompt)
            ])
            parsed_content = self.output_parser.parse(response.content)
            rewritten_query = parsed_content.rewritten_query
            self.logger.debug("Successfully rewritten query")
        except Exception as e:
            self.logger.exception(e)
            rewritten_query = original_query

        state["rewritten_query"] = rewritten_query
        return state
