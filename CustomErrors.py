class APIError(Exception):
    """Raised with the lightpollutionmap.info API returns a non-200 response code."""
    def __init__(self, response_code):
        self.response_code = response_code