import logging
import logging.handlers


FORMATTER = logging.Formatter("%(asctime)s [ %(levelname)s ] %(message)s")
LEVEL = logging.INFO

handler_file = logging.handlers.RotatingFileHandler(
    "kutana.log", maxBytes=5243000, backupCount=5
)
handler_file.setLevel(LEVEL)
handler_file.setFormatter(FORMATTER)

handler_stream = logging.StreamHandler()
handler_stream.setLevel(LEVEL)
handler_stream.setFormatter(FORMATTER)

logger = logging.getLogger("kutana")
logger.setLevel(LEVEL)
logger.addHandler(handler_stream)
logger.addHandler(handler_file)


def set_logger_level(level):  # pragma: no cover
    handler_file.setLevel(level)
    handler_stream.setLevel(level)
    logger.setLevel(level)
