import logging

from langchain_core.messages import AIMessage, HumanMessage, trim_messages
from langchain_core.messages.utils import count_tokens_approximately
from supabase import Client

from app.constants import GEMINI_25_MAX_INPUT_TOKENS
from app.workflows.state import ChatState


class HistoryFetcher:
    def __init__(self, supabase: Client):
        self.supabase = supabase
        self.logger = logging.getLogger(self.__class__.__name__)


    def __call__(self, state: ChatState) -> dict:
        """
        Fetches conversation history from Supabase database.
        """
        chatroom_id = state["chatroom_id"]

        try:
            response = (
                self.supabase.rpc("get_chatroom_messages", { "p_chatroom_id": chatroom_id })
                .execute()
            )

            messages = response.data
            chat_history = []
            # Separate user messages and GroupGPT's messages
            current_user_messages = []
            current_groupgpt_messages = []

            for msg in messages:
                username = msg["username"]
                content = msg["content"]

                if username == "GroupGPT":  # Current message is from GroupGPT
                    # Add accumulated user messages first (if any)
                    if current_user_messages:
                        combined_user_messages = "\n".join(current_user_messages)
                        chat_history.append(HumanMessage(content=combined_user_messages))
                        current_user_messages = []

                    # Accumulate GroupGPT's messages
                    current_groupgpt_messages.append(f"{username}: {content}")
                else:  # Current message is from a user
                    # Add accumulated GroupGPT messages first (if any)
                    if current_groupgpt_messages:
                        combined_groupgpt_messages = "\n".join(current_groupgpt_messages)
                        chat_history.append(AIMessage(content=combined_groupgpt_messages))
                        current_groupgpt_messages = []

                    # Accumulate user messages
                    current_user_messages.append(f"{username}: {content}")

            # If there are any remaining user messages, add them to the chat history
            combined_user_messages = "\n".join(current_user_messages)
            chat_history.append(HumanMessage(content=combined_user_messages))
            length_before_trim = len(chat_history)

            chat_history = trim_messages(
                chat_history,
                max_tokens=0.8 * GEMINI_25_MAX_INPUT_TOKENS,  # Set aside 20% for subsequent tool calls and responses
                strategy="last",
                token_counter=count_tokens_approximately,
                allow_partial=False
            )
            length_after_trim = len(chat_history)

            self.logger.debug(f"Successfully fetched conversation history. Length before trim: {length_before_trim}, after trim: {length_after_trim}")
        except Exception as e:
            self.logger.exception(e)

        return {"chat_history": chat_history}
