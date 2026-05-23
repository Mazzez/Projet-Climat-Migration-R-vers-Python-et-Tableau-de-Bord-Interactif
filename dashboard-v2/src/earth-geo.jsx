// Earth geometry loader — fetches world-110m TopoJSON, builds shared
// triangulated land mesh + coastline line segments, caches them.

const THREE_EG = window.THREE;

// Convert lon/lat (degrees) → unit sphere XYZ
function lonLatToXYZ(lon, lat, r = 1) {
  const phi = (90 - lat) * Math.PI / 180;
  const theta = lon * Math.PI / 180;
  return [
    -r * Math.sin(phi) * Math.cos(theta),
     r * Math.cos(phi),
     r * Math.sin(phi) * Math.sin(theta),
  ];
}

// Tessellate a segment between two lon/lat points along a chord, then project
// each interpolated point onto the sphere. Avoids straight-line shortcuts.
function tessellateSegment(lon0, lat0, lon1, lat1, r, segments = 4) {
  // Handle antimeridian wrap
  let dLon = lon1 - lon0;
  if (dLon > 180) lon1 -= 360;
  else if (dLon < -180) lon1 += 360;
  const pts = [];
  for (let i = 0; i <= segments; i++) {
    const t = i / segments;
    const lo = lon0 + (lon1 - lon0) * t;
    const la = lat0 + (lat1 - lat0) * t;
    const xyz = lonLatToXYZ(lo, la, r);
    pts.push(...xyz);
  }
  return pts;
}

// Densify a ring of [lon,lat] coords by tessellating each edge.
function densifyRing(ring, subdiv = 3) {
  const dense = [];
  for (let i = 0; i < ring.length - 1; i++) {
    const [lon0, lat0] = ring[i];
    const [lon1, lat1] = ring[i + 1];
    let lonA = lon0, lonB = lon1;
    const d = lonB - lonA;
    if (d > 180) lonB -= 360;
    else if (d < -180) lonB += 360;
    for (let s = 0; s < subdiv; s++) {
      const t = s / subdiv;
      dense.push([lonA + (lonB - lonA) * t, lat0 + (lat1 - lat0) * t]);
    }
  }
  // Close the ring
  if (dense.length > 0) {
    const [lon0, lat0] = ring[ring.length - 1];
    dense.push([lon0, lat0]);
  }
  return dense;
}

// Triangulate one polygon (outer ring + optional holes) using THREE.ShapeUtils.
// Returns flat array of triangle vertex positions in XYZ on sphere of radius r.
function triangulatePolygonOnSphere(polygon, r) {
  if (!polygon || polygon.length === 0) return [];
  const positions = [];
  const outer = polygon[0];
  if (!outer || outer.length < 3) return [];

  // Densify
  const denseOuter = densifyRing(outer, 2);
  const holes = polygon.slice(1).map(h => densifyRing(h, 2).map(([x,y]) => new THREE_EG.Vector2(x, y)));
  const contour = denseOuter.map(([x,y]) => new THREE_EG.Vector2(x, y));

  let tris;
  try {
    tris = THREE_EG.ShapeUtils.triangulateShape(contour, holes);
  } catch (e) {
    return [];
  }
  // tris is array of [i,j,k] using indices into combined [contour, ...holes] array
  const combined = [...contour, ...holes.flat()];
  for (const tri of tris) {
    for (const idx of tri) {
      const v = combined[idx];
      if (!v) continue;
      const xyz = lonLatToXYZ(v.x, v.y, r);
      positions.push(...xyz);
    }
  }
  return positions;
}

// Build coastline positions (LineSegments) from a polygon ring.
function buildRingSegments(ring, r) {
  const positions = [];
  for (let i = 0; i < ring.length - 1; i++) {
    const [lon0, lat0] = ring[i];
    const [lon1, lat1] = ring[i + 1];
    const seg = tessellateSegment(lon0, lat0, lon1, lat1, r, 3);
    // LineSegments wants pairs (start, end) for each segment. seg has 4 points = 4*3 floats.
    // Convert to pairs.
    for (let k = 0; k < seg.length - 3; k += 3) {
      positions.push(seg[k], seg[k+1], seg[k+2]);
      positions.push(seg[k+3], seg[k+4], seg[k+5]);
    }
  }
  return positions;
}

let _earthGeoCache = null;
let _earthGeoPromise = null;

async function loadEarthGeo() {
  if (_earthGeoCache) return _earthGeoCache;
  if (_earthGeoPromise) return _earthGeoPromise;

  _earthGeoPromise = (async () => {
    let land;
    try {
      const url = 'https://cdn.jsdelivr.net/npm/world-atlas@2.0.2/land-110m.json';
      const topology = await fetch(url).then(r => r.json());
      if (!window.topojson) throw new Error('topojson-client not loaded');
      land = window.topojson.feature(topology, topology.objects.land);
    } catch (e) {
      console.warn('[earth-geo] CDN fetch failed, using fallback', e);
      land = { type: 'FeatureCollection', features: window.FALLBACK_LAND ? window.FALLBACK_LAND.features : [] };
    }

    // Build land triangulation
    const landR = 1.0008;
    const allLandPositions = [];
    // Coastline positions
    const coastR = 1.0015;
    const allCoastPositions = [];

    for (const feature of land.features) {
      const polys = feature.geometry.type === 'Polygon'
        ? [feature.geometry.coordinates]
        : feature.geometry.coordinates;
      for (const poly of polys) {
        const triPositions = triangulatePolygonOnSphere(poly, landR);
        for (const v of triPositions) allLandPositions.push(v);
        // Coastlines: outer ring + holes
        for (const ring of poly) {
          const seg = buildRingSegments(ring, coastR);
          for (const v of seg) allCoastPositions.push(v);
        }
      }
    }

    const landGeom = new THREE_EG.BufferGeometry();
    landGeom.setAttribute('position', new THREE_EG.Float32BufferAttribute(allLandPositions, 3));
    // Add normals (pointing outward = position normalized) for shader
    const normals = new Float32Array(allLandPositions.length);
    for (let i = 0; i < allLandPositions.length; i += 3) {
      const x = allLandPositions[i], y = allLandPositions[i+1], z = allLandPositions[i+2];
      const len = Math.sqrt(x*x + y*y + z*z) || 1;
      normals[i] = x/len; normals[i+1] = y/len; normals[i+2] = z/len;
    }
    landGeom.setAttribute('normal', new THREE_EG.Float32BufferAttribute(normals, 3));

    const coastGeom = new THREE_EG.BufferGeometry();
    coastGeom.setAttribute('position', new THREE_EG.Float32BufferAttribute(allCoastPositions, 3));

    _earthGeoCache = { landGeom, coastGeom };
    return _earthGeoCache;
  })();

  return _earthGeoPromise;
}

// Starfield builder — simple Points cloud on large sphere.
function makeStarfield(count = 600) {
  const positions = new Float32Array(count * 3);
  const colors = new Float32Array(count * 3);
  for (let i = 0; i < count; i++) {
    const u = Math.random();
    const v = Math.random();
    const theta = 2 * Math.PI * u;
    const phi = Math.acos(2 * v - 1);
    const r = 40 + Math.random() * 30;
    positions[i*3+0] = r * Math.sin(phi) * Math.cos(theta);
    positions[i*3+1] = r * Math.sin(phi) * Math.sin(theta);
    positions[i*3+2] = r * Math.cos(phi);
    // Slight tint variation
    const t = Math.random();
    colors[i*3+0] = 0.85 + 0.15 * t;
    colors[i*3+1] = 0.9  + 0.1  * t;
    colors[i*3+2] = 1.0;
  }
  const geom = new THREE_EG.BufferGeometry();
  geom.setAttribute('position', new THREE_EG.Float32BufferAttribute(positions, 3));
  geom.setAttribute('color', new THREE_EG.Float32BufferAttribute(colors, 3));
  const mat = new THREE_EG.PointsMaterial({
    size: 0.18, vertexColors: true,
    transparent: true, opacity: 0.6,
    sizeAttenuation: true, depthWrite: false,
  });
  return new THREE_EG.Points(geom, mat);
}

window.loadEarthGeo = loadEarthGeo;
window.makeStarfield = makeStarfield;
window.lonLatToXYZ_geo = lonLatToXYZ;
