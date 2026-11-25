"""Sources for Kling (Kuaishou) video model releases."""

from models.common.pages import link_list
from models.common.runner import cli
from models.common.sources import hf, html

SOURCES = [
	html("https://kling.ai/blog", link_list(r"^/blog/(?!$)[^/]+$")),
	hf("KlingTeam"),
]

if __name__ == "__main__":
	cli(__file__, SOURCES)
