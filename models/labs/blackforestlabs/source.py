"""Sources for Black Forest Labs (FLUX) model releases."""

from models.common.pages import link_list
from models.common.runner import cli
from models.common.sources import hf, html

LABEL = "Black Forest Labs"

SOURCES = [
	html("https://bfl.ai/blog", link_list(r"^/blog/[^/]+$")),
	hf("black-forest-labs"),
]

if __name__ == "__main__":
	cli(__file__, LABEL, SOURCES)
