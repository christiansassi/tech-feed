/**
 * Cover styles for the News cards, one GLSL `cover()` function per style.
 *
 * Each function receives the pixel position `uv` (0 to 1) and draws with the
 * helpers of the prelude in `covers.js`: `hash`, `noise`, `fbm`, `voronoi`,
 * `bayer4`, `grain` and `ramp`, which runs through the four colors of the
 * palette from dark to light. `uSeed` holds four values from 0 to 1 that vary
 * the drawing per news item. The styles are original code, grouped in families
 * after the kinds of generators on playgrnd.tools. Load before `covers.js`.
 */

const COVER_STYLES = {
	// Soft gradients and washes.
	aura: `
vec3 cover(vec2 uv) {
	vec2 p = uv * 1.6 + uSeed.xy * 10.0;
	vec2 q = vec2(fbm(p), fbm(p + vec2(5.2, 1.3)));
	vec2 r = vec2(fbm(p + 3.0 * q + vec2(1.7, 9.2)), fbm(p + 3.0 * q + vec2(8.3, 2.8)));

	return ramp(smoothstep(0.2, 0.8, fbm(p + 2.5 * r))) + grain(gl_FragCoord.xy) * 0.06;
}
`,
	mist: `
vec3 cover(vec2 uv) {
	vec2 p = vec2(uv.x * 3.0 + uSeed.x * 20.0, uv.y * 0.35 + uSeed.y * 10.0);
	float t = fbm(p + vec2(fbm(p * 1.5), 0.0) * 0.8);
	float streak = noise(vec2(uv.x * 40.0 + uSeed.z * 50.0, uv.y * 2.0));

	return ramp(smoothstep(0.25, 0.75, t * 0.85 + streak * 0.15)) + grain(gl_FragCoord.xy) * 0.08;
}
`,
	sear: `
vec3 cover(vec2 uv) {
	float row = floor(uv.y * 48.0);
	float shift = (hash(vec2(row, uSeed.x * 91.0)) - 0.5) * 0.25 * step(0.6, hash(vec2(row * 0.7, uSeed.y * 37.0)));
	vec2 p = vec2((uv.x + shift) * 2.2, uv.y * 3.0) + uSeed.zw * 20.0;
	float t = fbm(p + fbm(p * 2.0) * 0.6);

	return ramp(floor(smoothstep(0.25, 0.75, t) * 6.0) / 5.0);
}
`,
	pane: `
vec3 cover(vec2 uv) {
	float row = floor(uv.y * 3.0);
	float columns = floor(1.0 + hash(vec2(row, uSeed.x * 13.0)) * 4.0);
	vec2 cell = vec2(floor(uv.x * columns), row);
	vec2 f = vec2(fract(uv.x * columns), fract(uv.y * 3.0));
	float angle = hash(cell + uSeed.yz * 7.0) * 6.2832;
	float along = dot(f - 0.5, vec2(cos(angle), sin(angle))) + 0.5;
	float offset = hash(cell * 1.3 + uSeed.w * 5.0);

	return ramp(offset * 0.5 + along * 0.5);
}
`,
	benday: `
vec3 cover(vec2 uv) {
	float cells = 52.0;
	vec2 grid = uv * cells;
	vec2 center = (floor(grid) + 0.5) / cells;
	vec2 p = center * 1.8 + uSeed.xy * 10.0;
	float t = fbm(p + fbm(p * 1.7) * 1.2);
	float radius = 0.12 + 0.42 * smoothstep(0.2, 0.8, t);
	float spot = smoothstep(radius, radius - 0.08, length(fract(grid) - 0.5));

	return mix(ramp(0.05) * 0.8, ramp(0.3 + t * 0.7), spot);
}
`,
	hiss: `
vec3 cover(vec2 uv) {
	float snow = hash(floor(gl_FragCoord.xy / 2.0) + uSeed.xy * 77.0);
	float band = fbm(vec2(uv.y * 6.0, uSeed.z * 10.0));
	float roll = step(0.85, fract(uv.y * 3.0 + uSeed.w)) * 0.25;

	return ramp(floor(clamp(snow * 0.55 + band * 0.7 - 0.15 + roll, 0.0, 1.0) * 5.0) / 4.0);
}
`,

	// Pixel fields.
	prism: `
vec3 cover(vec2 uv) {
	float n = 24.0;
	vec2 id = floor(uv * n) / n;
	float edge = 0.5 + (fbm(vec2(id.y * 3.0, uSeed.x * 10.0)) - 0.5) * 0.7;
	float jitter = hash(id * n + uSeed.yz * 50.0) - 0.5;
	float t = clamp(0.5 - (id.x - edge) * 3.0 + jitter * 0.35, 0.0, 1.0);

	if (t > 0.97) {
		return vec3(0.95, 0.94, 0.9);
	}

	if (t < 0.05) {
		return vec3(0.03, 0.03, 0.05);
	}

	return ramp(t);
}
`,
	oddgrid: `
vec3 cover(vec2 uv) {
	float n = 6.0;
	vec2 id = floor(uv * n);
	vec2 f = fract(uv * n);
	float h = hash(id + uSeed.xy * 31.0);
	float k = hash(id * 1.7 + uSeed.zw * 17.0);
	float m = step(f.x, f.y);

	if (k < 0.25) {
		m = step(0.5, f.x);
	} else if (k < 0.5) {
		m = step(length(f - 0.5), 0.38);
	} else if (k < 0.75) {
		m = step(0.5, mod(floor(f.x * 4.0) + floor(f.y * 4.0), 2.0));
	}

	return mix(ramp(h), ramp(fract(h + 0.5)), m);
}
`,
	quilt: `
vec3 cover(vec2 uv) {
	float n = 32.0;
	vec2 id = floor(uv * n);
	float t = sin(id.x * 0.35 + uSeed.x * 6.0) + sin(id.y * 0.4 + uSeed.y * 6.0) + sin((id.x + id.y) * 0.2 + uSeed.z * 6.0);
	float level = floor((t / 6.0 + 0.5) * 5.0) / 4.0;
	vec2 block = mod(id, 8.0);
	float seam = clamp(step(block.x, 0.0) + step(block.y, 0.0), 0.0, 1.0);

	return mix(ramp(level), ramp(1.0 - level) * 0.9, seam * 0.6);
}
`,
	totem: `
vec3 cover(vec2 uv) {
	float n = 16.0;
	vec2 id = floor(uv * n);
	float mirrored = min(id.x, n - 1.0 - id.x);
	float band = floor(id.y / 4.0);
	vec3 background = ramp(0.1 + 0.2 * hash(vec2(band, uSeed.z)));
	vec3 figure = ramp(0.55 + 0.45 * hash(vec2(band + 3.0, uSeed.w)));

	return mix(background, figure, step(0.35 + 0.35 * (mirrored / n), hash(vec2(mirrored, id.y) + uSeed.xy * 40.0)));
}
`,
	bloom: `
vec3 cover(vec2 uv) {
	float n = 20.0;
	vec2 m = abs(floor(uv * n) - (n - 1.0) * 0.5);
	m = vec2(max(m.x, m.y), min(m.x, m.y));

	return ramp(floor(smoothstep(0.25, 0.75, fbm(m * 0.25 + uSeed.xy * 10.0)) * 6.0) / 5.0);
}
`,
	fold: `
vec3 cover(vec2 uv) {
	float n = 48.0;
	vec2 q = (floor(uv * n) + 0.5) / n - 0.5;
	float sector = 6.2832 / 6.0;
	float angle = abs(mod(atan(q.y, q.x), sector) - sector * 0.5);
	vec2 p = vec2(cos(angle), sin(angle)) * length(q) * 4.0 + uSeed.xy * 10.0;

	return ramp(floor(smoothstep(0.25, 0.75, fbm(p + fbm(p * 1.5))) * 5.0) / 4.0);
}
`,
	stitch: `
vec3 cover(vec2 uv) {
	float n = 24.0;
	float row = floor(uv.y * n);
	float shift = floor((hash(vec2(row, uSeed.x * 7.0)) - 0.5) * 6.0) * step(0.65, hash(vec2(row, uSeed.y * 13.0)));
	vec2 id = vec2(floor(uv.x * n) + shift, row);
	vec2 f = fract(uv * n);
	vec3 color = ramp(floor(noise(id * 0.25 + uSeed.zw * 20.0) * 4.0) / 3.0);

	return color * (0.85 + 0.15 * step(0.12, min(f.x, f.y)));
}
`,
	static: `
vec3 cover(vec2 uv) {
	float row = floor(uv.y * 30.0);
	float shift = step(0.7, hash(vec2(row, uSeed.x * 11.0))) * (hash(vec2(row, uSeed.y * 5.0)) - 0.5) * 0.4;
	vec2 cell = floor(vec2((uv.x + shift) * 18.0, uv.y * 30.0));
	float level = floor(noise(cell * vec2(0.18, 0.35) + uSeed.zw * 20.0) * 5.0) / 4.0;
	float burst = step(0.93, hash(cell + uSeed.xy * 13.0));

	return mix(ramp(level), ramp(1.0 - level), burst) * (0.85 + 0.15 * step(0.5, fract(uv.y * 90.0)));
}
`,
	mosh: `
vec3 cover(vec2 uv) {
	vec2 block = floor(uv * 16.0);
	vec2 direction = vec2(hash(block + uSeed.xy * 20.0), hash(block + uSeed.zw * 20.0)) - 0.5;
	float smear = step(0.55, hash(block * 0.37 + uSeed.x));
	vec2 p = uv + direction * 0.35 * smear * fract(uv.y * 16.0);

	return ramp(smoothstep(0.2, 0.8, fbm(p * 2.5 + uSeed.yz * 10.0))) * (1.0 - 0.15 * smear);
}
`,
	delta: `
vec3 cover(vec2 uv) {
	vec2 tiles = vec2(5.0, 7.0);
	vec2 block = floor(uv * tiles);
	vec2 offset = vec2(hash(block + uSeed.x), hash(block + uSeed.y)) * 3.0;
	float level = floor(fbm(uv * 3.0 + offset + uSeed.zw * 10.0) * 7.0) / 6.0;
	vec2 f = fract(uv * tiles);

	return ramp(fract(level + hash(block) * 0.3)) * (0.85 + 0.15 * step(0.02, f.x) * step(0.02, f.y));
}
`,

	// Stripes and op-art.
	whorl: `
vec3 cover(vec2 uv) {
	vec2 p = uv * 2.0 + uSeed.xy * 10.0;
	float warp = fbm(p) * 4.0 + fbm(p * 2.0 + 3.0) * 1.5;
	float angle = uSeed.z * 6.2832;
	float stripe = sin((uv.x * cos(angle) + uv.y * sin(angle)) * 40.0 + warp * 6.0);
	float mask = smoothstep(-0.12, 0.12, stripe);

	return mix(uPalette[0] * 0.3, mix(vec3(0.95, 0.93, 0.88), uPalette[2], 0.25), mask);
}
`,
	warp: `
vec3 cover(vec2 uv) {
	vec2 p = uv - 0.5;
	p += 0.15 * vec2(fbm(p * 3.0 + uSeed.xy * 9.0), fbm(p * 3.0 + uSeed.zw * 9.0)) - 0.075;
	float pattern = sin(length(p) * 60.0) * sin(atan(p.y, p.x) * 8.0 + uSeed.x * 6.0);

	return mix(uPalette[0] * 0.3, uPalette[3], step(0.0, pattern));
}
`,
	vee: `
vec3 cover(vec2 uv) {
	float band = floor(uv.y * 6.0 + abs(uv.x - 0.5) * 6.0 * (0.6 + uSeed.x) + uSeed.y * 10.0);

	return ramp(mod(band, 4.0) / 3.0);
}
`,
	rise: `
vec3 cover(vec2 uv) {
	vec2 center = vec2(0.5, -0.1 + uSeed.x * 0.2);
	float band = floor(length(uv - center) * 9.0);
	float angle = atan(uv.y - center.y, uv.x - center.x);
	float stripe = step(0.5, fract(angle * 10.0 / 3.1416 + band * 0.5)) * step(0.4, hash(vec2(band, uSeed.y)));

	return mix(ramp(band / 9.0), ramp(1.0 - band / 9.0) * 0.8, stripe);
}
`,
	weave: `
vec3 cover(vec2 uv) {
	vec2 g = uv * 8.0;
	vec2 id = floor(g);
	vec2 f = fract(g);
	bool vertical = mod(id.x + id.y, 2.0) < 1.0;
	vec3 color = vertical ? ramp(hash(vec2(id.x, uSeed.x * 9.0))) : ramp(hash(vec2(id.y, uSeed.y * 9.0)));
	float stripe = step(0.5, fract((vertical ? f.y : f.x) * 4.0));
	float edge = vertical ? smoothstep(0.0, 0.12, min(f.x, 1.0 - f.x)) : smoothstep(0.0, 0.12, min(f.y, 1.0 - f.y));

	return color * (0.8 + 0.2 * stripe) * (0.6 + 0.4 * edge);
}
`,
	zig: `
vec3 cover(vec2 uv) {
	float z = abs(fract(uv.x * 4.0 + uSeed.y) - 0.5) * 2.0;
	z = z * z * (3.0 - 2.0 * z);

	return ramp(mod(floor(uv.y * 8.0 + uSeed.x * 10.0 + z * 1.2), 5.0) / 4.0);
}
`,

	// Organic textures.
	terrain: `
vec3 cover(vec2 uv) {
	float v = fbm(uv * 2.0 + uSeed.xy * 10.0);
	vec3 color = ramp(floor(v * 12.0) / 11.0);

	return mix(color, uPalette[0] * 0.5, 1.0 - smoothstep(0.0, 0.1, fract(v * 12.0)));
}
`,
	culture: `
vec3 cover(vec2 uv) {
	vec3 cell = voronoi(uv * 4.0 + uSeed.xy * 10.0);
	float blob = smoothstep(0.45, 0.15, cell.x);

	return mix(ramp(0.08), ramp(0.5 + 0.5 * cell.z), blob) + grain(gl_FragCoord.xy) * 0.25 * blob;
}
`,
	filament: `
vec3 cover(vec2 uv) {
	vec2 p = uv * 1.2 + uSeed.xy * 10.0;
	float flow = fbm(p) * 1.4 + fbm(p * 0.5 + 7.0) * 0.8;
	float l = fract((uv.y + flow * 0.35) * 26.0);
	float line = smoothstep(0.0, 0.08, l) * smoothstep(0.35, 0.12, l);

	return mix(ramp(0.04), ramp(0.35 + 0.65 * fbm(p * 1.3 + 3.0)), line);
}
`,
	vein: `
vec3 cover(vec2 uv) {
	vec2 p = uv * 2.0 + uSeed.xy * 10.0;
	float v = uv.y * 3.0 + fbm(p) * 2.5 + fbm(p * 2.0 + 5.0);

	return ramp(mod(floor(v * 3.0), 4.0) / 3.0);
}
`,
	coral: `
vec3 cover(vec2 uv) {
	vec3 cell = voronoi(uv * 7.0 + uSeed.xy * 10.0);

	return mix(ramp(0.85), ramp(0.15 + 0.3 * cell.z), smoothstep(0.0, 0.08, cell.y - cell.x));
}
`,
	pith: `
vec3 cover(vec2 uv) {
	vec3 cell = voronoi(uv * 6.0 + uSeed.xy * 10.0);
	float shade = smoothstep(0.0, 0.6, cell.x) * 0.8 + 0.1 * cell.z;

	return mix(ramp(0.1), ramp(0.8), step(bayer4(gl_FragCoord.xy / 2.0), shade));
}
`,
	sonar: `
vec3 cover(vec2 uv) {
	float v = fbm(uv * 2.5 + uSeed.xy * 10.0);
	float d = bayer4(gl_FragCoord.xy / 3.0);

	if (v > 0.5) {
		return mix(ramp(0.6), ramp(1.0), step(d, (v - 0.5) * 3.0));
	}

	return mix(ramp(0.0), ramp(0.3), step(d, v * 1.6));
}
`,
	dahlia: `
vec3 cover(vec2 uv) {
	vec2 q = uv - 0.5;
	float r = length(q) * 2.0;
	float petals = 8.0 + floor(uSeed.x * 10.0);
	float shape = step(r, 0.3 + 0.6 * abs(sin(atan(q.y, q.x) * petals * 0.5 + r * 2.0)) * (1.0 - r * 0.4));

	return mix(ramp(0.08), ramp(0.3 + 0.7 * fract(floor(r * 6.0) * 0.3 + uSeed.y)), shape);
}
`,

	// Collages and paper.
	crowd: `
vec3 cover(vec2 uv) {
	vec2 p = uv * 2.4 + uSeed.xy * 10.0;
	float level = floor(smoothstep(0.25, 0.75, fbm(p + fbm(p * 1.3) * 0.8)) * 4.0) / 3.0;
	vec3 color = ramp(level);
	float stipple = step(0.82, hash(floor(gl_FragCoord.xy / 2.0) + uSeed.zw * 99.0));

	return mix(color, color * 0.35, stipple * step(level, 0.5));
}
`,
	riso: `
vec3 cover(vec2 uv) {
	vec2 p = uv * 1.8 + uSeed.xy * 10.0;
	float torn = noise(p * 40.0) * 0.04;
	float first = step(0.5, fbm(p) + torn);
	float second = step(0.52, fbm(p + vec2(3.1, 1.7)) + torn);
	vec3 color = vec3(0.95, 0.93, 0.88) * mix(vec3(1.0), uPalette[1], first) * mix(vec3(1.0), uPalette[2], second);

	return color + grain(gl_FragCoord.xy) * 0.1;
}
`,
	splice: `
vec3 cover(vec2 uv) {
	float strip = floor(uv.x * 5.0 + hash(vec2(floor(uv.y * 3.0), uSeed.x)) - 0.5);
	float k = hash(vec2(strip, uSeed.y * 7.0));
	float blot = step(0.5, fbm(uv * 3.0 + k * 10.0));
	float lines = step(0.5, fract((uv.y + k) * 30.0 * (0.5 + k)));
	vec3 color = mix(vec3(0.94, 0.92, 0.86), ramp(0.3 + 0.7 * k), k < 0.5 ? blot : lines);

	return color * (0.9 + 0.1 * grain(gl_FragCoord.xy));
}
`,
	carve: `
vec3 cover(vec2 uv) {
	vec3 cell = voronoi(uv * 3.0 + uSeed.xy * 10.0);

	return ramp(0.2 + 0.7 * cell.z) * (0.55 + 0.45 * smoothstep(0.0, 0.15, cell.y - cell.x));
}
`,

	// Tiles and scatters.
	relief: `
vec3 cover(vec2 uv) {
	vec2 p = vec2(uv.x * 6.0 * 1.732, uv.y * 6.0);
	vec2 a = vec2(p.x * 0.5 + p.y, p.y - p.x * 0.5) + uSeed.xy * 10.0;
	vec2 id = floor(a);
	vec2 f = fract(a);
	float shade = f.x + f.y < 1.0 ? 1.0 : (f.x > f.y ? 0.7 : 0.45);

	return ramp(0.2 + 0.6 * hash(id + uSeed.zw * 10.0)) * shade;
}
`,
	sampler: `
vec3 cover(vec2 uv) {
	vec2 id = floor(uv * 4.0);
	vec2 f = fract(uv * 4.0);
	float k = hash(id + uSeed.xy * 21.0);
	float m = step(f.y, 0.5 + 0.3 * sin(f.x * 6.2832));

	if (k < 0.2) {
		m = step(length(f), 0.7);
	} else if (k < 0.4) {
		m = step(0.5, fract((f.x + f.y) * 3.0));
	} else if (k < 0.6) {
		m = step(length(fract(f * 3.0) - 0.5), 0.3);
	} else if (k < 0.8) {
		m = clamp(step(abs(f.x - 0.5), 0.18) + step(abs(f.y - 0.5), 0.18), 0.0, 1.0);
	}

	return mix(ramp(hash(id + uSeed.zw * 5.0) * 0.5), ramp(0.5 + 0.5 * hash(id * 2.1 + uSeed.x)), m);
}
`,
	modular: `
vec3 cover(vec2 uv) {
	vec2 g = uv * 5.0;
	vec2 id = floor(g);
	float radius = 0.15 + 0.3 * hash(id + uSeed.xy * 3.0);
	vec2 d = abs(fract(g) - 0.5) - (0.42 - radius);
	float box = length(max(d, 0.0)) - radius;

	return mix(ramp(0.05), ramp(0.25 + 0.75 * hash(id * 1.9 + uSeed.zw)), smoothstep(0.02, -0.02, box));
}
`,
	chaff: `
vec3 cover(vec2 uv) {
	vec3 color = ramp(0.05);

	for (int k = 0; k < 3; k++) {
		float n = 5.0 + float(k) * 3.5;
		vec2 g = uv * n;
		vec2 id = floor(g);
		vec2 f = fract(g) - 0.5;
		float h = hash(id + uSeed.xy * 9.0 + float(k) * 3.7);
		vec2 direction = vec2(cos(h * 6.2832), sin(h * 6.2832));
		float along = dot(f, direction);
		float across = dot(f, vec2(-direction.y, direction.x));
		float blade = smoothstep(0.01, 0.0, abs(across) - 0.07 * (1.0 - abs(along) * 2.1)) * step(abs(along), 0.47);

		color = mix(color, ramp(0.35 + 0.65 * hash(id * 3.1 + uSeed.z + float(k))), blade * step(0.2, h));
	}

	return color;
}
`,
	strand: `
vec3 cover(vec2 uv) {
	vec2 g = uv * 8.0;
	vec2 id = floor(g);
	vec2 f = fract(g);
	float h = hash(id + uSeed.xy * 13.0);
	float rod = smoothstep(0.09, 0.06, h < 0.5 ? abs(f.y - 0.5) : abs(f.x - 0.5));
	float bead = smoothstep(0.2, 0.17, length(f - 0.5)) * step(0.6, h);

	return mix(ramp(0.05), ramp(0.4 + 0.5 * hash(id * 1.7 + uSeed.z)), max(rod, bead));
}
`,
	husk: `
vec3 cover(vec2 uv) {
	vec2 g = uv * 4.0;
	vec2 id = floor(g);
	vec2 offset = vec2(hash(id + uSeed.x), hash(id + uSeed.y)) - 0.5;
	float angle = hash(id + uSeed.z) * 3.1416;
	vec2 q = fract(g) - 0.5 - offset * 0.2;
	q = vec2(cos(angle) * q.x + sin(angle) * q.y, -sin(angle) * q.x + cos(angle) * q.y);
	float shell = length(q * vec2(1.0, 2.0)) - 0.36;
	float eaten = step(0.55, noise(g * 5.0 + uSeed.w * 30.0)) * step(-0.2, shell);

	return mix(ramp(0.9), ramp(0.15 + 0.4 * hash(id * 2.0)), step(shell, 0.0) * (1.0 - eaten));
}
`,
};
