import unittest
import sys
sys.path.append("..")
from app.hash import init_image, get_phash

class TestHash(unittest.TestCase):

    def setUp(self):
        self.img_1 = open("./tests/test_images/test_image_1.1.jpg", "rb")
        self.img_2 = open("./tests/test_images/test_image_1.2.jpg", "rb")

    def test_not_image(self):
        not_image = open("./tests/test_images/not_image.txt", "rb")

        self.assertLogs("hash", level="ERROR")
        self.assertIs(init_image(not_image), None)

        not_image.close()

    def test_same_image(self):
        img_1_hash_1 = get_phash(init_image(self.img_1))
        img_1_hash_2 = get_phash(init_image(self.img_1))

        self.assertEqual(img_1_hash_1, img_1_hash_2)

    def test_diff_image(self):
        img_1_hash = get_phash(init_image(self.img_1))
        img_2_hash = get_phash(init_image(self.img_2))

        self.assertNotEqual(img_1_hash, img_2_hash)

    def tearDown(self) -> None:
        self.img_1.close()
        self.img_2.close()

if __name__ == '__main__':
    unittest.main()