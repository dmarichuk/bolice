import enum
import typing as t

import PIL
from imagehash import (ImageHash, average_hash, hex_to_hash, phash,
                       phash_simple, whash)
from utils import get_custom_logger

logger = get_custom_logger("hash")


def init_image(data: t.BinaryIO) -> PIL.Image:
    try:
        img = PIL.Image.open(data)
    except PIL.UnidentifiedImageError:
        logger.error("File can not be read as image")
        return None
    return img


def get_image_hash(img: PIL.Image, hash_size=16, highfreq_factor=4) -> ImageHash:
    return phash(img, hash_size=hash_size, highfreq_factor=highfreq_factor)


class CompareResult(enum.IntEnum):
    DIFF = 0
    ALMOST_SAME = 1
    SAME = 2


def compare_two_hash(hash_1: str, hash_2: str) -> t.Tuple[CompareResult, float]:
    hash_1, hash_2 = hex_to_hash(hash_1), hex_to_hash(hash_2)
    comparison = (hash_1 - hash_2) / len(hash_1.hash) ** 2

    if comparison == 0:
        r = CompareResult.SAME
    elif comparison <= 0.25:
        r = CompareResult.ALMOST_SAME
    else:
        r = CompareResult.DIFF
    return r, comparison
