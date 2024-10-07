from pydantic import BaseModel
from langchain_openai import ChatOpenAI
from langchain.chains.question_answering import load_qa_chain
from dotenv import load_dotenv
import os

load_dotenv()
llm = ChatOpenAI()


class Chat(BaseModel):
    username: str
    message: str

    def __str__(self):
        return f"{self.username}: {self.message}"


def get_answer(chats: list[Chat]):
    chat_strings = ", ".join(str(chat) for chat in chats)
    messages = [
        (
            "system",
            "You are an assistant to university students in a group project, you are expected to act like an additional group member and have natural conversations with them. Your response to them should only be around 1 to 3 short sentences/phrases, and be in a conversational manner. You should read the conversation of students and try to match their energy. You can also address student names directly. You are to start each response with 'Hi team,' or 'Hi <Student Name>, ' ",
        ),
        (
            "user",
            "The following is a conversation between students in a group discussion, with the following format <Student Name>: <Message>, Those with student name AI Chatbot are responses you have previously given"
            + chat_strings
            + ". Reply to the following messages and give meaningful insights to help the discussion, like you are group member.",
        ),
    ]

    return llm.invoke(messages).content
