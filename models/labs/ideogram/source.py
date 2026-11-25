"""Sources for Ideogram image model releases."""

from models.common.pages import link_list
from models.common.runner import cli
from models.common.sources import hf, html

LABEL = "Ideogram"

SOURCES = [
	html("https://ideogram.ai/blog/", link_list(r"^/blog/[^/]+/?$")),
	hf("ideogram-ai"),
]

if __name__ == "__main__":
	cli(__file__, LABEL, SOURCES)
