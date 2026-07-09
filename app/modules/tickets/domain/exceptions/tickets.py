from app.platform.exceptions import AppException

class TicketNotFoundException(AppException):
    def __init__(self, message: str = "El ticket solicitado no fue encontrado."):
        super().__init__(status_code=404, code="TICKET_NOT_FOUND", message=message)
