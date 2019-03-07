"""Kutana - engine for developing bots."""

from .environment import Environment
from .exceptions import ExitException
from .loaders import import_module, load_plugins, load_plugins_from_file
from .utils import get_path, is_list_or_tuple, sort_callbacks
from .kutana import Kutana
from .logger import logger, set_logger_level
from .manager.manager import Manager
from .manager.debug import DebugEnvironment, DebugManager
from .manager.tg import TGEnvironment, TGManager, TGResponse
from .manager.vk import VKEnvironment, VKManager, VKRequest, VKResponse
from .plugin import Attachment, Message, Plugin

try:
    import uvloop
    uvloop.install()
except ImportError:  # pragma: no cover
    pass


NAME = "kutana"
