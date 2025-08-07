from pydantic import BaseModel
from langchain.schema import Document
from langchain_openai import ChatOpenAI
from langchain.chains.question_answering import load_qa_chain
from dotenv import load_dotenv
import os
from supabase import create_client, Client

from app.legacy.gpt import Chat, get_answer
from app.legacy.pdf import get_pdf_answer
from app.legacy.rag import get_rag_answer
from app.llms import gpt_4o_mini

load_dotenv()
url: str = os.environ.get('SUPABASE_URL')
key: str = os.environ.get('SUPABASE_SERVICE_ROLE_KEY')
supabase: Client = create_client(url, key)


def get_summaries(topic: str):
    res = supabase.table('document_summaries').select('filepath, summary').execute()
    return [
        f"{item['filepath']}: {item['summary']}"
        for item in res.data
        if topic == item['filepath'].split('/')[0]
    ]


def can_use_gpt(chats: list[Chat], query: str):
    chat_strings = ', '.join(str(chat) for chat in chats)
    messages = [
        (
            'system',
            'You are an AI chatbot assistant to university students in a group chat with the aim to answer their queries accurately. You are expected to act like an additional group member and have natural conversations with them.'
            + ' You will be given a conversation between students in a group discussion, with the following format <Student Name>: <Message>, Those with student name AI Chatbot are responses you have previously given.'
            + ' Your job is to categorise whether the past context of the conversation is enough to answer the query or whether additional information is needed. Respond YES if no additional information is needed. Respond NO if the query cannot be answered with the past conversation only.'
            + ' If a similar question was asked previously, response is definitely YES. If the query given does not sound like a question, response is definitely NO.',
        ),
        (
            'user',
            'This is the query the user would like an answer for:'
            + query
            + ' Below is the chat conversation to categorise if the context of this conversation is enough to answer the query accurately:'
            + chat_strings
            + 'Categorise by responding with either YES or NO. Do not add anything else to the response.',
        ),
    ]

    return gpt_4o_mini.invoke(messages).content


def can_use_summary(summaries, query: str):
    messages = [
        (
            'system',
            'You are an AI chatbot assistant to university students in a group chat with the aim to answer their queries accurately. You are expected to act like an additional group member and have natural conversations with them.'
            + ' You will be given a list of summaries for some PDF documents.'
            + ' Your job is to categorise whether the summaries of documents is enough to answer the query or more information is needed. Categorise as YES if query can be answered with the PDF summaries and no additional information is needed. Categorise as NO if more information is needed and summaries are not enough.',
        ),
        (
            'user',
            'This is the query the user would like an answer for:'
            + query
            + ' Below is the list of summaries in the format <filepath>: <summary>. Categorise if they are enough to answer the query accurately:'
            + str(summaries)
            + ' Categorise by responding with either YES or NO. Do not add anything else to the response.',
        ),
    ]

    return gpt_4o_mini.invoke(messages).content


def get_advanced_answer(chats: list[Chat], topic: str, query: str):
    if can_use_gpt(chats[:-1], query) == 'YES':
        return 'Quick Reply: ' + get_answer(chats)

    summaries = get_summaries(topic)
    if can_use_summary(summaries, query) == 'YES':
        chain = load_qa_chain(
            ChatOpenAI(model_name='gpt-3.5-turbo', temperature=0), chain_type='stuff'
        )
        summary_answer = chain.invoke(
            {
                'input_documents': [Document(page_content=text) for text in summaries],
                'question': query,
            }
        )['output_text']
        return 'Summary Query: ' + summary_answer

    rag_answer = get_rag_answer(topic, query)
    if (
        rag_answer
        != 'I do not have enough information to accurately answer that based on current documents.'
    ):
        return 'RAG Query: ' + rag_answer

    return 'PDF Query: ' + get_pdf_answer(topic, query)
