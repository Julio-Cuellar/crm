from typing import Any
from sqlalchemy.orm import DeclarativeBase, declared_attr


class Base(DeclarativeBase):
    id: Any
    __name__: str

    # Genera automáticamente el nombre de la tabla en snake_case
    @declared_attr.directive
    def __tablename__(cls) -> str:
        # Convierte de CamelCase a snake_case
        name = cls.__name__
        parts = []
        start = 0
        for i, char in enumerate(name):
            if char.isupper() and i > 0:
                parts.append(name[start:i].lower())
                start = i
        parts.append(name[start:].lower())
        return "_".join(parts)
