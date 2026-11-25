"""Sources for Nous Research (Hermes) model releases. The releases page labels each entry as MODEL, AGENT or PAPER."""

from models.common.runner import cli
from models.common.sources import hf, html

SOURCES = [
	html("https://nousresearch.com/releases"),
	hf("NousResearch"),
]

if __name__ == "__main__":
	cli(__file__, SOURCES)
