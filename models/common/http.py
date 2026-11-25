"""HTTP client setup for every source fetch.

Build primp clients that send a random desktop browser User-Agent from
fake-useragent, and send requests that fail loudly on HTTP errors so the runner
can record the status code of each source. A request that fails with a network
error, HTTP 429 or a 5xx status is retried once.
"""

import time

import primp
from fake_useragent import UserAgent

from models.common.validation import require_choice, require_http_url, require_positive_number, require_type

TIMEOUT_SECONDS = 30

ATTEMPTS = 2

RETRY_DELAY_SECONDS = 3

RETRY_STATUSES = {429, 500, 502, 503, 504}

METHODS = ("GET", "POST")

_USER_AGENTS = UserAgent(platforms="desktop")


class FetchError(Exception):
	"""Error raised when a source cannot be fetched or parsed.

	Attributes:
		http_status (int | None): HTTP status code when the server answered, else None.
	"""

	def __init__(self, message: str, http_status: int | None = None) -> None:
		"""Create the error.

		Args:
			message (str): Human-readable cause.
			http_status (int | None): HTTP status code when the server answered.

		Returns:
			None
		"""

		super().__init__(message)
		self.http_status = http_status


def new_client(timeout: float = TIMEOUT_SECONDS) -> primp.Client:
	"""Return a primp client with a random desktop User-Agent.

	Args:
		timeout (float): Total timeout in seconds for each request.

	Returns:
		primp.Client: Client that follows redirects.
	"""

	require_positive_number("timeout", timeout)

	headers = {
		"User-Agent": _USER_AGENTS.random,
		"Accept-Language": "en-US,en;q=0.9",
	}

	return primp.Client(headers=headers, follow_redirects=True, timeout=timeout)


def send(client: primp.Client, url: str, method: str = "GET", json_body: dict | None = None, headers: dict | None = None) -> primp.Response:
	"""Send one request and return the response, raising on transport or HTTP errors.

	Args:
		client (primp.Client): Client from ``new_client``.
		url (str): Absolute http(s) URL.
		method (str): ``"GET"`` or ``"POST"``.
		json_body (dict | None): JSON body for a POST request.
		headers (dict | None): Extra headers for this request only.

	Returns:
		primp.Response: Response with a status code below 400.
	"""

	require_type("client", client, primp.Client)
	require_http_url("url", url)
	require_choice("method", method, METHODS)

	if json_body is not None:
		require_type("json_body", json_body, dict)

	if headers is not None:
		require_type("headers", headers, dict)

	for attempt in range(1, ATTEMPTS + 1):
		last = attempt == ATTEMPTS

		try:
			response = client.request(method, url, json=json_body, headers=headers)
		except primp.PrimpError as exc:

			if last:
				raise FetchError(f"{type(exc).__name__}: {exc}") from exc

			time.sleep(RETRY_DELAY_SECONDS)
			continue

		if response.status_code in RETRY_STATUSES and not last:
			time.sleep(RETRY_DELAY_SECONDS)
			continue

		if response.status_code >= 400:
			raise FetchError(f"HTTP {response.status_code}", response.status_code)

		return response
