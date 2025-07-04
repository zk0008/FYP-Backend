import logging
from typing import List

from pydantic import BaseModel, Field
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_google_vertexai.chat_models import ChatVertexAI
from langchain_openai.chat_models.base import ChatOpenAI
from langchain.output_parsers import PydanticOutputParser

from app.workflows.state import ChatState


class ChunkSummary(BaseModel):
    filename: str = Field(description="Name of file where chunks were retrieved from")
    rrf_score: float = Field(description="RRF score of the retrieved chunk")
    content: str = Field(description="Summary of retrieved chunks from file")


class ChunkSummarizerOutput(BaseModel):
    chunk_summaries: List[ChunkSummary] = Field(description="List of summaries for each of the chunk provided")


class ChunkSummarizer:
    def __init__(self, llm: ChatOpenAI | ChatVertexAI):
        self.llm = llm
        self.logger = logging.getLogger(self.__class__.__name__)
        self.output_parser = PydanticOutputParser(pydantic_object=ChunkSummarizerOutput)
        self.system_message = SystemMessage(content=f"""
            You are a chunk summarizer. Your task is to condense the retrieved document chunks into concise summaries that retain all the essential information relevant to a given user query.

            <instructions>
            1. Carefully read and understand the user's query and the chunks presented to you.
            2. Identify main points and key details that are present in each of the chunks.
            3. Prioritize information within the chunk that either directly addresses or is highly relevant to the user's query. However, **DO NOT INVENT INFORMATION OR MAKE ASSUMPTIONS OUTSIDE THE CHUNK'S CONTENT".
            </instructions>

            <formatting>
            You must begin your response with an open curly brace: {{
            {self.output_parser.get_format_instructions()}
            </formatting>
        """)

    def __call__(self, state: ChatState) -> dict:
        query = state["query"]

        document_chunks = state["document_chunks"]
        if document_chunks:
            chunks_text = "\n\n".join([
                f"Filename: {chunk["filename"]}\nRRF score: {round(chunk["rrf_score"], 3)}\nContent: {chunk["content"]}"
                for chunk in document_chunks
            ])
            chunks_section = f"<document_chunks>\n{chunks_text}\n</document_chunks>"
        else:
            chunks_section = "<document_chunks>No document chunks available.</document_chunks>"

        try:
            response = self.llm.invoke([
                self.system_message,
                HumanMessage(content=f"""
                    Summarize the following chunks, ensuring that each summary remains relevant to the user's query.

                    <user_query>{query}</user_query>

                    {chunks_section}
                """)
            ])
            parsed_content = self.output_parser.parse(response.content)
            chunk_summaries = parsed_content.chunk_summaries
            self.logger.debug("Successfully summarized chunks")
        except Exception as e:
            self.logger.exception(e)
            chunk_summaries = document_chunks

        return {"chunk_summaries": chunk_summaries}
