"""
Shared pytest fixtures available to all test modules.
"""
import pytest
from bs4 import BeautifulSoup

BASE_HTML = """\
<!DOCTYPE html>
<html>
<head>
    <title>Original Title</title>
</head>
<body>
    <article id="main-content"></article>
</body>
</html>
"""


@pytest.fixture()
def base_soup():
    """A minimal BeautifulSoup document used as the base for HTMLFile tests."""
    return BeautifulSoup(BASE_HTML, "lxml")

