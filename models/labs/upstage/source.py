"""Sources for Upstage (Solar) model releases. The blog also carries many industry posts."""

from models.common.runner import cli
from models.common.sources import hf, html

SOURCES = [
	html("https://www.upstage.ai/blog"),
	hf("upstage"),
]

if __name__ == "__main__":
	cli(__file__, SOURCES)
