"""Sources for Xiaomi MiMo model releases. Hugging Face is the main signal; the blog list has no dates."""

from models.common.runner import cli
from models.common.sources import hf, html

SOURCES = [
	hf("XiaomiMiMo"),
	html("https://mimo.xiaomi.com/"),
]

if __name__ == "__main__":
	cli(__file__, SOURCES)
