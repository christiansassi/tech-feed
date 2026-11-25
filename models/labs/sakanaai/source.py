"""Sources for Sakana AI model releases. The feed mixes English and Japanese posts."""

from models.common.runner import cli
from models.common.sources import hf, rss

SOURCES = [
	rss("https://sakana.ai/feed.xml"),
	hf("SakanaAI"),
]

if __name__ == "__main__":
	cli(__file__, SOURCES)
