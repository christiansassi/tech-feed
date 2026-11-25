"""Sources for Cohere (Command) model releases. The docs changelog lists model launches."""

from models.common.pages import link_list
from models.common.runner import cli
from models.common.sources import hf, html, rss

SOURCES = [
	rss("https://docs.cohere.com/changelog.rss"),
	html("https://cohere.com/blog", link_list(r"^/blog/[^/]+$")),
	hf("CohereLabs"),
]

if __name__ == "__main__":
	cli(__file__, SOURCES)
