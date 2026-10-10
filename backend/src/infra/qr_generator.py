import io
import qrcode
from PIL import Image


def generate_qr_token(token: str) -> Image.Image:
    img = qrcode.make(token)
    return img


def generate_qr_png_bytes(token: str) -> bytes:
    img = generate_qr_token(token)
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    return buffer.getvalue()