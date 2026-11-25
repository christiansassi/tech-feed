"""Sources for Essential AI (Rnj) model releases.

Hugging Face is the only source: the research page renders its list with
JavaScript, carries no data in its HTML and has not been updated since early
2026 (Rnj-1.5 is missing from it).
"""

from models.common.runner import cli
from models.common.sources import hf

SOURCES = [
	hf("EssentialAI"),
]

if __name__ == "__main__":
	cli(__file__, SOURCES)
