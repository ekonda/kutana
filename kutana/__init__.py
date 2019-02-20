"""Kutana - engine for developing bots."""

from kutana.environment import Environment
from kutana.exceptions import ExitException
from kutana.executor import Executor
from kutana.functions import get_path, import_module, load_plugins, load_value
from kutana.kutana import Kutana
from kutana.logger import logger, set_logger_level
from kutana.manager.basic import BasicManager
from kutana.manager.debug import DebugEnvironment, DebugManager
from kutana.manager.tg import TGEnvironment, TGManager, TGResponse
from kutana.manager.vk import VKEnvironment, VKManager, VKRequest, VKResponse
from kutana.plugin import Attachment, Message, Plugin

try:
    import uvloop

    uvloop.install()
except ImportError:  # pragma: no cover
    pass


NAME = "kutana"
