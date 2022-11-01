import sys
import unittest

sys.path.append("..")
from app.hash import (CompareResult, compare_two_hash, get_image_hash,
                      init_image)


class TestHash(unittest.TestCase):
    def setUp(self):
        self.img_1 = open("./tests/test_images/test_image_1.1.jpg", "rb")
        self.img_2 = open("./tests/test_images/test_image_1.2.jpg", "rb")
        self.img_3 = open("./tests/test_images/test_image_2.1.jpg", "rb")
        self.img_4 = open("./tests/test_images/test_image_2.2.jpg", "rb")
        self.img_5 = open("./tests/test_images/test_image_2.3.jpg", "rb")

    def test_not_image(self):
        not_image = open("./tests/test_images/not_image.txt", "rb")

        self.assertLogs("hash", level="ERROR")
        self.assertIs(init_image(not_image), None)

        not_image.close()

    def test_same_image(self):
        img_1_hash_1 = get_image_hash(init_image(self.img_1))
        img_1_hash_2 = get_image_hash(init_image(self.img_1))
        comparison, diff = compare_two_hash(str(img_1_hash_1), str(img_1_hash_2))

        print(f"DIFF IN SAME IMAGE = ", diff)
        self.assertEqual(comparison, CompareResult.SAME)

    def test_diff_image(self):
        img_1_hash = get_image_hash(init_image(self.img_1))
        img_2_hash = get_image_hash(init_image(self.img_2))
        comparison, diff = compare_two_hash(str(img_1_hash), str(img_2_hash))

        print(f"DIFF IN DIFF IMAGE = ", diff)
        self.assertEqual(comparison, CompareResult.DIFF)

    def test_almost_same_image(self):
        img_1_hash = get_image_hash(init_image(self.img_3))
        img_2_hash = get_image_hash(init_image(self.img_4))
        comparison, diff = compare_two_hash(str(img_1_hash), str(img_2_hash))

        print(f"DIFF IN ALMOST SAME IMAGE = ", diff)
        self.assertEqual(comparison, CompareResult.ALMOST_SAME)

    def test_crop_image(self):
        img_1_hash = get_image_hash(init_image(self.img_3))
        img_2_hash = get_image_hash(init_image(self.img_5))
        comparison, diff = compare_two_hash(str(img_1_hash), str(img_2_hash))

        print(f"DIFF IN CROP IMAGE = ", diff)
        self.assertEqual(comparison, CompareResult.ALMOST_SAME)

    def tearDown(self) -> None:
        self.img_1.close()
        self.img_2.close()
        self.img_3.close()
        self.img_4.close()
        self.img_5.close()


if __name__ == "__main__":
    unittest.main()
