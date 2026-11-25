"""Sources for Tencent Hunyuan model releases. The blog is a JavaScript app; its post list comes from this API."""

from models.common.runner import cli
from models.common.sources import api, hf

SOURCES = [
	api("https://api.hunyuan.tencent.com/api/blog/publicList", method="POST", json_body={"pageNum": 1, "pageSize": 20}),
	hf("tencent", search="Hunyuan"),
	hf("tencent", search="Hy"),
]

if __name__ == "__main__":
	cli(__file__, SOURCES)
