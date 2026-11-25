"""Sources for Runway video model releases."""

from models.common.runner import cli
from models.common.sources import hf, html

SOURCES = [
	html("https://runway.com/research"),
	html("https://runway.com/changelog"),
	hf("runwayml"),
]

if __name__ == "__main__":
	cli(__file__, SOURCES)
