import logging
import logging.handlers


FORMATTER = logging.Formatter("%(asctime)s [ %(levelname)s ] %(message)s")
LEVEL = logging.INFO

handler_stream = logging.StreamHandler()
handler_stream.setLevel(LEVEL)
handler_stream.setFormatter(FORMATTER)

logger = logging.getLogger("kutana")
logger.setLevel(LEVEL)
logger.addHandler(handler_stream)


def set_logger_level(level):  # pragma: no cover
    handler_stream.setLevel(level)
    logger.setLevel(level)
