"""Sources for NVIDIA Nemotron model releases."""

from models.common.runner import cli
from models.common.sources import hf, rss

SOURCES = [
	rss("https://developer.nvidia.com/blog/tag/nemotron/feed/"),
	hf("nvidia", search="Nemotron"),
]

if __name__ == "__main__":
	cli(__file__, SOURCES)
