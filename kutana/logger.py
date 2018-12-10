from loguru import logger
logger.start("kutana.log", compression="zip", rotation="2 MB")


