"""Shared argument checks for the models package.

Every public function in the package validates its arguments with these helpers
before doing any work, so the checks are written once and raise the same error
types everywhere: ``TypeError`` for a wrong type and ``ValueError`` for a wrong value.
"""

from collections.abc import Collection
from urllib.parse import urlparse


def require_type(name: str, value: object, expected: type | tuple[type, ...]) -> None:
	"""Raise ``TypeError`` unless ``value`` is an instance of ``expected``.

	Args:
		name (str): Argument name, used in the error message.
		value (object): Value to check.
		expected (type | tuple[type, ...]): Accepted type or tuple of types.

	Returns:
		None
	"""

	if not isinstance(value, expected):
		raise TypeError(f"{name} must be {expected}, got {type(value).__name__}")


def require_text(name: str, value: object) -> None:
	"""Raise unless ``value`` is a non-empty string.

	Args:
		name (str): Argument name, used in the error message.
		value (object): Value to check.

	Returns:
		None
	"""

	require_type(name, value, str)

	if not value.strip():
		raise ValueError(f"{name} must not be empty")


def require_http_url(name: str, value: object) -> None:
	"""Raise unless ``value`` is an absolute http or https URL.

	Args:
		name (str): Argument name, used in the error message.
		value (object): Value to check.

	Returns:
		None
	"""

	require_text(name, value)

	parts = urlparse(value)

	if parts.scheme not in ("http", "https") or not parts.netloc:
		raise ValueError(f"{name} must be an absolute http(s) URL, got {value!r}")


def require_choice(name: str, value: object, choices: Collection[str]) -> None:
	"""Raise unless ``value`` is one of ``choices``.

	Args:
		name (str): Argument name, used in the error message.
		value (object): Value to check.
		choices (Collection[str]): Allowed values.

	Returns:
		None
	"""

	require_type(name, value, str)

	if value not in choices:
		raise ValueError(f"{name} must be one of {sorted(choices)}, got {value!r}")


def require_positive_number(name: str, value: object) -> None:
	"""Raise unless ``value`` is an int or float greater than zero.

	Args:
		name (str): Argument name, used in the error message.
		value (object): Value to check.

	Returns:
		None
	"""

	require_type(name, value, (int, float))

	if value <= 0:
		raise ValueError(f"{name} must be greater than zero, got {value!r}")


def require_callable(name: str, value: object) -> None:
	"""Raise ``TypeError`` unless ``value`` is callable.

	Args:
		name (str): Argument name, used in the error message.
		value (object): Value to check.

	Returns:
		None
	"""

	if not callable(value):
		raise TypeError(f"{name} must be callable, got {type(value).__name__}")
