class RequestException(Exception):
    def __init__(self, backend, request, response, error=None):
        self.backend = backend
        self.request = request
        self.response = response
        self.error = error
