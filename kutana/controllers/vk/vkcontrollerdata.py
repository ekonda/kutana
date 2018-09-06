from collections import namedtuple
import asyncio


VKResponse = namedtuple(
    "VKResponse",
    "error kutana_error response_error response execute_errors"
)

VKResponse.__doc__ = """ `error` is a boolean value indicating if error
happened.

`kutana_error`, `response_error` and `execute_errors` contains happened
errors.

`response` contains result of reqeust if no errors happened.
"""


class VKRequest(asyncio.Future):
    __slots__ = ("mthod", "kwargs")

    def __init__(self, method, **kwargs):
        super().__init__()

        self.method = method
        self.kwargs = kwargs
