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
    title: str | None = None
    description: str | None = None
    cover_image: Path | None = None
    url: str | None = None
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

    twitter_handle = meta.default.twitter_handle
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
                twitter_handle=meta.default.twitter_handle,
            )

        if matcher.action == 'TAKE_FROM_CONTENT':
            cover_image = get_cover_image(file)
            return ResolvedMeta(
                cover_image=cover_image if cover_image else default_cover_image,
                description=default_description,
                url=urljoin(base_href, f'{file.name}.html'),
                twitter_handle=twitter_handle,
            )

        if matcher.action == 'STATIC':
            title: str | None = None
            cover_image: Path | None = None
            url = meta.default.url
            if matcher.meta_fields is not None:
                if matcher.meta_fields.title is not None:
                    title = matcher.meta_fields.title
                if matcher.meta_fields.image is not None:
                    cover_image = Path(matcher.meta_fields.image)
                if matcher.meta_fields.url is not None:
                    url = matcher.meta_fields.url
                if matcher.meta_fields.twitter_handle is not None:
                    twitter_handle = matcher.meta_fields.twitter_handle
            return ResolvedMeta(
                title=title,
                description=default_description,
                cover_image=cover_image if cover_image else default_cover_image,
                url=url,
                twitter_handle=twitter_handle,
            )

    return ResolvedMeta(twitter_handle=twitter_handle)