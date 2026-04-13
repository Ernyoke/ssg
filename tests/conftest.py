"""
Shared pytest fixtures available to all test modules.
"""
import pytest
from bs4 import BeautifulSoup

from config.config import MetaFields

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


@pytest.fixture()
def default_meta():
    """A fully-populated MetaFields instance with sensible defaults."""
    return MetaFields(
        title="My Title",
        image="images/cover.png",
        description="My description",
        url="https://example.com/page",
        twitter_handle="@myhandle",
    )

