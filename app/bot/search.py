import concurrent.futures
import typing as t
from traceback import extract_tb

from motor.motor_asyncio import AsyncIOMotorCursor

from hash import CompareResult, compare_two_hash
from utils import get_custom_logger

logger = get_custom_logger("bot__search")


async def search_for_similarity(suspect_hash: str, cursor: AsyncIOMotorCursor):
    futs = list()
    with concurrent.futures.ProcessPoolExecutor() as pool:
        async for doc in cursor:
            futs.append(
                (
                    pool.submit(check_image_similarity, suspect_hash, doc["img_hash"]),
                    doc,
                )
            )

    similar_photos = list()
    for fut, doc in futs:
        try:
            r = fut.result()
            is_similar, comparison = r
            if is_similar:
                similar_photos.append((comparison, doc["message_id"], doc["is_active"]))
        except Exception as e:
            logger.error(extract_tb(e))
            continue
    return similar_photos


def check_image_similarity(img_hash_1: str, img_hash_2: str) -> t.Tuple[bool, float]:
    r, s = compare_two_hash(img_hash_1, img_hash_2)
    if r in {CompareResult.ALMOST_SAME, CompareResult.SAME}:
        return True, s
    return False, s
