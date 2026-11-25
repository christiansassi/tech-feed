"""Sources for InternLM (Shanghai AI Lab) model releases. The website is a stale JavaScript app; Hugging Face and GitHub carry the releases."""

from models.common.runner import cli
from models.common.sources import github, hf

LABEL = "InternLM"

SOURCES = [
	hf("internlm"),
	github("InternLM"),
]

if __name__ == "__main__":
	cli(__file__, LABEL, SOURCES)
