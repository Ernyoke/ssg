import unittest

from ssg import *


class MyTestCase(unittest.TestCase):
    def test_replace_md_with_html(self):
        self.assertEqual(ssg.replace_md_with_html('<a href="asd.md"></a><a href="x.html"></a>'),
                         '<a href="asd.html"></a><a href="x.html"></a>')


if __name__ == '__main__':
    unittest.main()
