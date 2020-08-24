from collections import namedtuple
from enum import Enum


class HandlerResponse(Enum):
    COMPLETE = 1
    SKIPPED = 2


Handler = namedtuple("Handler", [
    "handle", "priority",
])
