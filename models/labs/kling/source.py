"""Sources for Kling (Kuaishou) video model releases."""

from models.common.runner import cli
from models.common.sources import hf, html

SOURCES = [
	html("https://kling.ai/blog"),
	hf("KlingTeam"),
]

if __name__ == "__main__":
	cli(__file__, SOURCES)
