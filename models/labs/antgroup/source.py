"""Sources for Ant Group Ling model releases (inclusionAI). Hugging Face is ahead of the blog, which lags by months."""

from models.common.runner import cli
from models.common.sources import hf, rss

LABEL = "Ant Group"

SOURCES = [
	hf("inclusionAI"),
	rss("https://www.inclusion-ai.org/blog/rss.xml"),
]

if __name__ == "__main__":
	cli(__file__, LABEL, SOURCES)
