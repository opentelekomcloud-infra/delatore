from delatore.emoji import Emoji

AWX_EMOJI_MAP = {
    'successful': Emoji.SUCCESS,
    'failed': Emoji.FAILED,
    'never updated': Emoji.NO_DATA,
}

INFLUX_EMOJI_MAP = {
    '`OK`': Emoji.SUCCESS,
    '`FAIL`': Emoji.FAILED,
    '`NO_DATA`': Emoji.NO_DATA,
}

AWX_LISTENER_EMOJI_MAP = {
    '`failed`': Emoji.FAILED,
    '`running`': Emoji.RUNNING,
    '`success`': Emoji.SUCCESS,
    '`cancelled`': Emoji.CANCELED
}
