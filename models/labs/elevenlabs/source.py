"""Sources for ElevenLabs audio model releases. The docs changelog feed is large (about 2.7 MB)."""

from models.common.runner import cli
from models.common.sources import rss

SOURCES = [
	rss("https://elevenlabs.io/blog/rss.xml"),
	rss("https://elevenlabs.io/docs/changelog.rss"),
]

if __name__ == "__main__":
	cli(__file__, SOURCES)
