from app.platform.exceptions import AppException


class TenantNotFoundException(AppException):
    def __init__(self, message: str = "El tenant solicitado no existe."):
        super().__init__(
            status_code=404,
            code="TENANT_NOT_FOUND",
            message=message
        )


class TenantSlugAlreadyExistsException(AppException):
    def __init__(self, message: str = "El slug ya está en uso por otro tenant."):
        super().__init__(
            status_code=409,
            code="TENANT_SLUG_EXISTS",
            message=message
        )


class TenantInactiveException(AppException):
    def __init__(self, message: str = "El tenant está desactivado."):
        super().__init__(
            status_code=403,
            code="TENANT_INACTIVE",
            message=message
        )


class EventBusUnavailableException(AppException):
    def __init__(self, message: str = "El bus de eventos no está disponible."):
        super().__init__(
            status_code=503,
            code="EVENT_BUS_UNAVAILABLE",
            message=message
        )
