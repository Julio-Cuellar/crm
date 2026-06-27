class AppException(Exception):
    """Excepción base para toda la aplicación.
    
    Permite propagar códigos HTTP y códigos de error internos unificados.
    """
    def __init__(self, status_code: int, code: str, message: str):
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message
