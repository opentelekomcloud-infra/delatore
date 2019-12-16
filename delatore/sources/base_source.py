from ..bot import Delatore


class BaseSource:
    bot: Delatore

    def __init__(self, bot: Delatore):
        self.bot = bot
