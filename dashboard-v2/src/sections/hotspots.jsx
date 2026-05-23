// Section 5 — RÉGIONS QUI COMPTENT: "Hotspots & amplification"

function Hotspots() {
  const [ref, , seen] = useInView({ threshold: 0.05 });
  const hotspots = window.HOTSPOTS;
  const bands = window.BAND_TRENDS;
  const regions = window.REG_ZONE;

  return (
    <section ref={ref} className="section" id="sec-5" data-screen-label="05 Hotspots">
      <div className="aurora" />
      <SectionHeader
        act="05"
        kicker="Hotspots & amplification"
        title='4 régions, 5 latitudes, <span class="text-hot">une géographie inégale</span>.'
        accent="var(--hot1)"
      />

      {/* Hotspot grid 2x2 */}
      <div style={{
        display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 18,
        marginBottom: 56, position: 'relative', zIndex: 2,
      }}>
        {hotspots.map((hs, i) => (
          <HotspotCard key={hs.name} hs={hs} delay={i * 120} paused={!seen} />
        ))}
      </div>

      {/* Amplification thermometer + R² radar */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 24, position: 'relative', zIndex: 2 }}>
        <div className="glass" style={{ padding: 28 }}>
          <div className="mono" style={{ fontSize: 13, color: 'var(--text-dim)', letterSpacing: '0.14em', textTransform: 'uppercase', marginBottom: 6 }}>
            Tendance T2m par bande de latitude
          </div>
          <div className="display" style={{ fontSize: 22, color: 'var(--text)', marginBottom: 4 }}>Amplification arctique</div>
          <p style={{ fontSize: 16, marginBottom: 20 }}>
            La bande boréale chauffe <strong className="text-hot">4× plus vite</strong> que la
            zone tropicale. La bande australe — paradoxe — se refroidit légèrement.
          </p>
          <AmpThermometer bands={bands} />
        </div>

        <div className="glass" style={{ padding: 28 }}>
          <div className="mono" style={{ fontSize: 13, color: 'var(--text-dim)', letterSpacing: '0.14em', textTransform: 'uppercase', marginBottom: 6 }}>
            R² climat → CO₂ par zone
          </div>
          <div className="display" style={{ fontSize: 22, color: 'var(--text)', marginBottom: 4 }}>Où l'empreinte est-elle nette ?</div>
          <p style={{ fontSize: 16, marginBottom: 20 }}>
            Les bandes globales et tropicales expliquent <strong className="text-cold">~75% / 69%</strong> du
            CO₂ résiduel. Les hotspots locaux : <strong>moins de 10%</strong>.
          </p>
          <R2Radar regions={regions} />
        </div>
      </div>
    </section>
  );
}

// Mini-globe + stats for one hotspot
function HotspotCard({ hs, delay, paused }) {
  const tw = useContext(window.TweaksContext) || {};
  const trendStrength = tw.trendStrength ?? 1.0;
  const segments = Math.min(tw.detail ?? 64, 96); // cap mini at 96 for perf
  // Build a tighter-focused grid centered on this hotspot's lat (boost intensity around it)
  const grid = useMemo(() => {
    const base = window.T2M_TREND_GRID;
    // Slight amplification near the hotspot for visual emphasis
    return base.map((row, ri) => row.map((cell, ci) => {
      const lat = -85 + ri * 10;
      const lon = ci * 10;
      const dLat = Math.abs(lat - hs.centerLat);
      const dLon = Math.abs(((lon - hs.centerLon + 540) % 360) - 180);
      const dist = Math.sqrt(dLat * dLat + dLon * dLon);
      const boost = Math.max(0, 1 - dist / 35) * 0.4;
      return cell * (1 + boost);
    }));
  }, [hs.centerLat, hs.centerLon]);

  const minigrangerLabel = hs.grangerXtoCO2 >= 3 ? 'Forte avance climat' : hs.grangerXtoCO2 >= 1 ? 'Avance partielle' : 'Aucune avance';

  return (
    <div className="glass" style={{
      padding: 20, position: 'relative',
      animation: `slideUp 800ms var(--ease-expo) ${delay}ms both`,
      display: 'grid', gridTemplateColumns: '180px 1fr', gap: 20, alignItems: 'stretch',
    }}>
      {/* Mini globe */}
      <div style={{ position: 'relative', width: 180, height: 180, borderRadius: 10, overflow: 'hidden', background: 'radial-gradient(50% 50% at 50% 50%, rgba(0,217,255,0.06), transparent 65%)' }}>
        <Globe
          grid={grid}
          autoRotate={false}
          cameraDistance={2.0}
          initialLon={hs.centerLon}
          initialLat={hs.centerLat}
          segments={segments}
          interactive={false}
          paused={paused}
          showAtmosphere={tw.atmosphere !== false}
          showTrend={1.0 * trendStrength}
          showGrid={false}
        />
        {/* highlight dot */}
        <div style={{
          position: 'absolute', left: '50%', top: '50%',
          width: 22, height: 22, borderRadius: '50%',
          border: `1.5px solid ${hs.color}`,
          transform: 'translate(-50%, -50%)',
          boxShadow: `0 0 20px ${hs.color}55`,
          pointerEvents: 'none',
        }} />
      </div>

      {/* Stats */}
      <div style={{ display: 'flex', flexDirection: 'column' }}>
        <div className="hstack" style={{ justifyContent: 'space-between', marginBottom: 4 }}>
          <span className="display" style={{ fontSize: 22, color: hs.color }}>{hs.name}</span>
          <span className="mono" style={{ fontSize: 12, color: 'var(--text-dim)' }}>{hs.label}</span>
        </div>
        <div style={{ fontSize: 14, color: 'var(--text-dim)', marginBottom: 14 }}>{hs.role}</div>

        {/* Radial mini-charts: 4 vars */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr 1fr', gap: 8, marginBottom: 12 }}>
          {Object.entries(hs.vars).map(([k, v]) => (
            <RadialChip key={k} label={k} val={v.sen} max={0.5} color={hs.color} />
          ))}
        </div>

        <div className="hstack" style={{ gap: 18, marginTop: 'auto', paddingTop: 8, borderTop: '1px solid rgba(255,255,255,0.06)' }}>
          <div>
            <div className="mono" style={{ fontSize: 12, color: 'var(--text-dim)' }}>GRANGER X→CO₂</div>
            <div className="display tabular" style={{ fontSize: 22, color: hs.color }}>{hs.grangerXtoCO2}<span className="mono" style={{ fontSize: 14, color: 'var(--text-dim)' }}>/4</span></div>
          </div>
          <div>
            <div className="mono" style={{ fontSize: 12, color: 'var(--text-dim)' }}>R² CO₂</div>
            <div className="display tabular" style={{ fontSize: 22, color: 'var(--text)' }}>{hs.R2.toFixed(3)}</div>
          </div>
          <div>
            <div className="mono" style={{ fontSize: 12, color: 'var(--text-dim)' }}>SENS</div>
            <div style={{ fontSize: 14, color: hs.color, marginTop: 4 }}>{minigrangerLabel}</div>
          </div>
        </div>
      </div>
    </div>
  );
}

function RadialChip({ label, val, max, color }) {
  const t = Math.min(1, Math.abs(val) / max);
  const circumf = 2 * Math.PI * 14;
  const dash = circumf * t;
  return (
    <div style={{ textAlign: 'center' }}>
      <svg viewBox="0 0 40 40" width="100%" style={{ display: 'block' }}>
        <circle cx="20" cy="20" r="14" fill="none" stroke="rgba(255,255,255,0.08)" strokeWidth="2.5" />
        <circle cx="20" cy="20" r="14" fill="none" stroke={val < 0 ? '#00D9FF' : color} strokeWidth="2.5"
          strokeDasharray={`${dash} ${circumf}`} strokeLinecap="round"
          transform="rotate(-90 20 20)" />
        <text x="20" y="22" textAnchor="middle" fontFamily="JetBrains Mono" fontSize="7.5" fill="#F5F5F7">
          {val >= 0 ? '+' : ''}{val.toFixed(2)}
        </text>
      </svg>
      <div className="mono" style={{ fontSize: 12, color: 'var(--text-dim)', marginTop: 2 }}>{label}</div>
    </div>
  );
}

// Thermometer for latitude bands
function AmpThermometer({ bands }) {
  const order = ['boreal','temperate_N','tropical','temperate_S','austral'];
  const ordered = order.map(o => bands.find(b => b.band === o));
  const maxAbs = Math.max(...ordered.map(b => Math.abs(b.senT2m)));
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
      {ordered.map((b, i) => {
        const t = b.senT2m / maxAbs;
        const w = Math.abs(t) * 100;
        const isNeg = b.senT2m < 0;
        const color = isNeg ? '#00D9FF' : (b.band === 'boreal' ? '#FF6B35' : b.band === 'temperate_N' ? '#F7931E' : '#FFB627');
        return (
          <div key={b.band}>
            <div className="hstack" style={{ justifyContent: 'space-between', marginBottom: 4 }}>
              <span className="mono" style={{ fontSize: 11, color: 'var(--text)' }}>{b.band.replace('_', ' ').padEnd(12)}</span>
              <span className="mono tabular" style={{ fontSize: 11, color }}>{b.senT2m > 0 ? '+' : ''}{(b.senT2m * 1000).toFixed(1)} mK/an</span>
            </div>
            <div style={{ height: 8, background: 'rgba(255,255,255,0.05)', borderRadius: 4, position: 'relative', overflow: 'hidden' }}>
              <div style={{
                position: 'absolute', top: 0, bottom: 0,
                left: isNeg ? `${50 - w/2}%` : '50%',
                width: `${w/2}%`,
                background: `linear-gradient(to ${isNeg ? 'left' : 'right'}, ${color}aa, ${color})`,
                borderRadius: 3,
                transition: 'width 1200ms var(--ease-expo)',
              }} />
              <div style={{ position: 'absolute', top: 0, bottom: 0, left: '50%', width: 1, background: 'rgba(255,255,255,0.18)' }} />
            </div>
            <div className="mono" style={{ fontSize: 9, color: 'var(--text-dim)', marginTop: 2 }}>{b.latRange}</div>
          </div>
        );
      })}
    </div>
  );
}

// Radar chart for R² across zones
function R2Radar({ regions }) {
  const W = 360, H = 360, cx = W/2, cy = H/2;
  const R = 140;
  const N = regions.length;
  const angle = (i) => -Math.PI/2 + (i / N) * 2 * Math.PI;
  const maxR2 = 0.8;
  const point = (i, r2) => {
    const r = (r2 / maxR2) * R;
    return [cx + Math.cos(angle(i)) * r, cy + Math.sin(angle(i)) * r];
  };
  const path = regions.map((reg, i) => {
    const [x, y] = point(i, reg.R2);
    return `${i === 0 ? 'M' : 'L'}${x.toFixed(1)},${y.toFixed(1)}`;
  }).join(' ') + ' Z';
  return (
    <svg viewBox={`0 0 ${W} ${H}`} style={{ width: '100%', height: 'auto', display: 'block' }}>
      {/* Concentric */}
      {[0.2, 0.4, 0.6, 0.8].map((g, i) => (
        <circle key={i} cx={cx} cy={cy} r={(g / maxR2) * R} fill="none" stroke="rgba(255,255,255,0.06)" />
      ))}
      {[0.2, 0.4, 0.6, 0.8].map((g, i) => (
        <text key={'l'+i} x={cx + 4} y={cy - (g / maxR2) * R - 2} fontSize="9" fontFamily="JetBrains Mono" fill="rgba(255,255,255,0.25)">{g}</text>
      ))}
      {/* Spokes */}
      {regions.map((reg, i) => {
        const [x, y] = point(i, maxR2);
        return <line key={'s'+i} x1={cx} y1={cy} x2={x} y2={y} stroke="rgba(255,255,255,0.05)" />;
      })}
      {/* Polygon */}
      <path d={path} fill="rgba(82,255,184,0.18)" stroke="#52FFB8" strokeWidth="1.6" />
      {/* Points + labels */}
      {regions.map((reg, i) => {
        const [px, py] = point(i, reg.R2);
        const [lx, ly] = point(i, maxR2 * 1.12);
        const isHotspot = reg.type === 'hotspot';
        return (
          <g key={reg.zone}>
            <circle cx={px} cy={py} r="3.5" fill={isHotspot ? '#FF6B35' : '#52FFB8'} />
            <text x={lx} y={ly + 4} textAnchor={lx > cx + 10 ? 'start' : lx < cx - 10 ? 'end' : 'middle'}
              fontFamily="JetBrains Mono" fontSize="10"
              fill={isHotspot ? '#FF6B35' : '#9CA3AF'}>
              {reg.zone}
            </text>
            <text x={lx} y={ly + 16} textAnchor={lx > cx + 10 ? 'start' : lx < cx - 10 ? 'end' : 'middle'}
              fontFamily="JetBrains Mono" fontSize="9" fill="rgba(255,255,255,0.5)">
              {reg.R2.toFixed(2)}
            </text>
          </g>
        );
      })}
    </svg>
  );
}

window.Hotspots = Hotspots;
