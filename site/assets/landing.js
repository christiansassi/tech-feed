/**
 * Landing page runtime for Tech Feed.
 *
 * Render an animated full-screen background with a WebGL fragment shader and
 * show when the feed was last generated. Each page supplies only a GLSL
 * `field()` function in a `<script type="x-shader/x-fragment">` element; this
 * file adds the shared noise helpers, the prism heat palette, the film grain and
 * the dithered banding, then runs the render loop.
 */

const PAGES_ROOT = "https://christiansassi.github.io/tech-feed/";

const RENDER_SCALE = 0.75;

const MAX_PIXEL_RATIO = 1;

const GRAIN_FPS = 24;

const VERTEX_GLSL = `
attribute vec2 aPosition;

void main() {
	gl_Position = vec4(aPosition, 0.0, 1.0);
}
`;

const COMMON_GLSL = `
precision highp float;

uniform vec2 uRes;
uniform float uTime;
uniform float uBands;

float hash12(vec2 p) {
	vec3 p3 = fract(vec3(p.xyx) * 0.1031);
	p3 += dot(p3, p3.yzx + 33.33);
	return fract((p3.x + p3.y) * p3.z);
}

vec2 hash22(vec2 p) {
	vec3 p3 = fract(vec3(p.xyx) * vec3(0.1031, 0.1030, 0.0973));
	p3 += dot(p3, p3.yzx + 33.33);
	return fract((p3.xx + p3.yz) * p3.zy);
}

float noise(vec2 p) {
	vec2 i = floor(p);
	vec2 f = fract(p);
	vec2 u = f * f * (3.0 - 2.0 * f);
	float a = hash12(i);
	float b = hash12(i + vec2(1.0, 0.0));
	float c = hash12(i + vec2(0.0, 1.0));
	float d = hash12(i + vec2(1.0, 1.0));
	return mix(mix(a, b, u.x), mix(c, d, u.x), u.y);
}

float fbm(vec2 p) {
	float value = 0.0;
	float amp = 0.5;
	mat2 rot = mat2(1.6, 1.2, -1.2, 1.6);

	for (int i = 0; i < 5; i++) {
		value += amp * noise(p);
		p = rot * p;
		amp *= 0.5;
	}

	return value;
}

vec3 prism(float t) {
	t = clamp(t, 0.0, 1.0);
	vec3 c = vec3(0.020, 0.020, 0.027);
	c = mix(c, vec3(0.090, 0.043, 0.360), smoothstep(0.00, 0.20, t));
	c = mix(c, vec3(0.200, 0.250, 1.000), smoothstep(0.20, 0.38, t));
	c = mix(c, vec3(1.000, 0.180, 0.760), smoothstep(0.38, 0.55, t));
	c = mix(c, vec3(1.000, 0.420, 0.070), smoothstep(0.55, 0.70, t));
	c = mix(c, vec3(1.000, 0.830, 0.120), smoothstep(0.70, 0.85, t));
	c = mix(c, vec3(0.990, 0.970, 0.920), smoothstep(0.85, 1.00, t));
	return c;
}
`;

const MAIN_GLSL = `
void main() {
	vec2 uv = gl_FragCoord.xy / uRes;
	vec2 p = (gl_FragCoord.xy - 0.5 * uRes) / uRes.y;
	float frame = floor(uTime * ${GRAIN_FPS.toFixed(1)});

	float h = field(uv, p, uTime);

	float calm = smoothstep(0.10, 0.70, length(p * vec2(0.85, 1.45)));
	h *= mix(0.28, 1.0, calm);

	float dither = hash12(gl_FragCoord.xy + frame * vec2(17.31, 41.77)) - 0.5;
	float level = h + dither * 0.14;

	if (uBands > 0.5) {
		level = h + dither * (0.8 / uBands);
		level = (floor(level * uBands) + 0.5) / uBands;
	}

	vec3 color = prism(level);
	float grain = hash12(gl_FragCoord.xy * 1.37 + frame * vec2(91.7, 23.3)) - 0.5;
	color += grain * 0.075;

	gl_FragColor = vec4(color, 1.0);
}
`;

/**
 * Throw a `TypeError` when a value is not an instance of the expected class.
 *
 * @param {string} name Argument name used in the error message.
 * @param {*} value Value to check.
 * @param {Function} type Expected constructor, such as `HTMLCanvasElement`.
 * @returns {void}
 */
function requireInstance(name, value, type) {
	if (!(value instanceof type)) {
		throw new TypeError(`${name} must be a ${type.name}`);
	}
}

/**
 * Throw a `TypeError` for a non-string and a `RangeError` for an empty string.
 *
 * @param {string} name Argument name used in the error message.
 * @param {*} value Value to check.
 * @returns {void}
 */
function requireText(name, value) {
	if (typeof value !== "string") {
		throw new TypeError(`${name} must be a string`);
	}

	if (!value.trim()) {
		throw new RangeError(`${name} must not be empty`);
	}
}

/**
 * Compile one shader stage and return it, throwing with the GLSL log on failure.
 *
 * @param {WebGLRenderingContext} gl WebGL context.
 * @param {number} type `gl.VERTEX_SHADER` or `gl.FRAGMENT_SHADER`.
 * @param {string} source GLSL source code.
 * @returns {WebGLShader} Compiled shader.
 */
function compileShader(gl, type, source) {
	requireInstance("gl", gl, WebGLRenderingContext);
	requireText("source", source);

	const shader = gl.createShader(type);
	gl.shaderSource(shader, source);
	gl.compileShader(shader);

	if (!gl.getShaderParameter(shader, gl.COMPILE_STATUS)) {
		throw new Error(gl.getShaderInfoLog(shader) || "shader compile failed");
	}

	return shader;
}

/**
 * Link the shared vertex shader with a fragment shader built around a page's `field()` function.
 *
 * @param {WebGLRenderingContext} gl WebGL context.
 * @param {string} fieldSource GLSL that defines `float field(vec2 uv, vec2 p, float t)` returning 0 to 1.
 * @returns {WebGLProgram} Linked program.
 */
function createProgram(gl, fieldSource) {
	requireInstance("gl", gl, WebGLRenderingContext);
	requireText("fieldSource", fieldSource);

	const program = gl.createProgram();
	gl.attachShader(program, compileShader(gl, gl.VERTEX_SHADER, VERTEX_GLSL));
	gl.attachShader(program, compileShader(gl, gl.FRAGMENT_SHADER, COMMON_GLSL + fieldSource + MAIN_GLSL));
	gl.linkProgram(program);

	if (!gl.getProgramParameter(program, gl.LINK_STATUS)) {
		throw new Error(gl.getProgramInfoLog(program) || "program link failed");
	}

	return program;
}

/**
 * Start rendering an animated field into a canvas and return a function that stops it.
 *
 * Rendering pauses while the tab is hidden, and a single still frame is drawn
 * when the visitor prefers reduced motion.
 *
 * @param {HTMLCanvasElement} canvas Full-screen canvas.
 * @param {string} fieldSource GLSL that defines the page's `field()` function.
 * @param {number} bands Number of color bands; 0 keeps the gradient continuous.
 * @returns {Function} Call it to stop the animation.
 */
function startField(canvas, fieldSource, bands) {
	requireInstance("canvas", canvas, HTMLCanvasElement);
	requireText("fieldSource", fieldSource);

	if (!Number.isInteger(bands)) {
		throw new TypeError("bands must be an integer");
	}

	if (bands < 0 || bands > 64) {
		throw new RangeError("bands must be between 0 and 64");
	}

	const gl = canvas.getContext("webgl", { antialias: false, premultipliedAlpha: false });

	if (!gl) {
		throw new Error("WebGL is not available");
	}

	const program = createProgram(gl, fieldSource);
	gl.useProgram(program);

	const buffer = gl.createBuffer();
	gl.bindBuffer(gl.ARRAY_BUFFER, buffer);
	gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1, -1, 3, -1, -1, 3]), gl.STATIC_DRAW);

	const position = gl.getAttribLocation(program, "aPosition");
	gl.enableVertexAttribArray(position);
	gl.vertexAttribPointer(position, 2, gl.FLOAT, false, 0, 0);

	const uRes = gl.getUniformLocation(program, "uRes");
	const uTime = gl.getUniformLocation(program, "uTime");
	gl.uniform1f(gl.getUniformLocation(program, "uBands"), bands);

	const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
	const seed = Math.random() * 1000;
	const start = performance.now();
	let frameId = 0;

	/**
	 * Match the drawing buffer to the canvas size, scaled down for speed.
	 *
	 * @returns {void}
	 */
	function resize() {
		const ratio = Math.min(window.devicePixelRatio || 1, MAX_PIXEL_RATIO) * RENDER_SCALE;
		const width = Math.max(1, Math.round(canvas.clientWidth * ratio));
		const height = Math.max(1, Math.round(canvas.clientHeight * ratio));

		if (canvas.width !== width || canvas.height !== height) {
			canvas.width = width;
			canvas.height = height;
			gl.viewport(0, 0, width, height);
		}

		gl.uniform2f(uRes, width, height);
	}

	/**
	 * Draw one frame and schedule the next one unless motion is reduced.
	 *
	 * @param {number} now Timestamp from `requestAnimationFrame`, in milliseconds.
	 * @returns {void}
	 */
	function draw(now) {
		resize();
		gl.uniform1f(uTime, seed + (now - start) / 1000);
		gl.drawArrays(gl.TRIANGLES, 0, 3);

		if (!reduceMotion && !document.hidden) {
			frameId = requestAnimationFrame(draw);
		}
	}

	/**
	 * Resume the loop when the tab becomes visible again.
	 *
	 * @returns {void}
	 */
	function onVisibility() {
		cancelAnimationFrame(frameId);

		if (!document.hidden) {
			frameId = requestAnimationFrame(draw);
		}
	}

	document.addEventListener("visibilitychange", onVisibility);
	window.addEventListener("resize", () => draw(performance.now()));
	frameId = requestAnimationFrame(draw);

	return () => {
		cancelAnimationFrame(frameId);
		document.removeEventListener("visibilitychange", onVisibility);
	};
}

/**
 * Fetch the models index and write its generation time into an element.
 *
 * @param {HTMLElement} element Element that receives the status text.
 * @param {string} indexUrl Absolute URL of `models/index.json`.
 * @returns {Promise<void>} Resolves when the text is written or the fetch failed silently.
 */
async function showStatus(element, indexUrl) {
	requireInstance("element", element, HTMLElement);
	requireText("indexUrl", indexUrl);

	try {
		const response = await fetch(indexUrl, { cache: "no-store" });

		if (!response.ok) {
			return;
		}

		const index = await response.json();
		const generated = new Date(index.generated_at);
		const day = generated.toLocaleDateString("en-US", { month: "long", day: "numeric", year: "numeric", timeZone: "UTC" });
		const time = generated.toLocaleTimeString("en-GB", { hour: "2-digit", minute: "2-digit", timeZone: "UTC" });

		element.textContent = `${day} · ${time} UTC`;
	} catch {
		element.textContent = "";
	}
}

/**
 * Return the site root: the current folder on GitHub Pages, the public site elsewhere.
 *
 * @returns {string} Absolute URL ending with a slash.
 */
function siteRoot() {
	if (location.hostname.endsWith("github.io")) {
		return new URL("./", document.baseURI).href;
	}

	return PAGES_ROOT;
}

/**
 * Wire up the page: start the background shader and fill in the feed status.
 *
 * @returns {void}
 */
function boot() {
	const canvas = document.querySelector("canvas.field");
	const shader = document.getElementById(canvas.dataset.shader);
	const bands = Number.parseInt(canvas.dataset.bands || "0", 10);

	try {
		startField(canvas, shader.textContent, bands);
	} catch (error) {
		canvas.hidden = true;
		document.body.classList.add("no-webgl");
		console.warn("Background disabled:", error);
	}

	const stamp = document.querySelector(".stamp");

	if (stamp) {
		showStatus(stamp, new URL("models/index.json", siteRoot()).href);
	}
}

document.addEventListener("DOMContentLoaded", boot);
