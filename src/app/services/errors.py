class ServiceError(Exception):
    """Base class for expected use-case failures rendered by HTTP handlers."""


class NotFoundError(ServiceError):
    """The requested resource does not exist."""


class ConflictError(ServiceError):
    """The request conflicts with the current state of a resource."""
