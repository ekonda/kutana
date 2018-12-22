"""Module with logger that is used in this engine."""


import logging
import logging.handlers


FORMATTER = logging.Formatter('%(asctime)s [ %(levelname)s ] %(message)s')
LEVEL = logging.INFO

handler_file = logging.FileHandler('kutana.log')
handler_file.setLevel(LEVEL)
handler_file.setFormatter(FORMATTER)

handler_stream = logging.StreamHandler()
handler_stream.setLevel(LEVEL)
handler_stream.setFormatter(FORMATTER)

logger = logging.getLogger("kutana")
logger.setLevel(LEVEL)
logger.addHandler(handler_stream)
logger.addHandler(handler_file)
