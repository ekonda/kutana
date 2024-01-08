# Expose public API
from .backend import Backend
from .context import Context
from .exceptions import RequestException
from .handler import PROCESSED, SKIPPED
from .helpers import get_path
from .kutana import Kutana
from .plugin import Plugin
from .storages import MemoryStorage
from .update import Attachment, Message, RecipientKind

# Attempt to enable uvloop
try:
    import uvloop

    uvloop.install()
except ModuleNotFoundError:
    pass

# Setup nice logging format
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [ %(levelname)s ] %(message)s",
)


__all__ = [
    "Attachment",
    "Backend",
    "Context",
    "get_path",
    "Kutana",
    "MemoryStorage",
    "Message",
    "Plugin",
    "PROCESSED",
    "RecipientKind",
    "RequestException",
    "SKIPPED",
]
