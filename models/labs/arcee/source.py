"""Sources for Arcee AI model releases."""

from models.common.pages import link_list
from models.common.runner import cli
from models.common.sources import hf, html

LABEL = "Arcee AI"

SOURCES = [
	html("https://www.arcee.ai/blog", link_list(r"^/blog/[^/]+$")),
	hf("arcee-ai"),
]

if __name__ == "__main__":
	cli(__file__, LABEL, SOURCES)
