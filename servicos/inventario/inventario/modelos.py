from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from inventario.database import Base


class Ativo(Base):
    """Tabela exclusiva do banco de inventário (sem chaves estrangeiras externas)."""
    __tablename__ = "ativos"

    id: Mapped[int] = mapped_column(primary_key=True)
    patrimonio: Mapped[str] = mapped_column(String(30), unique=True)
    tipo: Mapped[str] = mapped_column(String(30))
    descricao: Mapped[str] = mapped_column(String(200))
    setor: Mapped[str] = mapped_column(String(80))
