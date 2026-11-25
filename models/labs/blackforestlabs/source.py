"""Sources for Black Forest Labs (FLUX) model releases."""

from models.common.runner import cli
from models.common.sources import hf, html

SOURCES = [
	html("https://bfl.ai/blog"),
	hf("black-forest-labs"),
]

if __name__ == "__main__":
	cli(__file__, SOURCES)
