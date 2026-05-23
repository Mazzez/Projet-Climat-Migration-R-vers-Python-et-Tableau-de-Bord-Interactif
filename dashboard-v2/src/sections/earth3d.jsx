// Section 3 — TERRE 3D INTERACTIVE: "La carte du climat" (CENTERPIECE)

// Format a legend bound — scientific for very small magnitudes, decimal otherwise.
function fmtBound(v, plus = false) {
  if (v == null || isNaN(v)) return '–';
  const sign = v >= 0 ? (plus ? '+' : '') : '−';
  const abs = Math.abs(v);
  if (abs === 0) return '0';
  if (abs < 0.001) return sign + abs.toExponential(1).replace('e', '·10');
  if (abs < 1)    return sign + abs.toFixed(3);
  if (abs < 10)   return sign + abs.toFixed(2);
  return sign + abs.toFixed(1);
}

function Earth3D() {
  const [ref, , seen] = useInView({ threshold: 0.1 });
  const tw = useContext(window.TweaksContext) || {};
  const trendStrength = tw.trendStrength ?? 1.0;
  const bigSegments = tw.bigSegments ?? 128;
  const bigDistance = tw.bigDistance ?? 2.4;
  const [variable, setVariable] = useState('T2m');
  const [mode, setMode] = useState('sen'); // 'sen' | 'corr'
  const [year, setYear] = useState(2025);
  const [activeBands, setActiveBands] = useState(['boreal', 'tropical', 'austral']);
  const [picked, setPicked] = useState(null);
  const [showHotspots, setShowHotspots] = useState(true);
  const [gridData, setGridData] = useState(null);

  const allVars = window.ALL_VARS_FULL;
  const hotspots = window.HOTSPOTS;

  // Lazy-load real Sen + corr grids from the phase3 pipeline (downsampled 18×36).
  useEffect(() => {
    fetch('data/trend_grids_36x18.json')
      .then(r => r.json())
      .then(d => setGridData(d))
      .catch(err => console.warn('[Earth3D] real grids load failed → fallback to T2m scaling', err));
  }, []);

  // Compute grid + scale + legend bounds + label.
  // Real path : use the loaded JSON for (variable, mode).
  // Fallback   : scale the T2M reference grid by |rResid| (rough proxy).
  const { grid, vmin, vmax, label, isReal } = useMemo(() => {
    const yearF = (year - 1979) / 46;
    const yearScale = 0.4 + 0.6 * yearF; // dramatize early years

    if (gridData && gridData.vars[variable] && gridData.vars[variable][mode]) {
      const m = gridData.vars[variable][mode];
      return {
        grid: m.grid.map(row => row.map(c => c * yearScale)),
        vmin: m.vmin,
        vmax: m.vmax,
        label: m.label,
        isReal: true,
      };
    }
    // Fallback
    const base = window.T2M_TREND_GRID;
    const v = allVars.find(x => x.var === variable) || allVars[0];
    let factor = 1;
    if (mode === 'sen' && variable !== 'T2m') {
      factor = (Math.abs(v.rResid) / 0.233) * 0.8;
    } else if (mode === 'corr') {
      factor = v.rResid * 1.4;
    }
    return {
      grid: base.map(row => row.map(c => c * factor * yearScale)),
      vmin: mode === 'sen' ? -0.06 : -1.0,
      vmax: mode === 'sen' ? +0.12 : +1.0,
      label: mode === 'sen' ? 'Pente Sen (K/an)' : 'Corr. CO₂',
      isReal: false,
    };
  }, [gridData, variable, mode, year]);

  const allVarOptions = ['T2m','T500','SPFH2m','PWAT','APCP','TCDC','DLWRF','ULWRF','DSWRF','USWRF','PRMSL','CSDSF','CSUSF','CSDLF','CSULF','CDUVB','DUVB','ALBDO'];

  const toggleBand = (b) => setActiveBands(s => s.includes(b) ? s.filter(x => x !== b) : [...s, b]);

  const variableMeta = allVars.find(v => v.var === variable);

  return (
    <section ref={ref} className="section" id="sec-3" data-screen-label="03 Earth 3D" style={{ minHeight: '120vh', padding: '96px 0 0', position: 'relative' }}>
      {/* Section header floating top */}
      <div style={{ padding: '0 56px 32px', position: 'relative', zIndex: 5 }}>
        <SectionHeader
          act="03"
          kicker="La carte du climat"
          title='Là où la <span class="text-hot">Terre se transforme</span>. <br/>Une variable, 47 ans, 18 fenêtres temporelles.'
          accent="var(--cold1)"
        />
      </div>

      {/* Big globe area */}
      <div style={{
        position: 'relative',
        width: '100%',
        height: '88vh',
        minHeight: 720,
        overflow: 'hidden',
      }}>
        <Globe
          grid={grid}
          vmin={vmin}
          vmax={vmax}
          autoRotate
          rotationSpeed={0.04}
          showTrend={1.0 * trendStrength}
          cameraDistance={bigDistance}
          hotspots={showHotspots ? hotspots : []}
          bands={activeBands}
          onHotspotClick={(hs) => setPicked(hs)}
          paused={!seen}
          segments={bigSegments}
          showGrid={tw.showGridLines !== false}
          showAtmosphere={tw.atmosphere !== false}
          showStars
          starCount={700}
        />

        {/* Floating control card — top right */}
        <div className="glass" style={{
          position: 'absolute', top: 28, right: 28,
          padding: 18, width: 300, zIndex: 4,
        }}>
          <div className="mono" style={{ fontSize: 12, letterSpacing: '0.14em', color: 'var(--text-dim)', textTransform: 'uppercase', marginBottom: 12 }}>
            Configuration
          </div>

          {/* Variable selector */}
          <div style={{ marginBottom: 14 }}>
            <div className="mono" style={{ fontSize: 12, color: 'var(--text-dim)', marginBottom: 6 }}>Variable</div>
            <select
              value={variable}
              onChange={(e) => setVariable(e.target.value)}
              style={{
                width: '100%', padding: '8px 10px',
                background: 'rgba(20,28,45,0.85)',
                color: 'var(--text)',
                border: '1px solid rgba(255,255,255,0.16)',
                borderRadius: 6,
                fontFamily: 'JetBrains Mono, monospace', fontSize: 13,
                outline: 'none', cursor: 'pointer',
                colorScheme: 'dark',
              }}
            >
              {allVarOptions.map(v => {
                const meta = allVars.find(x => x.var === v);
                return (
                  <option key={v} value={v} style={{ background: '#0F1426', color: '#F5F5F7' }}>
                    {v} — {meta ? meta.name : v}
                  </option>
                );
              })}
            </select>
          </div>

          {/* Mode toggle */}
          <div style={{ marginBottom: 14 }}>
            <div className="mono" style={{ fontSize: 12, color: 'var(--text-dim)', marginBottom: 6 }}>Représentation</div>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 4 }}>
              <button className={`btn-glass ${mode === 'sen' ? 'active' : ''}`} onClick={() => setMode('sen')}>Tendance Sen</button>
              <button className={`btn-glass ${mode === 'corr' ? 'active' : ''}`} onClick={() => setMode('corr')}>Corr. CO₂</button>
            </div>
          </div>

          {/* Year slider */}
          <div style={{ marginBottom: 14 }}>
            <div className="hstack" style={{ justifyContent: 'space-between', marginBottom: 4 }}>
              <span className="mono" style={{ fontSize: 12, color: 'var(--text-dim)' }}>Période 1979 →</span>
              <span className="mono tabular" style={{ fontSize: 14, color: 'var(--hot1)' }}>{year}</span>
            </div>
            <input type="range" min="1985" max="2025" value={year} onChange={(e) => setYear(+e.target.value)}
              style={{ width: '100%', accentColor: 'var(--hot1)' }} />
          </div>

          {/* Bands */}
          <div style={{ marginBottom: 14 }}>
            <div className="mono" style={{ fontSize: 12, color: 'var(--text-dim)', marginBottom: 6 }}>Bandes de latitude</div>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4 }}>
              {['austral','temperate_S','tropical','temperate_N','boreal'].map(b => (
                <button key={b} className={`btn-glass ${activeBands.includes(b) ? 'active' : ''}`} onClick={() => toggleBand(b)}
                  style={{ fontSize: 12, padding: '5px 10px' }}>
                  {b.replace('_', ' ')}
                </button>
              ))}
            </div>
          </div>

          {/* Hotspots toggle */}
          <div className="hstack" style={{ justifyContent: 'space-between' }}>
            <div className="mono" style={{ fontSize: 12, color: 'var(--text-dim)' }}>Hotspots</div>
            <button onClick={() => setShowHotspots(s => !s)}
              className={`btn-glass ${showHotspots ? 'active' : ''}`}
              style={{ fontSize: 12, padding: '5px 14px' }}>
              {showHotspots ? 'ON' : 'OFF'}
            </button>
          </div>
        </div>

        {/* Variable info card — top left */}
        <div className="glass" style={{
          position: 'absolute', top: 28, left: 28,
          padding: 18, width: 300, zIndex: 4,
        }}>
          <div className="mono" style={{ fontSize: 12, letterSpacing: '0.14em', color: 'var(--text-dim)', textTransform: 'uppercase', marginBottom: 8 }}>
            Variable affichée
          </div>
          <div className="display" style={{ fontSize: 28, color: 'var(--text)', marginBottom: 4 }}>{variable}</div>
          <div style={{ fontSize: 14, color: 'var(--text-dim)', marginBottom: 12 }}>{variableMeta?.name}</div>
          <div className="divider" style={{ margin: '12px 0' }} />
          <div className="hstack" style={{ justifyContent: 'space-between', fontSize: 13, marginBottom: 6 }}>
            <span className="text-dim mono">r résidus</span>
            <span className="mono tabular" style={{ color: variableMeta?.rResid > 0 ? 'var(--hot1)' : 'var(--cold1)' }}>
              {variableMeta?.rResid.toFixed(3)}
            </span>
          </div>
          <div className="hstack" style={{ justifyContent: 'space-between', fontSize: 13, marginBottom: 6 }}>
            <span className="text-dim mono">unité</span>
            <span className="mono tabular text-dim">{variableMeta?.unit}</span>
          </div>
          <div className="hstack" style={{ justifyContent: 'space-between', alignItems: 'center', fontSize: 13 }}>
            <span className="text-dim mono">causalité</span>
            <SensPill sens={variableMeta?.sens} />
          </div>
        </div>

        {/* Colormap legend — bottom right */}
        <div className="glass" style={{
          position: 'absolute', bottom: 28, right: 28,
          padding: '14px 18px', zIndex: 4,
        }}>
          <div className="hstack" style={{ gap: 8, marginBottom: 8 }}>
            <div className="mono" style={{ fontSize: 12, letterSpacing: '0.14em', color: 'var(--text-dim)', textTransform: 'uppercase' }}>
              {label}
            </div>
            <span title={isReal ? 'Grille réelle (pipeline 0.5°)' : 'Approximation visuelle'}
                  style={{
                    fontSize: 9, fontFamily: 'JetBrains Mono', padding: '2px 6px', borderRadius: 4,
                    background: isReal ? 'rgba(82,255,184,0.15)' : 'rgba(255,182,39,0.15)',
                    color: isReal ? 'var(--green)' : 'var(--hot3)',
                    letterSpacing: '0.05em',
                  }}>
              {isReal ? 'RÉEL' : 'APPROX'}
            </span>
          </div>
          <div style={{
            width: 240, height: 12, borderRadius: 6,
            background: 'linear-gradient(to right, #00D9FF, #4dabff, #f0f0f0, #FFB627, #FF6B35)',
          }} />
          <div className="hstack" style={{ justifyContent: 'space-between', marginTop: 4, fontSize: 11, fontFamily: 'JetBrains Mono', color: 'var(--text-dim)' }}>
            <span>{fmtBound(vmin)}</span>
            <span>0</span>
            <span>{fmtBound(vmax, true)}</span>
          </div>
        </div>

        {/* Drag hint — bottom left */}
        <div style={{
          position: 'absolute', bottom: 28, left: 28, zIndex: 4,
          fontFamily: 'JetBrains Mono, monospace', fontSize: 12, letterSpacing: '0.14em',
          color: 'var(--text-dim)', textTransform: 'uppercase',
        }}>
          <span style={{ opacity: 0.7 }}>↻ Glissez pour faire pivoter · cliquez un hotspot</span>
        </div>
      </div>

      {/* Drawer — hotspot detail */}
      <div className={`drawer ${picked ? 'open' : ''}`}>
        {picked && (
          <div>
            <div className="hstack" style={{ justifyContent: 'space-between', marginBottom: 20 }}>
              <div className="mono" style={{ fontSize: 10, letterSpacing: '0.14em', color: 'var(--text-dim)', textTransform: 'uppercase' }}>
                Hotspot · {picked.label}
              </div>
              <button onClick={() => setPicked(null)} style={{
                background: 'none', border: 'none', color: 'var(--text-dim)',
                fontSize: 18, cursor: 'pointer', padding: 4,
              }}>×</button>
            </div>
            <div className="display" style={{ fontSize: 40, color: picked.color, marginBottom: 6 }}>{picked.name}</div>
            <div style={{ fontSize: 13, color: 'var(--text-dim)', marginBottom: 24 }}>{picked.role}</div>

            <div className="divider" style={{ margin: '12px 0 20px' }} />

            <div className="mono" style={{ fontSize: 10, letterSpacing: '0.14em', color: 'var(--text-dim)', textTransform: 'uppercase', marginBottom: 12 }}>
              Tendances Sen & corrélation CO₂
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
              {Object.entries(picked.vars).map(([k, v]) => (
                <div key={k} style={{ padding: 14, background: 'rgba(255,255,255,0.03)', borderRadius: 8, border: '1px solid rgba(255,255,255,0.06)' }}>
                  <div className="hstack" style={{ justifyContent: 'space-between', marginBottom: 6 }}>
                    <span className="mono" style={{ fontSize: 11, fontWeight: 600, color: 'var(--text)' }}>{k}</span>
                    <span className="mono tabular" style={{ fontSize: 10, color: v.mkP < 0.05 ? picked.color : 'var(--text-dim)' }}>
                      p={v.mkP.toFixed(3)}
                    </span>
                  </div>
                  <div className="hstack" style={{ gap: 16, fontSize: 11 }}>
                    <div>
                      <div className="mono text-dim" style={{ fontSize: 9 }}>Sen /an</div>
                      <div className="mono tabular" style={{ color: v.sen > 0 ? 'var(--hot1)' : 'var(--cold1)' }}>{v.sen > 0 ? '+' : ''}{v.sen.toFixed(4)}</div>
                    </div>
                    <div>
                      <div className="mono text-dim" style={{ fontSize: 9 }}>r résidu CO₂</div>
                      <div className="mono tabular" style={{ color: 'var(--text)' }}>{v.rCO2 > 0 ? '+' : ''}{v.rCO2.toFixed(3)}</div>
                    </div>
                  </div>
                </div>
              ))}
            </div>

            <div className="divider" style={{ margin: '20px 0' }} />
            <div className="hstack" style={{ gap: 18 }}>
              <div>
                <div className="mono text-dim" style={{ fontSize: 10, letterSpacing: '0.1em' }}>GRANGER X→CO₂</div>
                <div className="display tabular" style={{ fontSize: 28, color: picked.color }}>{picked.grangerXtoCO2}<span className="mono" style={{ fontSize: 14, color: 'var(--text-dim)' }}>/4</span></div>
              </div>
              <div>
                <div className="mono text-dim" style={{ fontSize: 10, letterSpacing: '0.1em' }}>R² CO₂</div>
                <div className="display tabular" style={{ fontSize: 28, color: 'var(--text)' }}>{picked.R2.toFixed(3)}</div>
              </div>
            </div>
          </div>
        )}
      </div>
    </section>
  );
}

window.Earth3D = Earth3D;
