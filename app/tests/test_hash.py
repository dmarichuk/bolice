import sys
import unittest

sys.path.append("..")
from app.hash import (CompareResult, compare_two_hash, get_image_hash,
                      init_image)


class TestHash(unittest.TestCase):
    def setUp(self):
        self.almost_same_img_1_1 = open("./tests/test_images/test_image_3.1.jpg", "rb")
        self.almost_same_img_1_2 = open("./tests/test_images/test_image_3.2.jpg", "rb")
        self.almost_same_img_2_1 = open("./tests/test_images/test_image_2.1.jpg", "rb")
        self.almost_same_img_2_2 = open("./tests/test_images/test_image_2.2.jpg", "rb")
        self.img_5 = open("./tests/test_images/test_image_2.3.jpg", "rb")
        self.img_6 = open("./tests/test_images/test_image_1.1.jpg", "rb")
        self.img_7 = open("./tests/test_images/test_image_1.2.jpg", "rb")
        self.almost_same_img_3_1 = open("./tests/test_images/almost_same_image_1.jpg", "rb")
        self.almost_same_img_3_2 = open("./tests/test_images/almost_same_image_2.jpg", "rb")

    def test_not_image(self):
        not_image = open("./tests/test_images/not_image.txt", "rb")

        self.assertLogs("hash", level="ERROR")
        self.assertIs(init_image(not_image), None)

        not_image.close()

    def test_same_image(self):
        img_1_hash_1 = get_image_hash(init_image(self.img_5))
        img_1_hash_2 = get_image_hash(init_image(self.img_5))
        comparison, diff = compare_two_hash(str(img_1_hash_1), str(img_1_hash_2))

        print("DIFF IN SAME IMAGE = ", diff)
        self.assertEqual(comparison, CompareResult.SAME)

    def test_diff_image(self):
        img_1_hash = get_image_hash(init_image(self.img_5))
        img_2_hash = get_image_hash(init_image(self.img_7))
        comparison, diff = compare_two_hash(str(img_1_hash), str(img_2_hash))

        print("DIFF IN DIFF IMAGE = ", diff)
        self.assertEqual(comparison, CompareResult.DIFF)

    def test_almost_same_image_1(self):
        img_1_hash = get_image_hash(init_image(self.almost_same_img_1_1))
        img_2_hash = get_image_hash(init_image(self.almost_same_img_1_2))
        comparison, diff = compare_two_hash(str(img_1_hash), str(img_2_hash))

        print("DIFF IN ALMOST SAME IMAGE = ", diff)
        self.assertEqual(comparison, CompareResult.ALMOST_SAME)

    def test_almost_same_image_2(self):
        img_1_hash = get_image_hash(init_image(self.almost_same_img_2_1))
        img_2_hash = get_image_hash(init_image(self.almost_same_img_2_2))
        comparison, diff = compare_two_hash(str(img_1_hash), str(img_2_hash))

        print("DIFF IN ALMOST SAME IMAGE 2 = ", diff)
        self.assertEqual(comparison, CompareResult.ALMOST_SAME)

    def test_almost_same_image_3(self):
        img_1_hash = get_image_hash(init_image(self.almost_same_img_3_1))
        img_2_hash = get_image_hash(init_image(self.almost_same_img_3_2))
        comparison, diff = compare_two_hash(str(img_1_hash), str(img_2_hash))

        print("DIFF IN ALMOST SAME IMAGE 3 = ", diff)
        self.assertEqual(comparison, CompareResult.ALMOST_SAME)

    def tearDown(self) -> None:
        self.almost_same_img_1_1.close()
        self.almost_same_img_1_2.close()
        self.almost_same_img_2_1.close()
        self.almost_same_img_2_2.close()
        self.img_5.close()
        self.img_6.close()
        self.img_7.close()
        self.almost_same_img_3_1.close()
        self.almost_same_img_3_2.close()


if __name__ == "__main__":
    unittest.main()
