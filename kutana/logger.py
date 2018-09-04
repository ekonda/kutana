import logging


formatter = logging.Formatter('%(asctime)s [ %(levelname)s ] %(message)s')
level = logging.DEBUG

handler_file = logging.FileHandler('kutana.log')
handler_file.setLevel(level)
handler_file.setFormatter(formatter)

handler_stream = logging.StreamHandler()
handler_stream.setLevel(level)
handler_stream.setFormatter(formatter)

logger = logging.getLogger("kutana")
logger.setLevel(level)
logger.addHandler(handler_stream)
logger.addHandler(handler_file)
