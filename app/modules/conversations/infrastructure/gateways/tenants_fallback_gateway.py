import httpx
from fastapi import HTTPException, status

from app.platform.config import settings


class TenantsFallbackGateway:
    """Llama al endpoint público de `tenants` para obtener la configuración de WhatsApp
    del tenant actual, en vez de leer `Tenant`/`TenantCredential` directamente. No se
    proyecta localmente porque incluye un secreto descifrado — duplicarlo en la tabla
    de otro módulo multiplicaría la superficie de exposición sin necesidad real (no es
    un hot path, es una llamada por mensaje enviado)."""

    def __init__(self, access_token: str) -> None:
        self._access_token = access_token

    async def get_whatsapp_config(self) -> tuple[str, str]:
        url = f"{settings.INTERNAL_API_BASE_URL.rstrip('/')}/tenants/me/whatsapp"
        headers = {"Authorization": f"Bearer {self._access_token}"}
        async with httpx.AsyncClient(timeout=5.0) as client:
            try:
                response = await client.get(url, headers=headers)
            except httpx.HTTPError:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="No se pudo obtener la configuración de WhatsApp, intente de nuevo.",
                )
        if response.status_code != 200:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant no encontrado.")

        data = response.json()
        phone_number_id = data.get("phoneNumberId")
        access_token = data.get("whatsappApiToken")

        if not phone_number_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El tenant no tiene configurado un Phone Number ID de WhatsApp.",
            )
        if not access_token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El tenant no tiene configurado un token de acceso de WhatsApp.",
            )
        return phone_number_id, access_token
