"""Exceptions for the Ambeo Soundbar API."""


class AmbeoError(Exception):
    """Base class for all Ambeo Soundbar API errors."""


class AmbeoConnectionError(AmbeoError):
    """Raised when the device cannot be reached."""


class AmbeoTimeoutError(AmbeoConnectionError):
    """Raised when a request to the device times out."""


class AmbeoResponseError(AmbeoError):
    """Raised when the device answers with an unexpected response."""

    def __init__(self, message: str, status: int | None = None) -> None:
        """Initialize with an optional HTTP status code."""
        super().__init__(message)
        self.status = status


class AmbeoUnsupportedModelError(AmbeoError):
    """Raised when the device model is not supported."""

    def __init__(self, model: str | None) -> None:
        """Initialize with the unsupported model name."""
        super().__init__(f"Unsupported model: {model}")
        self.model = model
