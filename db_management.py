import os
from dotenv import load_dotenv

from sqlalchemy import create_engine, String, Integer, DateTime, update
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker


from datetime import datetime, timezone

import qrcode
import qrcode.image.svg
from qrcode import constants

load_dotenv()

db_URL = os.getenv("DATABASE_URL")
if db_URL is None:
    raise RuntimeError("DATABASE_URL environment variable is not set")

engine = create_engine(db_URL)
SessionLocal = sessionmaker(bind=engine)

class Base(DeclarativeBase):
    pass

class QRCode(Base):
    __tablename__ = "qr_codes"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    url: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    company: Mapped[str] = mapped_column(String, nullable=False)
    visits: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    #svg_path: Mapped[str] = mapped_column(String, nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

def get_db():
    with SessionLocal() as db:
        yield db

def store_qr_code_in_db(url:str, company: str):
    with SessionLocal() as db:
        existing = db.query(QRCode).filter(QRCode.url == url).first()
        if existing:
            print(f"\nexisint id: {existing.id}")
            return existing.id
        
        new_qr = QRCode(url = url, company = company)
        db.add(new_qr)
        db.commit()
        db.refresh(new_qr)
        print(f"\nCreated a new entry with id: {new_qr.id}")
        return new_qr.id

def _build_qr_image(base_url:str, id:int):
    qr = qrcode.QRCode(image_factory=qrcode.image.svg.SvgPathImage, error_correction=constants.ERROR_CORRECT_Q)
    qr.add_data(f"{base_url}/qrcode/{id}/visit")
    img = qr.make_image()
    #img.save("testing.svg") # type: ignore[arg-type]
    print("\nGenerating the image.")
    return img

def gen_new_QRCode(base_url:str, url: str, company:str):
    id = store_qr_code_in_db(url, company)
    print("\ngen_new_QRCode here")
    return id, _build_qr_image(base_url, id)                                  #yet to decide how we will handle img.

    # img.save("vector_code.svg")
    # print("inside gen qrcode")

def gen_from_id(base_url:str, qr_id: int):
    with SessionLocal() as db:
        existing = db.query(QRCode).filter(QRCode.id == qr_id).first()
        if not existing:
            print("Returing None, no matching id")
            return None
        print("\ngen_from_id here")
        return _build_qr_image(base_url, existing.id)



# def increment_visit(qr_id: int):
#     with SessionLocal() as db:
#         existing = db.query(QRCode).filter(QRCode.id == qr_id).first()
#         if not existing:
#             print("Returing None, no matching id")
#             return None

#         existing.visits += 1
#         db.commit()
#         return existing.url


# better version than the above.
def increment_visit(qr_id: int):
    with SessionLocal() as db:
        result = db.execute(
            update(QRCode)
            .where(QRCode.id == qr_id)
            .values(visits=QRCode.visits + 1)
            .returning(QRCode.url)
        )
        row = result.first()
        db.commit()
        if row is None:
            return None
        return row[0]