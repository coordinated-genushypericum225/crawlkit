"""Custom exceptions for CrawlKit SDK."""


class CrawlKitError(Exception):
    """Base exception for CrawlKit SDK."""
    pass


class AuthenticationError(CrawlKitError):
    """Raised when API key is invalid or missing."""
    pass


class RateLimitError(CrawlKitError):
    """Raised when rate limit is exceeded."""
    
    def __init__(self, message: str, retry_after: int = None):
        super().__init__(message)
        self.retry_after = retry_after


class NotFoundError(CrawlKitError):
    """Raised when a resource is not found."""
    pass


class ValidationError(CrawlKitError):
    """Raised when request validation fails."""
    pass


class ServerError(CrawlKitError):
    """Raised when server returns 5xx error."""
    pass
