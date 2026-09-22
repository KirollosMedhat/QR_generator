from datetime import datetime, timezone
from sqlalchemy import String, Integer, DateTime
from sqlalchemy.orm import Mapped, mapped_column

from database import Base

class QRCode(Base):
    __tablename__ = "qr_codes"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    url: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    company: Mapped[str] = mapped_column(String, nullable=False)
    visits: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    #svg_path: Mapped[str] = mapped_column(String, nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
