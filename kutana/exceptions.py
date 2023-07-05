class RequestException(Exception):
    def __init__(self, backend, method, kwargs, response, exception=None):
        self.backend = backend
        self.method = method
        self.kwargs = kwargs
        self.response = response
        self.exception = exception
