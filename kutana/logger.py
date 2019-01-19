"""Module with logger that is used in this engine."""


import logging
import logging.handlers


FORMATTER = logging.Formatter('%(asctime)s [ %(levelname)s ] %(message)s')
LEVEL = logging.INFO

handler_file = logging.FileHandler('kutana.log')  # pylint: disable=C0103
handler_file.setLevel(LEVEL)
handler_file.setFormatter(FORMATTER)

handler_stream = logging.StreamHandler()  # pylint: disable=C0103
handler_stream.setLevel(LEVEL)
handler_stream.setFormatter(FORMATTER)

logger = logging.getLogger("kutana")  # pylint: disable=C0103
logger.setLevel(LEVEL)
logger.addHandler(handler_stream)
logger.addHandler(handler_file)


def set_logger_level(level):
    """
    Set logging level for stream, file and logger.

    :param level: logging level to set
    """

    handler_file.setLevel(level)
    handler_stream.setLevel(level)
    logger.setLevel(level)
