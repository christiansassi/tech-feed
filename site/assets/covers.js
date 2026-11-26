/**
 * Generated covers for the News cards.
 *
 * Every news item gets a square abstract image drawn with WebGL in one of the
 * styles of `cover-styles.js` (gradients, pixel fields, stripes, organic
 * textures, collages, tiles). The style, the
 * palette and the noise seed come from a hash of the item's key, usually its
 * link, so the same item always gets the same cover. One hidden canvas renders
 * the covers one after another and each image is cached as an object URL. Load
 * after `landing.js`, which provides `compileShader`, `VERTEX_GLSL` and the
 * argument checks, and after `cover-styles.js`, which defines `COVER_STYLES`.
 */

const COVER_SIZE = 384;

// Palettes from dark to light, as 0-255 RGB; ramp() in the shaders runs through the four colors in order.
const COVER_PALETTES = [
	[[11, 11, 42], [58, 43, 216], [255, 61, 110], [255, 209, 102]],
	[[240, 113, 103], [246, 167, 163], [181, 201, 154], [106, 153, 78]],
	[[26, 16, 51], [255, 46, 136], [255, 159, 28], [232, 255, 89]],
	[[6, 42, 58], [31, 182, 255], [124, 245, 198], [254, 243, 199]],
	[[149, 184, 209], [184, 224, 210], [252, 213, 206], [255, 181, 167]],
	[[43, 10, 61], [181, 23, 158], [247, 37, 133], [255, 214, 165]],
	[[10, 15, 60], [37, 65, 178], [155, 246, 255], [253, 255, 182]],
	[[18, 32, 24], [46, 139, 87], [255, 95, 109], [255, 195, 160]],
];

const COVER_PRELUDE = `
precision highp float;

uniform vec2 uResolution;
uniform vec4 uSeed;
uniform vec3 uPalette[4];

float hash(vec2 p) {
	p = fract(p * vec2(123.34, 456.21));
	p += dot(p, p + 45.32);
	return fract(p.x * p.y);
}

float noise(vec2 p) {
	vec2 i = floor(p);
	vec2 f = fract(p);
	vec2 u = f * f * (3.0 - 2.0 * f);
	return mix(mix(hash(i), hash(i + vec2(1.0, 0.0)), u.x), mix(hash(i + vec2(0.0, 1.0)), hash(i + vec2(1.0, 1.0)), u.x), u.y);
}

float fbm(vec2 p) {
	float value = 0.0;
	float amplitude = 0.5;

	for (int i = 0; i < 5; i++) {
		value += amplitude * noise(p);
		p = p * 2.03 + 17.1;
		amplitude *= 0.5;
	}

	return value;
}

vec3 ramp(float t) {
	t = clamp(t, 0.0, 1.0) * 3.0;

	if (t < 1.0) {
		return mix(uPalette[0], uPalette[1], t);
	}

	if (t < 2.0) {
		return mix(uPalette[1], uPalette[2], t - 1.0);
	}

	return mix(uPalette[2], uPalette[3], t - 2.0);
}

float grain(vec2 p) {
	return hash(p * 1.7 + uSeed.xy * 100.0) - 0.5;
}

vec3 voronoi(vec2 p) {
	vec2 i = floor(p);
	vec2 f = fract(p);
	float first = 8.0;
	float second = 8.0;
	float id = 0.0;

	for (int y = -1; y <= 1; y++) {
		for (int x = -1; x <= 1; x++) {
			vec2 g = vec2(float(x), float(y));
			vec2 o = vec2(hash(i + g), hash(i + g + 19.7));
			float d = length(g + o - f);

			if (d < first) {
				second = first;
				first = d;
				id = hash(i + g + 3.1);
			} else if (d < second) {
				second = d;
			}
		}
	}

	return vec3(first, second, id);
}

float bayer2(vec2 a) {
	a = floor(a);
	return fract(dot(a, vec2(0.5, a.y * 0.75)));
}

float bayer4(vec2 a) {
	return bayer2(0.5 * a) * 0.25 + bayer2(a);
}

vec3 cover(vec2 uv);

void main() {
	gl_FragColor = vec4(cover(gl_FragCoord.xy / uResolution), 1.0);
}
`;

const COVER_STYLE_NAMES = Object.keys(COVER_STYLES);

let coverRenderer = null;

const coverCache = new Map();

let coverQueue = Promise.resolve();

/**
 * Return a 32-bit FNV-1a hash of a string.
 *
 * @param {string} text Text to hash, such as a link.
 * @returns {number} Unsigned 32-bit hash.
 */
function coverHash(text) {
	requireText("text", text);

	let value = 2166136261;

	for (const char of text) {
		value = Math.imul(value ^ char.codePointAt(0), 16777619);
	}

	return value >>> 0;
}

/**
 * Return a seeded random generator (mulberry32) whose values run from 0 to 1.
 *
 * @param {number} seed Unsigned 32-bit seed.
 * @returns {function(): number} Generator; each call returns the next value.
 */
function coverRandom(seed) {
	if (!Number.isInteger(seed)) {
		throw new TypeError("seed must be an integer");
	}

	return () => {
		seed = (seed + 0x6d2b79f5) >>> 0;

		let t = Math.imul(seed ^ (seed >>> 15), seed | 1);

		t ^= t + Math.imul(t ^ (t >>> 7), t | 61);

		return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
	};
}

/**
 * Return the style, palette and noise seed of the cover of a key.
 *
 * @param {string} key Stable identifier of the item, usually its link.
 * @returns {{style: string, palette: number[][], seed: number[]}} Cover recipe; the same key always gives the same recipe.
 */
function coverRecipe(key) {
	requireText("key", key);

	const next = coverRandom(coverHash(key));
	const style = COVER_STYLE_NAMES[Math.floor(next() * COVER_STYLE_NAMES.length)];
	const palette = COVER_PALETTES[Math.floor(next() * COVER_PALETTES.length)];

	return {style, palette, seed: [next(), next(), next(), next()]};
}

/**
 * Create the hidden canvas, the WebGL context and one program per style.
 *
 * @returns {{canvas: HTMLCanvasElement, gl: WebGLRenderingContext, programs: Object<string, WebGLProgram>}} Renderer shared by every cover.
 */
function createCoverRenderer() {
	const canvas = document.createElement("canvas");

	canvas.width = canvas.height = COVER_SIZE;

	const gl = canvas.getContext("webgl", {preserveDrawingBuffer: true, antialias: false});

	if (!gl) {
		throw new Error("WebGL is not available");
	}

	const buffer = gl.createBuffer();

	gl.bindBuffer(gl.ARRAY_BUFFER, buffer);
	gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1, -1, 3, -1, -1, 3]), gl.STATIC_DRAW);

	const programs = {};

	for (const [name, source] of Object.entries(COVER_STYLES)) {
		const program = gl.createProgram();

		gl.attachShader(program, compileShader(gl, gl.VERTEX_SHADER, VERTEX_GLSL));
		gl.attachShader(program, compileShader(gl, gl.FRAGMENT_SHADER, COVER_PRELUDE + source));
		gl.linkProgram(program);

		if (!gl.getProgramParameter(program, gl.LINK_STATUS)) {
			throw new Error(gl.getProgramInfoLog(program) || `program ${name} failed to link`);
		}

		programs[name] = program;
	}

	return {canvas, gl, programs};
}

/**
 * Draw the cover of a recipe and return it as a JPEG blob.
 *
 * @param {{style: string, palette: number[][], seed: number[]}} recipe Recipe from `coverRecipe`.
 * @returns {Promise<Blob>} Encoded image.
 */
function drawCover(recipe) {
	if (!recipe || !COVER_STYLES[recipe.style]) {
		throw new RangeError("recipe must name a known style");
	}

	coverRenderer = coverRenderer || createCoverRenderer();

	const {canvas, gl, programs} = coverRenderer;
	const program = programs[recipe.style];
	const position = gl.getAttribLocation(program, "aPosition");

	gl.useProgram(program);
	gl.enableVertexAttribArray(position);
	gl.vertexAttribPointer(position, 2, gl.FLOAT, false, 0, 0);
	gl.viewport(0, 0, COVER_SIZE, COVER_SIZE);
	gl.uniform2f(gl.getUniformLocation(program, "uResolution"), COVER_SIZE, COVER_SIZE);
	gl.uniform4fv(gl.getUniformLocation(program, "uSeed"), recipe.seed);
	gl.uniform3fv(gl.getUniformLocation(program, "uPalette"), recipe.palette.flat().map((channel) => channel / 255));
	gl.drawArrays(gl.TRIANGLES, 0, 3);

	return new Promise((resolve, reject) => canvas.toBlob((blob) => (blob ? resolve(blob) : reject(new Error("canvas.toBlob returned nothing"))), "image/jpeg", 0.88));
}

/**
 * Return the URL of the cover of a key, drawing it the first time.
 *
 * Covers are drawn one at a time on the shared canvas and cached for the page's lifetime.
 *
 * @param {string} key Stable identifier of the item, usually its link.
 * @returns {Promise<string>} Object URL of the JPEG cover.
 */
function coverUrl(key) {
	requireText("key", key);

	if (!coverCache.has(key)) {
		const result = coverQueue.then(async () => URL.createObjectURL(await drawCover(coverRecipe(key))));

		coverQueue = result.catch(() => {});
		coverCache.set(key, result);
	}

	return coverCache.get(key);
}
