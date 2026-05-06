class AppError(Exception):
    def __init__(self, message: str, status_code: int = 400, code: str = "app_error") -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.code = code


class ProviderConfigurationError(AppError):
    def __init__(self, message: str = "LLM provider is not configured.") -> None:
        super().__init__(message=message, status_code=503, code="provider_configuration_error")


class ProviderRequestError(AppError):
    def __init__(self, message: str = "Provider request failed.") -> None:
        super().__init__(message=message, status_code=502, code="provider_request_error")
