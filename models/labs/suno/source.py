"""Sources for Suno music model releases."""

from models.common.runner import cli
from models.common.sources import rss

LABEL = "Suno"

SOURCES = [
	rss("https://suno.com/blog/rss.xml"),
]

if __name__ == "__main__":
	cli(__file__, LABEL, SOURCES)
