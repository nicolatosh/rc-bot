import enum
import json
from random import choice


class ConversationType(enum.Enum):
    CONTINUE_QUESTION = "CONTINUE_QUESTION"
    CONTINUE_YES = "CONTINUE_YES"
    CONTINUE_NO = "CONTINUE_NO"
    WELCOME = "WELCOME"


class ConversationText:
    """
    Manages the conversation text of the BOT
    to make it "human" like.
    Fluent api implemented.

    Example:
        conv.type(ConversationType.CONTINUE_YES).random().get()
    """
    def __init__(self):
        with open("conversation.json", encoding='utf-8') as f:
            self.conversation = json.load(f)

        self.__out_text = None
        self.__conversation_type = None
        self.__rnd = False

    def type(self, conversation_type: ConversationType):
        self.__conversation_type = conversation_type
        return self

    def random(self):
        self.__rnd = True
        return self

    def get(self) -> str:
        """
        Get the conversation text for the bot based on the
        status. Set the status using "TYPE" method.
        :return:
        """
        if self.__conversation_type is None:
            self.__conversation_type = ConversationType.WELCOME

        messages = self.conversation[self.__conversation_type.value]
        if self.__rnd:
            return choice(messages)
        else:
            return messages[0]




