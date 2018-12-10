from loguru import logger
logger.start("kutana-{time}.log", compression="zip", rotation="2 MB")


