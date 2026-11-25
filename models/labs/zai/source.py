"""Sources for Z.ai (GLM, Zhipu) model releases. The Chinese homepage shows the newest flagship model first; the news page is corporate and stale, and the docs feed lags behind."""

from models.common.runner import cli
from models.common.sources import hf, html, rss

SOURCES = [
	html("https://www.zhipuai.cn/"),
	rss("https://docs.z.ai/release-notes/new-released/rss.xml"),
	hf("zai-org"),
]

if __name__ == "__main__":
	cli(__file__, SOURCES)
