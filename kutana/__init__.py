"""Kutana - engine for developing bots."""

from kutana.logger import logger

from kutana.kutana import Kutana
from kutana.plugin import Plugin, Message, Attachment
from kutana.executor import Executor
from kutana.exceptions import ExitException

from kutana.environment import Environment

from kutana.manager.basic import BasicManager
from kutana.manager.debug import DebugManager, DebugEnvironment
from kutana.manager.vk import VKManager, VKRequest, VKResponse, VKEnvironment
from kutana.manager.tg import TGManager, TGResponse, TGEnvironment

from kutana.functions import get_path, load_configuration, import_module, \
    load_plugins, is_done

NAME = "kutana"
