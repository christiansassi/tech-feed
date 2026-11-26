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

/**
 * Number the month headers and rows of a list for the cascade entrance.
 *
 * Each month gets its position (`--g`) and each element its position inside
 * its month (`--j`); `section.css` turns them into animation delays, so the
 * months open one after the other and their rows follow.
 *
 * @param {HTMLElement} container List container.
 * @returns {void}
 */
function cascade(container) {
	requireInstance("container", container, HTMLElement);

	let group = -1;
	let position = 0;

	for (const node of container.querySelectorAll(".month, .row")) {

		if (node.classList.contains("month")) {
			group += 1;
			position = 0;
		}

		node.style.setProperty("--g", group);
		node.style.setProperty("--j", position);
		position += 1;
	}

	container.classList.add("cascade");
}

/**
 * Fill every `.updated` element with the time its index file was generated.
 *
 * The index is rewritten each time the sources are read, so this is the time of
 * the last data check. Elements whose index cannot be read are removed. The line
 * that holds them stays hidden until then, so it appears once and complete.
 *
 * @returns {Promise<void>} Resolves when every element is filled or removed.
 */
async function showUpdated() {
	for (const node of document.querySelectorAll(".updated[data-index]")) {
		const line = node.closest(".meta");
		const index = await getJson(node.dataset.index);

		if (!index || !Number.isInteger(index.generated_at)) {
			node.remove();
		} else {
			const when = new Date(index.generated_at * 1000);
			const day = when.toLocaleDateString("en-US", {month: "short", day: "numeric", timeZone: "UTC"});
			const time = when.toLocaleTimeString("en-GB", {hour: "2-digit", minute: "2-digit", timeZone: "UTC"});

			node.textContent = `Updated ${day}, ${time} UTC`;
		}

		if (line) {
			line.classList.add("ready");
		}
	}
}

/**
 * Fill the chips of the Following layer, in alphabetical order, and the count on its button.
 *
 * Followed entries get the `on` class; the button shows how many there are,
 * followed by `noun`. With no entries (the index could not be read) the
 * "Following" part of the update line is removed instead.
 *
 * @param {?Array<{label: string, on: boolean, icon: ?Node}>} entries Chips to show, or null when the index is missing.
 * @param {string} noun Plural word after the count, such as "labs".
 * @returns {void}
 */
function renderFollowing(entries, noun) {
	if (entries !== null && !Array.isArray(entries)) {
		throw new TypeError("entries must be an array or null");
	}

	requireText("noun", noun);

	const trigger = document.querySelector(".follow-trigger");
	const chips = document.querySelector(".follow-layer .chips");

	if (!trigger || !chips) {
		return;
	}

	if (entries === null) {
		trigger.closest(".following").remove();
		return;
	}

	const sorted = entries.slice().sort((a, b) => a.label.localeCompare(b.label, "en", {sensitivity: "base"}));

	sorted.forEach((entry, position) => {
		const chip = element("span", entry.on ? "chip on" : "chip");

		chip.style.setProperty("--k", position);

		if (entry.icon) {
			chip.append(entry.icon);
		}

		chip.append(element("span", "", entry.label));
		chips.append(chip);
	});

	trigger.textContent = `${entries.filter((entry) => entry.on).length} ${noun}`;
	trigger.closest(".following").classList.remove("pending");
}

/**
 * Open or close the Following layer, moving the focus into it and back to the button.
 *
 * @param {boolean} open Whether the layer is shown.
 * @returns {void}
 */
function setFollowingOpen(open) {
	if (typeof open !== "boolean") {
		throw new TypeError("open must be a boolean");
	}

	const trigger = document.querySelector(".follow-trigger");
	const layer = document.querySelector(".follow-layer");

	if (!trigger || !layer || layer.classList.contains("open") === open) {
		return;
	}

	layer.classList.toggle("open", open);
	trigger.setAttribute("aria-expanded", String(open));

	(open ? layer : trigger).focus({preventScroll: true});
}

/**
 * Attach the listeners of the Following layer: the button toggles it, and Escape or a click anywhere but a link closes it.
 *
 * @returns {void}
 */
function bindFollowing() {
	const trigger = document.querySelector(".follow-trigger");
	const layer = document.querySelector(".follow-layer");

	if (!trigger || !layer) {
		return;
	}

	trigger.addEventListener("click", () => setFollowingOpen(trigger.getAttribute("aria-expanded") !== "true"));

	layer.addEventListener("click", (event) => {

		if (!event.target.closest("a")) {
			setFollowingOpen(false);
		}
	});

	document.addEventListener("keydown", (event) => {

		if (event.key === "Escape") {
			setFollowingOpen(false);
		}
	});
}

document.addEventListener("DOMContentLoaded", showUpdated);
