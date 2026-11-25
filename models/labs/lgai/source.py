"""Sources for LG AI Research (EXAONE) model releases. The blog is rendered with JavaScript; its post list comes from this API."""

from models.common.runner import cli
from models.common.sources import api, hf

SOURCES = [
	api("https://www.lgresearch.ai/api/board/blog/list?pg=1&pgSz=10&schExpsYn=Y&schLangTp=en"),
	hf("LGAI-EXAONE"),
]

if __name__ == "__main__":
	cli(__file__, SOURCES)
