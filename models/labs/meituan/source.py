"""Sources for Meituan LongCat model releases. The LongCat websites are JavaScript apps; Hugging Face, the Chinese tech blog feed and GitHub carry the releases."""

from models.common.runner import cli
from models.common.sources import github, hf, rss

LABEL = "Meituan"

SOURCES = [
	hf("meituan-longcat"),
	rss("https://tech.meituan.com/feed/"),
	github("meituan-longcat"),
]

if __name__ == "__main__":
	cli(__file__, LABEL, SOURCES)
