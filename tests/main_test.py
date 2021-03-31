import unittest

import ssg


class MyTestCase(unittest.TestCase):
    def test_replace_md_with_html(self):
        self.assertEqual(ssg.replace_md_with_html('<a href="asd.md"></a><a href="x.html"></a>'),
                         '<a href="asd.html"></a><a href="x.html"></a>')

    def test_add_base_path(self):
        self.assertEqual(ssg.add_base_path(['<head>', '</head>'], 'base.html'),
                         ['<head>', '<base href="base.html"/>', '</head>'])


if __name__ == '__main__':
    unittest.main()
