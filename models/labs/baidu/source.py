"""Sources for Baidu ERNIE model releases."""

from models.common.pages import link_list
from models.common.runner import cli
from models.common.sources import hf, html

SOURCES = [
	html("https://ernie.baidu.com/research/", link_list(r"^/(?:research/posts|release)/[^/]+")),
	hf("baidu"),
]

if __name__ == "__main__":
	cli(__file__, SOURCES)
