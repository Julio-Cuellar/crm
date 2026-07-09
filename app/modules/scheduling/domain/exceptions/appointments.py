from app.platform.exceptions import AppException


class AppointmentNotFoundException(AppException):
    def __init__(self, message: str = "La cita solicitada no existe o no pertenece a este negocio."):
        super().__init__(
            status_code=404,
            code="APPOINTMENT_NOT_FOUND",
            message=message
        )


class AppointmentConflictException(AppException):
    def __init__(self, message: str = "El horario solicitado se superpone con otra cita existente."):
        super().__init__(
            status_code=409,
            code="APPOINTMENT_CONFLICT",
            message=message
        )


class RelatedCustomerNotFoundException(AppException):
    """Mismo código/forma de error que `customers.CustomerNotFoundException`, pero
    definida localmente para que `scheduling` no dependa del módulo `customers`."""

    def __init__(self, message: str = "El cliente solicitado no existe o no pertenece a este negocio."):
        super().__init__(
            status_code=404,
            code="CUSTOMER_NOT_FOUND",
            message=message
        )


class RelatedServiceNotFoundException(AppException):
    """Mismo código/forma de error que `catalog.ServiceNotFoundException`, pero
    definida localmente para que `scheduling` no dependa del módulo `catalog`."""

    def __init__(self, message: str = "El servicio solicitado no existe o no pertenece a este negocio."):
        super().__init__(
            status_code=404,
            code="SERVICE_NOT_FOUND",
            message=message
        )
