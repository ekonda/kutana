class RequestException(Exception):
    def __init__(self, backend, request, response):
        self.backend = backend
        self.request = request
        self.response = response
