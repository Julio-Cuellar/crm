from app.platform.exceptions import AppException


class CustomerNotFoundException(AppException):
    def __init__(self, message: str = "El cliente solicitado no existe o no pertenece a este negocio."):
        super().__init__(
            status_code=404,
            code="CUSTOMER_NOT_FOUND",
            message=message
        )


class CustomerAlreadyExistsException(AppException):
    def __init__(self, message: str = "Un cliente con este número de teléfono ya está registrado en este negocio."):
        super().__init__(
            status_code=409,
            code="CUSTOMER_ALREADY_EXISTS",
            message=message
        )
