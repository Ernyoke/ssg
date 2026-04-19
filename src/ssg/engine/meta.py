import fnmatch
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urljoin

from ssg.config import Meta
from ssg.dirtree.file_node import FileNode
from ssg.engine.cover_image import get_cover_image


@dataclass(frozen=True)
class ResolvedMeta:
    """
    Resolved HTML meta tag values for a single page.

    Holds the values that should be rendered into the ``<meta>`` tags of
    a generated HTML file (Open Graph title/description/image/url and
    Twitter handle), as resolved by :func:`get_meta` for that file's
    route. Any field may be ``None`` if no value was configured or could
    be derived for that page.
    """
    url: str
    title: str | None = None
    description: str | None = None
    cover_image: Path | None = None
    author: str | None = None
    author_email: str | None = None
    twitter_handle: str | None = None

def get_meta(file: FileNode, meta: Meta | None, base_href: str) -> ResolvedMeta:
    """
    Resolve the HTML meta tag values for ``file`` using the first matching
    route in ``meta.matchers``.

    Returns an empty :class:`ResolvedMeta` (with the default Twitter
    handle, if any) when no route matches or ``meta`` is ``None``.
    """
    if meta is None:
        return ResolvedMeta()

    url_computed = urljoin(base_href, file.path.with_suffix('.html').as_posix())
    twitter_handle = meta.default.twitter_handle
    author_name = meta.default.author_name
    author_email = meta.default.author_email
    for matcher in meta.matchers:
        if not fnmatch.fnmatch(file.path.as_posix(), matcher.file):
            continue

        default_cover_image = Path(meta.default.image) if meta.default.image is not None else None
        default_description = meta.default.description if meta.default.description is not None else None

        if matcher.action == 'USE_DEFAULT':
            return ResolvedMeta(
                title=meta.default.title,
                description=default_description,
                cover_image=default_cover_image,
                url=meta.default.url,
                author=author_name,
                author_email=author_email,
                twitter_handle=meta.default.twitter_handle,
            )

        if matcher.action == 'TAKE_FROM_CONTENT':
            cover_image = get_cover_image(file)
            return ResolvedMeta(
                cover_image=cover_image if cover_image else default_cover_image,
                description=default_description,
                url=url_computed,
                author=author_name,
                author_email=author_email,
                twitter_handle=twitter_handle,
            )

        if matcher.action == 'STATIC':
            title: str | None = None
            cover_image: Path | None = None
            static_url = meta.default.url if meta.default.url is not None else url_computed
            if matcher.meta_fields is not None:
                if matcher.meta_fields.title is not None:
                    title = matcher.meta_fields.title
                if matcher.meta_fields.image is not None:
                    cover_image = Path(matcher.meta_fields.image)
                if matcher.meta_fields.url is not None:
                    static_url = matcher.meta_fields.url
                if matcher.meta_fields.author_name is not None:
                    author_name = matcher.meta_fields.author_name
                if matcher.meta_fields.author_email is not None:
                    author_email = matcher.meta_fields.author_email
                if matcher.meta_fields.twitter_handle is not None:
                    twitter_handle = matcher.meta_fields.twitter_handle
            return ResolvedMeta(
                title=title,
                description=default_description,
                cover_image=cover_image if cover_image else default_cover_image,
                url=static_url,
                author=author_name,
                author_email=author_email,
                twitter_handle=twitter_handle,
            )

    return ResolvedMeta(twitter_handle=twitter_handle)