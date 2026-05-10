class LaddroAPIError(Exception):
    def __init__(self, message: str, status: int, code: str | None = None):
        super().__init__(message)
        self.status = status
        self.code = code


class LaddroAuthError(LaddroAPIError):
    def __init__(self, message: str):
        super().__init__(message, 401, "unauthorized")


class LaddroUsageLimitError(LaddroAPIError):
    def __init__(self, message: str):
        super().__init__(message, 402, "usage_limit")


class LaddroNotFoundError(LaddroAPIError):
    def __init__(self, message: str):
        super().__init__(message, 404, "not_found")
