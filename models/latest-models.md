## Parameters

```
BASE_URL = https://christiansassi.github.io/tech-feed/models/
LEVEL    = medium    # light | medium | full
LABS     = all       # all, or a comma-separated list of lab names such as: qwen, openai, xiaomi
```

## Task

Find the most recent model released by each AI lab listed on BASE_URL and report it. Use only the JSON files described below. Do not open the article links inside them and do not search the web.

## Steps

1. Fetch `{BASE_URL}index.json`. Its `labs` array has one entry per lab with:
	- `lab`: lab name, such as `qwen`
	- `urls`: the paths of the three files of the lab, relative to BASE_URL, keyed by level (`light`, `medium`, `full`)
2. For every lab in `labs` (or only the labs named in LABS), fetch `{BASE_URL}{urls[LEVEL]}`. Fetch one lab at a time or in parallel; every lab is independent.
3. Each lab file has this shape:
	```
	{
		"lab": "qwen",
		"level": "medium",
		"generated_at": 1795613766,
		"sources": [
			{
				"rank": 1,
				"type": "api",
				"url": "...",
				"fetched_at": 1795613760,
				"status": "ok",
				"error": null,
				"items_dropped": 0,
				"items": [
					{"title": "...", "date": 1794787200, "url": "...", "summary": "..."}
				]
			}
		]
	}
	```
	- `sources` are ordered from the main source (`rank` 1) to the least important. `type` is `api`, `rss` or `html` for the lab's own site and `hf` for its Hugging Face organization.
	- Skip a source whose `status` is not `ok`.
	- `date` is a Unix timestamp in seconds (UTC). When the source gives only the day, it is midnight UTC of that day. It can be `null`.
	- `summary` exists from level `medium` and `body` from level `full`; both can be `null`.
4. In each lab file, keep only the items that announce a new model or a new version of a model made by that lab (language, vision, image, video, audio, speech, embedding, code or any other model). Use the title and, when present, the summary to decide. Discard:
	- research papers, benchmarks and technical reports that do not release a model
	- product features, apps, pricing, API changes, partnerships, events, hiring and company news
	- on Hugging Face (`type` `hf`): datasets, Spaces, quantized or converted copies (GGUF, AWQ, GPTQ, FP8, INT4, MLX, ONNX), adapters and LoRAs, and fine-tunes of models made by other labs
5. Several items can describe the same release: a blog post, a changelog entry and the Hugging Face repositories of its sizes or variants. Treat them as one model, named as the lab names the release (for example `Qwen4-Max`, not `Qwen/Qwen4-Max-Instruct-2611-FP8`). Its date is the date of the lab's own announcement when there is one, otherwise the earliest date among its items.
6. The latest model of a lab is the kept model with the highest `date`. Use a model with `date` `null` only when the lab has no dated model, and then report `date` as `null`.
7. If a lab file cannot be fetched, or no item in it is a model release, report the lab as `null`.

## Output

Reply with one JSON object and nothing else: no prose, no code fence. Use the lab names as keys, in the order of `index.json`. Each value is `null` or an object with:

- `title`: the model name
- `date`: Unix timestamp in seconds, as found in the data (do not convert it)

```
{
	"qwen": {"title": "Qwen4-Max", "date": 1794787200},
	"xiaomi": {"title": "MiMo-V2.6", "date": 1790000000},
	"essentialai": null
}
```
