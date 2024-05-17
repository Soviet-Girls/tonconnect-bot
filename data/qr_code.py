
from qrcode_styled.pil.image import PilStyledImage, Image

import qrcode_styled
from io import BytesIO

def generate(data: str) -> BytesIO:
    qr = qrcode_styled.QRCodeStyled(
        version=None,
        error_correction=qrcode_styled.ERROR_CORRECT_M,
        border=1,
        box_size=32,
        image_factory=PilStyledImage,
        mask_pattern=None,
    )

    img = qr.get_image(
        data=data,
        image=Image.open('images/logo.png'),
        optimize=100,
    )

    buff = BytesIO()
    img.save(buff, 'PNG')
    buff.seek(0)
    img = Image.open(buff)
    img = img.crop((19, 19, img.width - 19, img.height - 19))
    img = img.resize((684, 684))
    background = Image.open('images/background.png')
    background.paste(img, (157, 157))
    buff = BytesIO()
    background.save(buff, 'PNG')
    buff.seek(0)
    return buff