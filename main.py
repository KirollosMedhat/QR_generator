from contextlib import asynccontextmanager
from sqlalchemy.exc import OperationalError, IntegrityError
from fastapi import FastAPI, Depends, HTTPException, Response,  Request
from fastapi.responses import RedirectResponse, JSONResponse
import os
from dotenv import load_dotenv
from pydantic import BaseModel, HttpUrl 

from database import Base, engine
import qr_services

class CreateQR(BaseModel):
    url: HttpUrl
    company: str


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(engine)
    yield

load_dotenv()

api = FastAPI(lifespan=lifespan)

base_url = os.getenv("BASE_URL")
if base_url is None:
    raise RuntimeError("BASE_URL environment variable is not set")

@api.exception_handler(OperationalError)
def handle_operational_error(request: Request, exc: OperationalError):
    return JSONResponse(
        status_code=503,
        content={"detail": "Database is currently unavailable. Please try again later."},
    )

#IntegrityError in store_qr_code_in_db will get handled there first before here due to the call order.
@api.exception_handler(IntegrityError)
def handle_integrity_error(request: Request, exc: IntegrityError):
    return JSONResponse(
        status_code=409,
        content={"detail": "A conflicting record already exists."},
    )

@api.get("/qrcode/{id}")
def get_qr_code(id: int):
    img = qr_services.gen_from_id(base_url, id) # type: ignore[arg-type]
    if img is None:
        raise HTTPException(status_code=404, detail="QR code not found")

    svg_data = img.to_string()
    return Response(content=svg_data, media_type="image/svg+xml")

@api.post("/create_qrcode")
def new_qrcode(QRCode: CreateQR):

    id, img = qr_services.gen_new_QRCode(base_url, str(QRCode.url), QRCode.company) # type: ignore[arg-type]
    return id

@api.get("/qrcode/{id}/visit")
def redirect(id: int):
    redirected_url = qr_services.increment_visit(id)

    if redirected_url is None:
        raise HTTPException(status_code=404, detail="website not found")
    
    return RedirectResponse(url=redirected_url)