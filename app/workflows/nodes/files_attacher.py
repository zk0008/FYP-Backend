import logging

from langchain_core.messages import HumanMessage

from app.workflows.state import ChatState


class FilesAttacher:
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)


    def __call__(self, state: ChatState) -> dict:
        """
        Attaches any files sent by the user to the input message.
        """
        user_message = state["chat_history"][-1]
        chat_history = state["chat_history"][:-1]  # Excluding last user message

        if isinstance(user_message, HumanMessage):
            initial_content = user_message.content
            new_user_message = HumanMessage(
                content=[
                    {
                        "type": "text",
                        "text": initial_content
                    }
                ] + state["files_data"]
            )
            chat_history.append(new_user_message)
        else:
            self.logger.warning("Last message is not a HumanMessage, cannot attach files.")
            chat_history.append(user_message)

        return {"chat_history": chat_history}
