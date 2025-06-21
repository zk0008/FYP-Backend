import logging

from langchain_core.messages import AIMessage, HumanMessage
from supabase import Client

from app.workflows.state import ChatState


class HistoryFetcher:
    def __init__(self, supabase: Client):
        self.supabase = supabase
        self.logger = logging.getLogger(self.__class__.__name__)

    def __call__(self, state: ChatState) -> ChatState:
        """
        Fetches conversation history from Supabase database.
        """
        chatroom_id = state["chatroom_id"]

        try:
            response = (
                self.supabase.rpc("get_chatroom_messages", { "p_chatroom_id": chatroom_id })
                .execute()
            )

            # # Exclude last message for now, which is the latest message sent by the user to invoke GroupGPT
            messages = response.data
            chat_history = []

            # Users' and GroupGPT's messages are separated
            current_user_messages = []
            for msg in messages:
                username = msg["username"]
                content = msg["content"]

                # Current message is from GroupGPT
                if username == "GroupGPT":
                    # Add accumulated user messages first
                    if current_user_messages:
                        combined_user_messages = "\n".join(current_user_messages)
                        chat_history.append(HumanMessage(content=combined_user_messages))
                        current_user_messages = []

                    # Add GroupGPT's message
                    chat_history.append(AIMessage(content=content))
                # Current message is from a user
                else:
                    current_user_messages.append(f"{username}: {content}")


            # Include last message, which is user's rewritten query, to remaining user messages
            # current_user_messages.append(f"{state["username"]}: {state["rewritten_query"]}")
            combined_user_messages = "\n".join(current_user_messages)
            chat_history.append(HumanMessage(content=combined_user_messages))

            self.logger.debug("Successfully fetched conversation history")
        except Exception as e:
            self.logger.exception(e)

        return {"chat_history": chat_history}
