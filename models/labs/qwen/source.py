"""Sources for Qwen (Alibaba) model releases.

The qwen.ai research page is rendered with JavaScript; its article list comes
from the retrieval API used below. Hugging Face lists the open-weight releases.
"""

from models.common.runner import cli
from models.common.sources import api, hf

SOURCES = [
	api("https://qwen.ai/api/v2/article/retrieval?type=qwen_ai&language=en-US"),
	hf("Qwen"),
]

if __name__ == "__main__":
	cli(__file__, SOURCES)
