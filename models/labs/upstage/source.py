"""Sources for Upstage (Solar) model releases. The blog also carries many industry posts."""

from models.common.pages import link_list
from models.common.runner import cli
from models.common.sources import hf, html

LABEL = "Upstage"

SOURCES = [
	html("https://www.upstage.ai/blog", link_list(r"^/blog/en/[^/]+$")),
	hf("upstage"),
]

if __name__ == "__main__":
	cli(__file__, LABEL, SOURCES)
