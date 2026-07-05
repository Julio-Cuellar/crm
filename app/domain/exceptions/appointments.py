from app.domain.exceptions.base import AppException


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
