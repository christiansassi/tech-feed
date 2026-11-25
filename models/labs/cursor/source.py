"""Sources for Cursor (Composer) model releases. Model launches appear in the changelog feed; cursor.com/atom.xml is stale and not used."""

from models.common.pages import link_list
from models.common.runner import cli
from models.common.sources import html, rss

SOURCES = [
	rss("https://cursor.com/changelog/rss.xml"),
	html("https://cursor.com/blog", link_list(r"^/(?:en-US/)?blog/[^/]+$")),
]

if __name__ == "__main__":
	cli(__file__, SOURCES)
