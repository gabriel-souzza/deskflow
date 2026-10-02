import qrcode
from PIL import Image


def generate_qr_token(token: str) -> Image.Image:
    img = qrcode.make(token)
    return img