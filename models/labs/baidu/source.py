"""Sources for Baidu ERNIE model releases."""

from models.common.runner import cli
from models.common.sources import hf, html

SOURCES = [
	html("https://ernie.baidu.com/research/"),
	hf("baidu"),
]

if __name__ == "__main__":
	cli(__file__, SOURCES)
