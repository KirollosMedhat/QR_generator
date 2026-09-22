from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends, HTTPException, Response
from fastapi.responses import RedirectResponse
import db_management
import os
from dotenv import load_dotenv

@asynccontextmanager
async def lifespan(app: FastAPI):
    db_management.Base.metadata.create_all(db_management.engine)
    yield

load_dotenv()

api = FastAPI(lifespan=lifespan)
base_url = os.getenv("BASE_URL")
if base_url is None:
    raise RuntimeError("BASE_URL environment variable is not set")


@api.get("/qrcode/{id}")
def get_qr_code(id: int):
    
    img = db_management.gen_from_id(base_url, id) # type: ignore[arg-type]
    if img is None:
        raise HTTPException(status_code=404, detail="QR code not found")

    svg_data = img.to_string()
    return Response(content=svg_data, media_type="image/svg+xml")

@api.post("/create_qrcode")
def new_qrcode(url: str, company: str):

    id, img = db_management.gen_new_QRCode(base_url, url, company) # type: ignore[arg-type]
    return id

@api.get("/qrcode/{id}/visit")
def redirect(id: int):
    redirected_url = db_management.increment_visit(id)

    if redirected_url is None:
        raise HTTPException(status_code=404, detail="website not found")
    
    return RedirectResponse(url=redirected_url)


