// Three.js wrappers — Globe (shader-based data globe) + Particles
// No R3F — direct THREE for CDN reliability.

const THREE = window.THREE;

// Convert lat/lon (degrees) to Vector3 on unit sphere
function latLonToVec3(latDeg, lonDeg, r = 1) {
  const phi = (90 - latDeg) * Math.PI / 180;
  const theta = (lonDeg) * Math.PI / 180;
  return new THREE.Vector3(
    -r * Math.sin(phi) * Math.cos(theta),
     r * Math.cos(phi),
     r * Math.sin(phi) * Math.sin(theta),
  );
}

// Build DataTexture from grid [latRows][lonCols] of values, scale encoded into [0..255]
function gridToTexture(grid, vmin = -0.06, vmax = 0.12) {
  const rows = grid.length, cols = grid[0].length;
  const data = new Uint8Array(rows * cols * 4);
  for (let r = 0; r < rows; r++) {
    for (let c = 0; c < cols; c++) {
      const v = grid[r][c];
      const t = (v - vmin) / (vmax - vmin);
      const tt = Math.max(0, Math.min(1, t));
      const i = (r * cols + c) * 4;
      data[i + 0] = Math.round(tt * 255);
      data[i + 1] = 0;
      data[i + 2] = 0;
      data[i + 3] = 255;
    }
  }
  const tex = new THREE.DataTexture(data, cols, rows, THREE.RGBAFormat);
  tex.magFilter = THREE.LinearFilter;
  tex.minFilter = THREE.LinearFilter;
  tex.wrapS = THREE.RepeatWrapping;
  tex.wrapT = THREE.ClampToEdgeWrapping;
  tex.needsUpdate = true;
  return tex;
}

// Hand-baked continent silhouette mask 256x128 (cylindrical/equirectangular)
// Approximate ellipses for major landmasses. Lon 0..360, Lat -90..90.
function makeContinentTexture() {
  const w = 512, h = 256;
  const canvas = document.createElement('canvas');
  canvas.width = w; canvas.height = h;
  const ctx = canvas.getContext('2d');
  ctx.fillStyle = '#000'; ctx.fillRect(0, 0, w, h);
  ctx.fillStyle = '#fff';

  // helper: lon (0-360), lat (-90 to 90)
  const px = (lon) => ((lon + 360) % 360) / 360 * w;
  const py = (lat) => (1 - (lat + 90) / 180) * h;

  const blob = (lon, lat, rx, ry, rot = 0) => {
    ctx.save();
    ctx.translate(px(lon), py(lat));
    ctx.rotate(rot);
    ctx.beginPath();
    ctx.ellipse(0, 0, rx, ry, 0, 0, Math.PI * 2);
    ctx.fill();
    ctx.restore();
  };

  // North America
  blob(255, 50, 38, 26, -0.2);
  blob(265, 30, 22, 18, 0.1);
  blob(290, 60, 32, 20, 0.1);
  // South America
  blob(300, -15, 18, 26, 0.15);
  blob(305, -35, 14, 18, 0.1);
  // Greenland
  blob(320, 72, 14, 12, 0);
  // Europe
  blob(15, 50, 22, 14, -0.1);
  blob(35, 60, 28, 14, -0.05);
  // Africa
  blob(20, 5, 22, 18, 0.05);
  blob(25, -15, 16, 20, -0.05);
  blob(35, 25, 18, 14, 0.2);
  // Middle East
  blob(48, 28, 14, 14, 0);
  // Asia
  blob(80, 50, 50, 24, -0.1);
  blob(110, 40, 40, 24, 0);
  blob(95, 25, 18, 14, 0.2);
  blob(135, 55, 28, 18, 0);
  // India
  blob(78, 18, 14, 16, 0);
  // SE Asia / Indonesia
  blob(115, -2, 18, 8, 0.05);
  blob(125, -3, 14, 6, 0);
  blob(140, -5, 10, 5, -0.1);
  // Australia
  blob(135, -25, 26, 14, 0);
  // Antarctica band
  ctx.fillRect(0, py(-90), w, h - py(-90));
  ctx.fillRect(0, py(-65), w, py(-90) - py(-65));

  const tex = new THREE.CanvasTexture(canvas);
  tex.magFilter = THREE.LinearFilter;
  tex.minFilter = THREE.LinearFilter;
  tex.wrapS = THREE.RepeatWrapping;
  tex.wrapT = THREE.ClampToEdgeWrapping;
  return tex;
}
let _contTex = null;
function getContinentTex() { if (!_contTex) _contTex = makeContinentTexture(); return _contTex; }

// ----------------------------------------------------------------
// GLOBE COMPONENT
// ----------------------------------------------------------------
function Globe({
  grid = window.T2M_TREND_GRID,
  vmin = -0.06,
  vmax = 0.12,
  autoRotate = true,
  rotationSpeed = 0.04,
  showTrend = 1.0,
  showAtmosphere = true,
  hotspots = [],
  bands = [],
  cameraDistance = 2.6,
  initialLon = 0,
  initialLat = 0,           // latitude (degrees) to face the camera
  height,                  // px or fraction
  width,
  pulse = true,
  interactive = true,
  onHotspotClick,
  segments = 96,
  showGrid = true,
  paused = false,
  showStars = false,
  starCount = 500,
}) {
  const mountRef = useRef(null);
  const stateRef = useRef({});
  const pausedRef = useRef(paused);
  const [hover, setHover] = useState(null);
  const [labelPositions, setLabelPositions] = useState({});

  useEffect(() => { pausedRef.current = paused; }, [paused]);

  useEffect(() => {
    const mount = mountRef.current;
    if (!mount) return;
    let W = mount.clientWidth;
    let H = mount.clientHeight;

    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(45, W / H, 0.1, 100);
    // Position camera: by default at +Z looking at origin. If initialLat/initialLon
    // are non-zero AND autoRotate is off, we re-position camera along the (lat,lon)
    // radial direction so that point faces the camera. Robust against rotation order
    // confusion. When autoRotate is on, we keep the simple +Z position so rotations work.
    if (!autoRotate && (Math.abs(initialLat) > 0.01 || Math.abs(initialLon) > 0.01)) {
      const camPos = latLonToVec3(initialLat, initialLon, cameraDistance);
      camera.position.set(camPos.x, camPos.y, camPos.z);
      camera.lookAt(0, 0, 0);
    } else {
      camera.position.set(0, 0.2, cameraDistance);
    }

    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true, preserveDrawingBuffer: true });
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.setSize(W, H);
    renderer.setClearColor(0x000000, 0);
    mount.appendChild(renderer.domElement);

    // Trend texture (continent texture removed — replaced by real geo meshes)
    const trendTex = gridToTexture(grid, vmin, vmax);

    // Earth Day texture (NASA Blue Marble Next Generation, ~1-2 MB JPEG via jsdelivr)
    const earthTexLoader = new THREE.TextureLoader();
    earthTexLoader.setCrossOrigin('anonymous');
    const earthTex = earthTexLoader.load(
      'https://cdn.jsdelivr.net/npm/three-globe@2.31.0/example/img/earth-day.jpg',
      undefined, undefined,
      (err) => console.warn('[Globe] earth-day texture failed', err),
    );
    if ('colorSpace' in earthTex) earthTex.colorSpace = THREE.SRGBColorSpace;
    earthTex.wrapS = THREE.RepeatWrapping;
    earthTex.wrapT = THREE.ClampToEdgeWrapping;
    earthTex.minFilter = THREE.LinearMipmapLinearFilter;
    earthTex.magFilter = THREE.LinearFilter;
    earthTex.anisotropy = 8;

    // Custom shader — Earth Day texture + trend overlay (translucid)
    const oceanMat = new THREE.ShaderMaterial({
      uniforms: {
        earthTex: { value: earthTex },
        trendTex: { value: trendTex },
        opacityTrend: { value: showTrend },
        time: { value: 0 },
        vmin: { value: vmin },
        vmax: { value: vmax },
        showGrid: { value: showGrid ? 1.0 : 0.0 },
        landFactor: { value: 0.0 }, // kept for backward compat with land mesh path
        rimGlow: { value: 1.0 },
        sunDir: { value: new THREE.Vector3(1.0, 0.3, 0.7).normalize() },
        baseOcean: { value: new THREE.Color('#0a1e3a') }, // fallback while texture loads
        atmoColor: { value: new THREE.Color('#7ec8ff') },
        hotColor: { value: new THREE.Color('#FF6B35') },
        coldColor: { value: new THREE.Color('#00D9FF') },
      },
      vertexShader: `
        varying vec3 vLocalPos;
        varying vec3 vWorldNormal;
        varying vec3 vViewNormal;
        varying vec3 vViewDir;
        void main() {
          vLocalPos = position;
          vWorldNormal = normalize(mat3(modelMatrix) * normal);
          vViewNormal = normalize(normalMatrix * normal);
          vec4 mvPos = modelViewMatrix * vec4(position, 1.0);
          vViewDir = normalize(-mvPos.xyz);
          gl_Position = projectionMatrix * mvPos;
        }
      `,
      fragmentShader: `
        precision highp float;
        uniform sampler2D earthTex;
        uniform sampler2D trendTex;
        uniform float opacityTrend;
        uniform float time;
        uniform float vmin;
        uniform float vmax;
        uniform float showGrid;
        uniform float landFactor;
        uniform float rimGlow;
        uniform vec3 sunDir;
        uniform vec3 baseOcean;
        uniform vec3 atmoColor;
        uniform vec3 hotColor;
        uniform vec3 coldColor;
        varying vec3 vLocalPos;
        varying vec3 vWorldNormal;
        varying vec3 vViewNormal;
        varying vec3 vViewDir;

        void main() {
          // Earth texture & trend data are anchored to the SPHERE (local space),
          // so they rotate with it. Sunlight stays in WORLD space (fixed sun).
          vec3 n = normalize(vLocalPos);
          float lat = asin(clamp(n.y, -1.0, 1.0)) / 3.14159265 + 0.5;
          float lon = atan(n.z, n.x) / (2.0 * 3.14159265) + 0.5;

          // Earth base color — UV maps onto Blue Marble equirectangular (Greenwich at u=0.5).
          // Note: shader lon increases westward due to atan(z,x), so we use (0.5 - lon).
          // Three.js auto-flips the JPEG so v=1 is the north pole → no extra inversion.
          vec2 earthUV = vec2(fract(0.5 - lon), lat);
          vec3 earth = texture2D(earthTex, earthUV).rgb;
          // Fallback to baseOcean while texture is still loading (initial all-black)
          float texReady = smoothstep(0.0, 0.04, length(earth));
          vec3 base = mix(baseOcean, earth, texReady);

          // Trend overlay (Sen pente or corr CO2)
          float encoded = texture2D(trendTex, vec2(lon, lat)).r;
          float trend = encoded * (vmax - vmin) + vmin;
          vec3 tint = vec3(0.0);
          if (trend > 0.0) {
            tint = hotColor * smoothstep(0.005, vmax * 0.85, trend);
          } else {
            tint = coldColor * smoothstep(0.005, -vmin * 0.85, -trend);
          }
          // Translucid overlay ~35% — darkens base slightly then adds tint
          float tintStrength = opacityTrend * 0.40;
          vec3 col = mix(base, base * 0.55 + tint * 1.15, tintStrength);

          // Subtle lat/lon grid — discreet over the Earth texture
          float latF = abs(fract(lat * 6.0) - 0.5);
          float lonF = abs(fract(lon * 12.0) - 0.5);
          float grid = max(
            smoothstep(0.497, 0.5, latF),
            smoothstep(0.497, 0.5, lonF)
          ) * 0.10 * showGrid;
          col += vec3(grid);

          // Special emphasis on equator and tropics
          float eq = smoothstep(0.0012, 0.0, abs(lat - 0.5));
          float trN = smoothstep(0.0012, 0.0, abs(lat - 0.63));
          float trS = smoothstep(0.0012, 0.0, abs(lat - 0.37));
          col += vec3(0.4, 0.7, 1.0) * eq * 0.25 * showGrid;
          col += vec3(1.0, 0.85, 0.5) * (trN + trS) * 0.18 * showGrid;

          // Gentle day/night modulation — sun is fixed in WORLD space, so the
          // terminator sweeps across continents as the globe rotates.
          float dayness = clamp(dot(vWorldNormal, sunDir) * 0.5 + 0.5, 0.0, 1.0);
          float lightF = mix(0.55, 1.08, dayness);
          col *= lightF;

          // Fresnel rim — calmer (was 1.4)
          float fres = 1.0 - max(0.0, dot(vViewNormal, vViewDir));
          fres = pow(fres, 2.2);
          col += atmoColor * fres * 0.55 * rimGlow;

          gl_FragColor = vec4(col, 1.0);
        }
      `,
    });

    const globe = new THREE.Mesh(new THREE.SphereGeometry(1, segments, segments), oceanMat);
    // YXZ : apply Y (longitude) first, then X (latitude) — needed for centering on hotspots
    globe.rotation.order = 'YXZ';
    const globeMat = oceanMat; // alias for backward compatibility with state ref
    scene.add(globe);

    // Land mesh + coastlines disabled — the Earth Day texture now provides
    // continents and coastlines natively. Keep this dead branch as a backup if
    // the user ever switches back to procedural mode.
    let landMesh = null;
    let coastlines = null;

    // Starfield (only if requested via prop — large background sphere of points)
    let starfield = null;
    if (showStars && window.makeStarfield) {
      starfield = window.makeStarfield(starCount);
      scene.add(starfield);
    }

    // Outer atmosphere shell
    let atmoMesh = null;
    if (showAtmosphere) {
      const atmoMat = new THREE.ShaderMaterial({
        side: THREE.BackSide,
        transparent: true,
        depthWrite: false,
        blending: THREE.AdditiveBlending,
        uniforms: {
          atmoColor: { value: new THREE.Color('#7ec8ff') },
          intensity: { value: 0.65 },
        },
        vertexShader: `
          varying vec3 vNormal;
          varying vec3 vViewDir;
          void main() {
            vNormal = normalize(normalMatrix * normal);
            vec4 mvPos = modelViewMatrix * vec4(position, 1.0);
            vViewDir = normalize(-mvPos.xyz);
            gl_Position = projectionMatrix * mvPos;
          }
        `,
        fragmentShader: `
          uniform vec3 atmoColor;
          uniform float intensity;
          varying vec3 vNormal;
          varying vec3 vViewDir;
          void main() {
            float f = pow(1.0 - max(0.0, dot(vNormal, vViewDir)), 2.4);
            gl_FragColor = vec4(atmoColor * f * intensity, f);
          }
        `,
      });
      atmoMesh = new THREE.Mesh(new THREE.SphereGeometry(1.15, 64, 64), atmoMat);
      scene.add(atmoMesh);
    }

    // Latitude band rings
    const bandRings = [];
    const bandLats = {
      austral: -75, temperate_S: -45, tropical: 0, temperate_N: 45, boreal: 75,
    };
    const bandColors = {
      austral: '#0077B6', temperate_S: '#3da4ff', tropical: '#52FFB8', temperate_N: '#FFB627', boreal: '#FF6B35',
    };
    bands.forEach(b => {
      const lat = bandLats[b];
      if (lat == null) return;
      const r = Math.cos(lat * Math.PI / 180) * 1.005;
      const y = Math.sin(lat * Math.PI / 180) * 1.005;
      const geo = new THREE.RingGeometry(r * 0.998, r * 1.002, 96);
      const mat = new THREE.MeshBasicMaterial({
        color: bandColors[b], side: THREE.DoubleSide, transparent: true, opacity: 0.7,
      });
      const ring = new THREE.Mesh(geo, mat);
      ring.rotation.x = Math.PI / 2;
      ring.position.y = y;
      scene.add(ring);
      bandRings.push(ring);
    });

    // Hotspots
    const hotspotMeshes = [];
    hotspots.forEach((hs, idx) => {
      const pos = latLonToVec3(hs.centerLat, hs.centerLon, 1.04);
      const group = new THREE.Group();
      // Pulsing inner sphere
      const innerMat = new THREE.MeshBasicMaterial({
        color: hs.color, transparent: true, opacity: 1,
      });
      const inner = new THREE.Mesh(new THREE.SphereGeometry(0.025, 16, 16), innerMat);
      group.add(inner);
      // Outer pulse ring
      const ringMat = new THREE.MeshBasicMaterial({
        color: hs.color, transparent: true, opacity: 0.4, side: THREE.DoubleSide,
      });
      const ring = new THREE.Mesh(new THREE.RingGeometry(0.04, 0.05, 24), ringMat);
      ring.lookAt(pos.clone().multiplyScalar(2));
      group.add(ring);
      group.position.copy(pos);
      group.userData = { hs, idx, inner, ring };
      scene.add(group);
      hotspotMeshes.push(group);
    });

    stateRef.current = { scene, camera, renderer, globe, atmoMesh, hotspotMeshes, bandRings, globeMat };

    // Drag rotation
    let isDragging = false;
    let lastX = 0, lastY = 0;
    let velX = 0;
    // If we re-positioned the camera (non-rotating mode), keep the globe at identity
    // so the hotspot at (initialLat, initialLon) faces the camera naturally.
    const useCameraMode = !autoRotate && (Math.abs(initialLat) > 0.01 || Math.abs(initialLon) > 0.01);
    let manualRotY = useCameraMode ? 0 : initialLon * Math.PI / 180;
    let manualRotX = useCameraMode ? 0 : initialLat * Math.PI / 180;
    let lastInteraction = performance.now();

    const onDown = (e) => {
      if (!interactive) return;
      isDragging = true;
      const pt = e.touches ? e.touches[0] : e;
      lastX = pt.clientX; lastY = pt.clientY;
      lastInteraction = performance.now();
      mount.style.cursor = 'grabbing';
    };
    const onMove = (e) => {
      if (!isDragging) return;
      const pt = e.touches ? e.touches[0] : e;
      const dx = pt.clientX - lastX;
      const dy = pt.clientY - lastY;
      manualRotY += dx * 0.005;
      manualRotX = Math.max(-Math.PI/2.4, Math.min(Math.PI/2.4, manualRotX + dy * 0.004));
      velX = dx * 0.005;
      lastX = pt.clientX; lastY = pt.clientY;
      lastInteraction = performance.now();
    };
    const onUp = () => { isDragging = false; mount.style.cursor = interactive ? 'grab' : 'default'; };

    if (interactive) {
      mount.style.cursor = 'grab';
      mount.addEventListener('mousedown', onDown);
      window.addEventListener('mousemove', onMove);
      window.addEventListener('mouseup', onUp);
      mount.addEventListener('touchstart', onDown, { passive: true });
      window.addEventListener('touchmove', onMove, { passive: true });
      window.addEventListener('touchend', onUp);
    }

    // Click on hotspot via raycast
    const raycaster = new THREE.Raycaster();
    const mouseVec = new THREE.Vector2();
    const onClick = (e) => {
      if (!onHotspotClick) return;
      const rect = renderer.domElement.getBoundingClientRect();
      mouseVec.x = ((e.clientX - rect.left) / rect.width) * 2 - 1;
      mouseVec.y = -((e.clientY - rect.top) / rect.height) * 2 + 1;
      raycaster.setFromCamera(mouseVec, camera);
      const hits = raycaster.intersectObjects(hotspotMeshes.map(g => g.children[0]), true);
      if (hits.length) {
        const group = hits[0].object.parent;
        onHotspotClick(group.userData.hs, group.userData.idx);
      }
    };
    mount.addEventListener('click', onClick);

    // Resize
    const onResize = () => {
      W = mount.clientWidth; H = mount.clientHeight;
      camera.aspect = W / H; camera.updateProjectionMatrix();
      renderer.setSize(W, H);
    };
    const ro = new ResizeObserver(onResize);
    ro.observe(mount);

    // Visibility detection
    let visible = true;
    const io = new IntersectionObserver(([e]) => { visible = e.isIntersecting; }, { threshold: 0.01 });
    io.observe(mount);

    // Animate
    let raf;
    const clock = new THREE.Clock();
    let t = 0;
    const tick = () => {
      raf = requestAnimationFrame(tick);
      if (!visible || pausedRef.current) return;
      const dt = Math.min(clock.getDelta(), 0.05);
      t += dt;

      // Auto-rotate if not dragging and recent interaction
      const sinceInter = performance.now() - lastInteraction;
      if (autoRotate && !isDragging && sinceInter > 2500) {
        manualRotY += rotationSpeed * dt;
      } else {
        // Decay velocity
        velX *= 0.95;
        manualRotY += velX;
      }
      globe.rotation.y = manualRotY;
      globe.rotation.x = manualRotX;
      if (atmoMesh) { atmoMesh.rotation.y = manualRotY; atmoMesh.rotation.x = manualRotX; }
      bandRings.forEach(r => { r.rotation.z = manualRotY; });

      // Hotspot follow rotation + pulse
      hotspotMeshes.forEach(g => {
        const hs = g.userData.hs;
        const basePos = latLonToVec3(hs.centerLat, hs.centerLon, 1.04);
        const v = basePos.clone().applyEuler(new THREE.Euler(manualRotX, manualRotY, 0, 'YXZ'));
        g.position.copy(v);
        if (pulse) {
          const s = 1 + 0.25 * Math.sin(t * 2 + g.userData.idx * 1.2);
          g.userData.ring.scale.setScalar(s);
          g.userData.ring.material.opacity = 0.5 - 0.3 * Math.sin(t * 2 + g.userData.idx * 1.2);
          g.userData.ring.lookAt(camera.position);
        }
      });

      globeMat.uniforms.time.value = t;

      // Compute screen positions for hotspot labels (only outward-facing)
      if (hotspotMeshes.length && stateRef.current.labelsCallback) {
        const positions = {};
        hotspotMeshes.forEach((g, i) => {
          const wp = g.position.clone();
          const facing = wp.clone().normalize().dot(camera.position.clone().normalize()) > 0.15;
          const sp = wp.clone().project(camera);
          const x = (sp.x * 0.5 + 0.5) * W;
          const y = (1 - (sp.y * 0.5 + 0.5)) * H;
          positions[i] = { x, y, visible: facing };
        });
        stateRef.current.labelsCallback(positions);
      }

      renderer.render(scene, camera);
    };
    tick();

    return () => {
      cancelAnimationFrame(raf);
      ro.disconnect(); io.disconnect();
      mount.removeEventListener('mousedown', onDown);
      window.removeEventListener('mousemove', onMove);
      window.removeEventListener('mouseup', onUp);
      mount.removeEventListener('touchstart', onDown);
      window.removeEventListener('touchmove', onMove);
      window.removeEventListener('touchend', onUp);
      mount.removeEventListener('click', onClick);
      try { mount.removeChild(renderer.domElement); } catch (e) {}
      globeMat.dispose(); globe.geometry.dispose();
      if (atmoMesh) { atmoMesh.material.dispose(); atmoMesh.geometry.dispose(); }
      bandRings.forEach(r => { r.material.dispose(); r.geometry.dispose(); });
      hotspotMeshes.forEach(g => g.children.forEach(c => { c.material.dispose(); c.geometry.dispose(); }));
      trendTex.dispose();
      earthTex.dispose();
      renderer.dispose();
    };
  // eslint-disable-next-line
  }, [grid, bands.join(','), hotspots.length, autoRotate, showAtmosphere, segments]);

  // Update uniforms reactively
  useEffect(() => {
    const s = stateRef.current;
    if (s.globeMat) {
      s.globeMat.uniforms.opacityTrend.value = showTrend;
      s.globeMat.uniforms.showGrid.value = showGrid ? 1.0 : 0.0;
    }
  }, [showTrend, showGrid]);

  // Hotspot label tracking
  useEffect(() => {
    stateRef.current.labelsCallback = setLabelPositions;
  }, []);

  return (
    <div ref={mountRef} style={{ position: 'relative', width: width || '100%', height: height || '100%' }}>
      {hotspots.map((hs, i) => {
        const p = labelPositions[i];
        if (!p) return null;
        return (
          <div key={i}
            style={{
              position: 'absolute',
              left: p.x, top: p.y,
              transform: 'translate(12px, -50%)',
              pointerEvents: 'none',
              opacity: p.visible ? 1 : 0.15,
              transition: 'opacity 280ms var(--ease-expo)',
              fontFamily: 'JetBrains Mono, monospace',
              fontSize: 10,
              letterSpacing: '0.06em',
              color: hs.color,
              textShadow: '0 0 8px rgba(0,0,0,0.8)',
              whiteSpace: 'nowrap',
            }}>
            <div style={{ fontWeight: 600 }}>{hs.name.toUpperCase()}</div>
            <div style={{ fontSize: 9, color: 'var(--text-dim)' }}>{hs.label}</div>
          </div>
        );
      })}
    </div>
  );
}

// ----------------------------------------------------------------
// PARTICLES — ascending CO2 stream behind hero
// ----------------------------------------------------------------
function ParticleField({ count = 280, height: pxHeight }) {
  const mountRef = useRef(null);
  useEffect(() => {
    const mount = mountRef.current;
    if (!mount) return;
    let W = mount.clientWidth, H = mount.clientHeight;
    const scene = new THREE.Scene();
    const camera = new THREE.OrthographicCamera(-W/2, W/2, H/2, -H/2, -1000, 1000);
    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.setSize(W, H);
    renderer.setClearColor(0x000000, 0);
    mount.appendChild(renderer.domElement);

    const geom = new THREE.BufferGeometry();
    const positions = new Float32Array(count * 3);
    const offsets = new Float32Array(count);
    const speeds = new Float32Array(count);
    const colors = new Float32Array(count * 3);
    for (let i = 0; i < count; i++) {
      positions[i*3+0] = (Math.random() - 0.5) * W * 1.4;
      positions[i*3+1] = (Math.random() - 0.5) * H;
      positions[i*3+2] = (Math.random() - 0.5) * 100;
      offsets[i] = Math.random() * H;
      speeds[i] = 12 + Math.random() * 30;
      // gradient cold -> hot by height
      const t = Math.random();
      if (t < 0.5) { colors[i*3+0] = 0.0; colors[i*3+1] = 0.85; colors[i*3+2] = 1.0; }
      else         { colors[i*3+0] = 1.0; colors[i*3+1] = 0.42; colors[i*3+2] = 0.20; }
    }
    geom.setAttribute('position', new THREE.BufferAttribute(positions, 3));
    geom.setAttribute('color', new THREE.BufferAttribute(colors, 3));

    const mat = new THREE.PointsMaterial({
      size: 2.2, vertexColors: true, transparent: true, opacity: 0.85,
      blending: THREE.AdditiveBlending, depthWrite: false,
    });
    const pts = new THREE.Points(geom, mat);
    scene.add(pts);

    let raf, t0 = performance.now();
    let visible = true;
    const io = new IntersectionObserver(([e]) => { visible = e.isIntersecting; }, { threshold: 0.01 });
    io.observe(mount);

    const tick = () => {
      raf = requestAnimationFrame(tick);
      if (!visible) return;
      const t = (performance.now() - t0) / 1000;
      const pos = geom.getAttribute('position');
      for (let i = 0; i < count; i++) {
        let y = pos.array[i*3+1] + speeds[i] * 0.016;
        if (y > H/2) y = -H/2 - Math.random() * 50;
        pos.array[i*3+1] = y;
        pos.array[i*3+0] += Math.sin(t * 0.4 + i) * 0.15;
      }
      pos.needsUpdate = true;
      renderer.render(scene, camera);
    };
    tick();

    const onResize = () => {
      W = mount.clientWidth; H = mount.clientHeight;
      camera.left = -W/2; camera.right = W/2; camera.top = H/2; camera.bottom = -H/2;
      camera.updateProjectionMatrix();
      renderer.setSize(W, H);
    };
    const ro = new ResizeObserver(onResize); ro.observe(mount);

    return () => {
      cancelAnimationFrame(raf); ro.disconnect(); io.disconnect();
      try { mount.removeChild(renderer.domElement); } catch (e) {}
      geom.dispose(); mat.dispose(); renderer.dispose();
    };
  }, [count]);

  return <div ref={mountRef} style={{ position: 'absolute', inset: 0, pointerEvents: 'none' }} />;
}

Object.assign(window, { Globe, ParticleField, latLonToVec3, gridToTexture });
