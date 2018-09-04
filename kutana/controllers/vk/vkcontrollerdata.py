from collections import namedtuple
import asyncio


VKResponse = namedtuple(
    "VKResponse",
    "error kutana_error response_error response execute_errors"
)


class VKRequest(asyncio.Future):
    __slots__ = ("mthod", "kwargs")

    def __init__(self, method, **kwargs):
        super().__init__()

        self.method = method
        self.kwargs = kwargs
