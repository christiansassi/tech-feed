"""Sources for TII (Falcon) model releases."""

from models.common.runner import cli
from models.common.sources import hf, rss

LABEL = "TII"

SOURCES = [
	rss("https://falcon-lm.github.io/blog/index.xml"),
	hf("tiiuae"),
]

if __name__ == "__main__":
	cli(__file__, LABEL, SOURCES)
