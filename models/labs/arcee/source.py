"""Sources for Arcee AI model releases."""

from models.common.runner import cli
from models.common.sources import hf, html

SOURCES = [
	html("https://www.arcee.ai/blog"),
	hf("arcee-ai"),
]

if __name__ == "__main__":
	cli(__file__, SOURCES)
