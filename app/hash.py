from imagehash import phash, ImageHash
import typing as t
import PIL
from utils import get_custom_logger

logger = get_custom_logger(__name__)

def init_image(data: t.BinaryIO) -> PIL.Image:
    try:
        img = PIL.Image.open(data)
    except PIL.UnidentifiedImageError:
        logger.error("File can not be read as image")
        return None   
    return img

def get_phash(img: PIL.Image, hash_size=16, highfreq_factor=4) -> ImageHash:
    return phash(img, hash_size=hash_size, highfreq_factor=4)
