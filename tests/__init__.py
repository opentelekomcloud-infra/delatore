import logging

LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.DEBUG)
CLG = logging.StreamHandler()
CLG.setLevel(logging.DEBUG)
LOGGER.addHandler(CLG)
