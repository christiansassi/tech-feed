/**
 * Helpers shared by the section pages (Models, Conferences): dates, elements,
 * JSON downloads and list rows. Load after `landing.js`, which provides the
 * argument checks, and before the script of the page.
 */

const DAY_SECONDS = 86400;

/**
 * Return the month heading of a Unix timestamp.
 *
 * @param {number} seconds Unix timestamp in seconds.
 * @returns {string} Month and year in UTC, such as "November 2026".
 */
function monthOf(seconds) {
	if (!Number.isInteger(seconds)) {
		throw new TypeError("seconds must be an integer");
	}

	return new Date(seconds * 1000).toLocaleDateString("en-US", {month: "long", year: "numeric", timeZone: "UTC"});
}

/**
 * Create an element with a class name and optional text.
 *
 * @param {string} tag Tag name.
 * @param {string} className Class attribute.
 * @param {string} [text] Text content.
 * @returns {HTMLElement} New element.
 */
function element(tag, className, text) {
	requireText("tag", tag);

	const node = document.createElement(tag);

	node.className = className;

	if (text !== undefined) {
		node.textContent = text;
	}

	return node;
}

/**
 * Download a JSON file, returning null when it is missing or invalid.
 *
 * @param {string} url Absolute or page-relative URL.
 * @returns {Promise<?object>} Parsed JSON, or null.
 */
async function getJson(url) {
	requireText("url", url);

	try {
		const response = await fetch(url, {cache: "no-store"});

		return response.ok ? await response.json() : null;
	} catch {
		return null;
	}
}

/**
 * Create a list row: a link that opens in a new tab when there is a URL, a plain block otherwise.
 *
 * @param {?string} url Target of the row, or null.
 * @returns {HTMLElement} Row element with the `row` class.
 */
function rowElement(url) {
	if (url !== null && url !== undefined && typeof url !== "string") {
		throw new TypeError("url must be a string or null");
	}

	const row = element(url ? "a" : "div", "row");

	if (url) {
		row.href = url;
		row.target = "_blank";
		row.rel = "noopener";
	}

	return row;
}
