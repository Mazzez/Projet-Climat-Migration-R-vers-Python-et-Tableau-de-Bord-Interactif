// Section 2 — TRAJECTOIRE CO2: "La trace inéluctable"

function Trajectory() {
  const [ref, , seen] = useInView({ threshold: 0.15 });
  const [overlay, setOverlay] = useState('linear'); // linear | quad | cubic
  const [hoverIdx, setHoverIdx] = useState(null);
  const [pickedEvent, setPickedEvent] = useState(null);

  const series = window.CO2_ANNUAL; // 47 points
  const monthly = window.CO2_SERIES; // 564 points

  const W = 760, H = 360;
  const padL = 56, padR = 24, padT = 24, padB = 36;
  const yMin = 332, yMax = 432;
  const xToY = (year) => padT + ((1 - (year - 1979) / 46) * 0) + 0; // unused
  const sx = (year) => padL + ((year - 1979) / 46) * (W - padL - padR);
  const sy = (v) => padT + (1 - (v - yMin) / (yMax - yMin)) * (H - padT - padB);

  // Main CO2 path
  const mainPath = useMemo(() => {
    return monthly.map((d, i) => `${i === 0 ? 'M' : 'L'}${sx(d.year).toFixed(1)},${sy(d.value).toFixed(1)}`).join(' ');
  }, []);

  // Central trajectory for each model (1979 + y → ppm).
  // Linear coef from Sen 1.881 [IC 1.777-1.965]; quad/cubic kept to mimic observed curvature.
  const trajFn = useMemo(() => {
    const start = 336.78;
    return {
      linear: (y) => start + 1.881 * y,
      quad:   (y) => start + 1.78  * y + 0.003   * y * y,
      cubic:  (y) => start + 1.55  * y + 0.005   * y * y + 0.000015 * y * y * y,
    };
  }, []);

  // IC95 band around the SELECTED model. Half-width follows the linear Sen IC
  // (≈ 0.094 ppm/yr → grows ~ y ppm over 47 years), centred on the chosen overlay.
  const bandPath = useMemo(() => {
    const fn = trajFn[overlay];
    const halfWidth = (y) => 0.094 * y;
    const pts = [];
    for (let y = 0; y <= 46; y += 1) pts.push(y);
    const up = pts.map(y => `${sx(1979 + y).toFixed(1)},${sy(fn(y) + halfWidth(y)).toFixed(1)}`).join(' L');
    const dn = pts.slice().reverse().map(y => `${sx(1979 + y).toFixed(1)},${sy(fn(y) - halfWidth(y)).toFixed(1)}`).join(' L');
    return `M${up} L${dn} Z`;
  }, [overlay, trajFn]);

  // Overlay paths
  const overlayPaths = useMemo(() => {
    const arr = (fn) => {
      const out = [];
      for (let y = 0; y <= 46; y += 0.25) out.push([1979 + y, fn(y)]);
      return out;
    };
    const toPath = (arr) => arr.map(([y, v], i) => `${i === 0 ? 'M' : 'L'}${sx(y).toFixed(1)},${sy(v).toFixed(1)}`).join(' ');
    return {
      linear: toPath(arr(trajFn.linear)),
      quad:   toPath(arr(trajFn.quad)),
      cubic:  toPath(arr(trajFn.cubic)),
    };
  }, [trajFn]);

  // Hover scrub
  const svgRef = useRef(null);
  const onSvgMove = (e) => {
    const rect = svgRef.current.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const realX = (x / rect.width) * W;
    const year = 1979 + ((realX - padL) / (W - padL - padR)) * 46;
    const idx = Math.max(0, Math.min(monthly.length - 1, Math.round((year - 1979) * 12)));
    setHoverIdx(idx);
  };
  const onSvgLeave = () => setHoverIdx(null);

  const hoverData = hoverIdx != null ? monthly[hoverIdx] : null;

  const events = window.EVENTS;

  return (
    <section ref={ref} className="section" id="sec-2" data-screen-label="02 Trajectory">
      <div className="aurora" />
      <SectionHeader
        act="02"
        kicker="La trace inéluctable"
        title="Une pente <span class='text-hot'>quasi linéaire</span>. <br/>Une accélération qui se confirme."
        accent="var(--hot1)"
      />

      <div style={{ position: 'relative', zIndex: 2, display: 'grid', gridTemplateColumns: '1.5fr 1fr', gap: 24, alignItems: 'start' }}>
        {/* Left: chart */}
        <div className="glass" style={{ padding: 24, position: 'relative' }}>
          <div className="hstack" style={{ justifyContent: 'space-between', marginBottom: 14 }}>
            <div>
              <div className="mono" style={{ fontSize: 13, letterSpacing: '0.14em', color: 'var(--text-dim)', textTransform: 'uppercase' }}>CO₂ atmosphérique · Mauna Loa-style</div>
              <div style={{ fontSize: 15, color: 'var(--text-dim)' }}>1979 → 2025 · données mensuelles, série annuelle moyennée</div>
            </div>
            <div className="hstack" style={{ gap: 6 }}>
              {['linear','quad','cubic'].map(o => (
                <button key={o} className={`btn-glass ${overlay === o ? 'active' : ''}`} onClick={() => setOverlay(o)}>
                  {o === 'linear' ? 'Linéaire' : o === 'quad' ? 'Quadratique' : 'Cubique'}
                </button>
              ))}
            </div>
          </div>

          <svg ref={svgRef} viewBox={`0 0 ${W} ${H}`} style={{ width: '100%', height: 'auto', display: 'block' }}
               onMouseMove={onSvgMove} onMouseLeave={onSvgLeave}>
            <defs>
              <linearGradient id="co2grad" x1="0" y1="0" x2="1" y2="0">
                <stop offset="0%" stopColor="#00D9FF" />
                <stop offset="55%" stopColor="#FFB627" />
                <stop offset="100%" stopColor="#FF6B35" />
              </linearGradient>
              <linearGradient id="co2fill" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#FF6B35" stopOpacity="0.25" />
                <stop offset="100%" stopColor="#FF6B35" stopOpacity="0" />
              </linearGradient>
            </defs>

            {/* Y axis ticks */}
            {[340, 360, 380, 400, 420].map(v => (
              <g key={v}>
                <line x1={padL} x2={W - padR} y1={sy(v)} y2={sy(v)} stroke="rgba(255,255,255,0.06)" strokeDasharray="2 4" />
                <text x={padL - 8} y={sy(v) + 3} textAnchor="end" className="mono" fontSize="10" fill="#9CA3AF">{v}</text>
              </g>
            ))}
            {/* X axis */}
            {[1980, 1990, 2000, 2010, 2020, 2025].map(y => (
              <g key={y}>
                <text x={sx(y)} y={H - 12} textAnchor="middle" className="mono" fontSize="10" fill="#9CA3AF">{y}</text>
              </g>
            ))}
            <text x={padL - 8} y={padT + 4} textAnchor="end" className="mono" fontSize="9" fill="#9CA3AF">ppm</text>

            {/* IC band */}
            <path d={bandPath} fill="rgba(255, 182, 39, 0.10)" />

            {/* Overlay regression */}
            <path d={overlayPaths[overlay]} stroke={overlay === 'linear' ? '#FFB627' : overlay === 'quad' ? '#F7931E' : '#FF6B35'}
                  strokeWidth="1.4" strokeDasharray="6 4" fill="none" opacity="0.7" />

            {/* Main curve */}
            <path d={mainPath} stroke="url(#co2grad)" strokeWidth="1.8" fill="none" />

            {/* Events */}
            {events.map((ev, i) => (
              <g key={i} onClick={() => setPickedEvent(ev)} style={{ cursor: 'pointer' }}>
                <line x1={sx(ev.year)} x2={sx(ev.year)} y1={padT} y2={H - padB} stroke={ev.color} strokeOpacity="0.18" strokeDasharray="2 3" />
                <circle cx={sx(ev.year)} cy={H - padB + 14} r="3.5" fill={ev.color} />
              </g>
            ))}

            {/* Hover scrub */}
            {hoverData && (
              <g>
                <line x1={sx(hoverData.year)} x2={sx(hoverData.year)} y1={padT} y2={H - padB} stroke="#fff" strokeOpacity="0.3" />
                <circle cx={sx(hoverData.year)} cy={sy(hoverData.value)} r="4" fill="#fff" />
              </g>
            )}
          </svg>

          {/* Hover tooltip */}
          {hoverData && (
            <div className="glass" style={{
              position: 'absolute',
              left: `${(sx(hoverData.year) / W) * 100}%`,
              top: 60,
              transform: 'translateX(12px)',
              padding: '10px 14px', fontSize: 12,
              pointerEvents: 'none', zIndex: 4,
            }}>
              <div className="mono" style={{ color: 'var(--text-dim)', fontSize: 10 }}>{Math.floor(hoverData.year)} · M{(hoverData.month + 1).toString().padStart(2, '0')}</div>
              <div className="display tabular" style={{ fontSize: 22, color: 'var(--hot1)' }}>{hoverData.value.toFixed(2)}</div>
              <div className="mono" style={{ fontSize: 10, color: 'var(--text-dim)' }}>ppm CO₂</div>
            </div>
          )}

          {/* Legend */}
          <div className="hstack" style={{ marginTop: 12, gap: 18, fontSize: 14, color: 'var(--text-dim)' }}>
            <span className="hstack" style={{ gap: 6 }}>
              <span style={{ width: 14, height: 2, background: 'linear-gradient(to right, #00D9FF, #FF6B35)' }}></span>
              Mensuel
            </span>
            <span className="hstack" style={{ gap: 6 }}>
              <span style={{ width: 14, height: 2, background: '#FFB627', boxShadow: '0 0 0 1px #FFB627' }}></span>
              IC 95% Sen
            </span>
            <span className="hstack" style={{ gap: 6 }}>
              <span style={{ width: 14, height: 0, borderTop: '1.4px dashed #FF6B35' }}></span>
              Modèle {overlay}
            </span>
          </div>
        </div>

        {/* Right: metric cards */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
          <MetricCard
            label="Pente Sen (robuste)"
            value="+1.881"
            unit="ppm/an"
            sub={<>IC 95% bootstrap : <span className="mono text-hot">[1.78, 1.97]</span></>}
            spark={series.map(d => d.value)}
            accent="var(--hot1)"
          />
          <MetricCard
            label="Modèle exponentiel"
            value="0.5%"
            unit="/an"
            sub={<>Taux croissance instantané · doublement à <span className="mono text-hot">137 ans</span></>}
            accent="var(--hot2)"
          />
          <div className="glass" style={{ padding: 22 }}>
            <div className="mono" style={{ fontSize: 13, color: 'var(--text-dim)', textTransform: 'uppercase', letterSpacing: '0.14em' }}>Vs. paléoclimat (Vostok)</div>
            <div className="hstack" style={{ gap: 10, alignItems: 'baseline', marginTop: 8 }}>
              <span className="display tabular" style={{ fontSize: 40, color: 'var(--green)', lineHeight: 1 }}>30×</span>
              <span className="mono" style={{ fontSize: 15, color: 'var(--text-dim)' }}>plus rapide</span>
            </div>
            <div style={{ fontSize: 15, color: 'var(--text-dim)', marginTop: 8 }}>
              Le taux moderne dépasse le pic paléoclimatique enregistré dans la
              carotte de Vostok (414 ka).
            </div>
            {/* Mini paléo viz — Vostok 414 ka + modern arrow */}
            <svg viewBox="0 0 320 152" style={{ width: '100%', marginTop: 14 }}>
              {/* Layout :
                   plot area  : x ∈ [56, 290]  y ∈ [22, 108]
                   y-axis : 425 ppm (top, modern) → 180 ppm (bottom, glacial min)
                   x-axis : 414 ka BP (left)     → today (right)
              */}
              {(() => {
                const xMin = 56, xMax = 290, yTop = 22, yBot = 108;
                const ppmMin = 175, ppmMax = 430;
                const ageMax = 420000;
                const ppmToY = (p) => yTop + (1 - (p - ppmMin) / (ppmMax - ppmMin)) * (yBot - yTop);
                const ageToX = (age) => xMax - (age / ageMax) * (xMax - xMin);
                const yNatLow = ppmToY(180);
                const yNatHigh = ppmToY(300);
                const yModern = ppmToY(425);

                return <>
                  {/* Y-axis ticks */}
                  {[180, 300, 425].map(p => {
                    const y = ppmToY(p);
                    return (
                      <g key={p}>
                        <line x1={xMin - 4} x2={xMax} y1={y} y2={y} stroke="rgba(255,255,255,0.06)" strokeDasharray="2 3" />
                        <text x={xMin - 6} y={y + 3} textAnchor="end" fontSize="9" fontFamily="JetBrains Mono" fill="#9CA3AF">{p}</text>
                      </g>
                    );
                  })}
                  {/* Unit "ppm" placed clearly above the 425 tick — top of the Y-axis */}
                  <text x={xMin - 6} y={ppmToY(425) - 14} textAnchor="end"
                    fontSize="8" fontFamily="JetBrains Mono" fill="#9CA3AF" fontStyle="italic">ppm</text>

                  {/* Natural range band 180-300 ppm */}
                  <rect x={xMin} y={yNatHigh} width={xMax - xMin} height={yNatLow - yNatHigh}
                    fill="rgba(82,255,184,0.08)" />
                  <text x={xMin + 6} y={yNatHigh + 12} fontSize="9" fontFamily="JetBrains Mono" fill="#52FFB8" opacity="0.7">
                    plage naturelle paléo
                  </text>

                  {/* Vostok dots + connecting line */}
                  {(() => {
                    const sorted = window.VOSTOK_SAMPLE.slice().sort((a, b) => b.ageBP - a.ageBP);
                    const linePath = sorted.map((d, i) =>
                      `${i === 0 ? 'M' : 'L'}${ageToX(d.ageBP).toFixed(1)},${ppmToY(d.CO2).toFixed(1)}`
                    ).join(' ');
                    return <>
                      <path d={linePath} fill="none" stroke="#52FFB8" strokeOpacity="0.45" strokeWidth="1" />
                      {sorted.map((d, i) => (
                        <circle key={i} cx={ageToX(d.ageBP)} cy={ppmToY(d.CO2)} r="2.4" fill="#52FFB8" />
                      ))}
                    </>;
                  })()}

                  {/* Modern CO2 arrow (right side, dramatic upshoot) */}
                  <line x1={xMax + 4} x2={xMax + 4} y1={yNatLow} y2={yModern + 4}
                    stroke="#FF6B35" strokeWidth="2" />
                  <polygon points={`${xMax + 1},${yModern + 6} ${xMax + 7},${yModern + 6} ${xMax + 4},${yModern}`}
                    fill="#FF6B35" />
                  <circle cx={xMax + 4} cy={yModern} r="3" fill="#FF6B35" />
                  <text x={xMax + 10} y={yModern + 4} fontSize="10" fontFamily="JetBrains Mono" fill="#FF6B35" fontWeight="600">425</text>

                  {/* X-axis tick labels — 4 ticks.
                      "−20 ka" is on the first label row; "aujourd'hui" stacked on a second
                      row below, since they share almost the same X (12 px apart). */}
                  {[
                    { age: 414000, label: '−414 ka',      anchor: 'middle', row: 1 },
                    { age: 200000, label: '−200 ka',      anchor: 'middle', row: 1 },
                    { age:  20000, label: '−20 ka',       anchor: 'middle', row: 1 },
                    { age:      0, label: 'aujourd\'hui', anchor: 'end',    row: 2 },
                  ].map(t => {
                    const yLabel = yBot + (t.row === 1 ? 14 : 26);
                    return (
                      <g key={t.label}>
                        <line x1={ageToX(t.age)} x2={ageToX(t.age)} y1={yBot} y2={yBot + 3} stroke="#9CA3AF" />
                        <text x={ageToX(t.age) + (t.anchor === 'end' ? 8 : 0)}
                          y={yLabel} textAnchor={t.anchor} fontSize="9" fontFamily="JetBrains Mono"
                          fill={t.age === 0 ? '#FF6B35' : '#9CA3AF'} fontWeight={t.age === 0 ? 600 : 400}>
                          {t.label}
                        </text>
                      </g>
                    );
                  })}
                </>;
              })()}
            </svg>
          </div>
        </div>
      </div>

      {/* Timeline events */}
      <div style={{ marginTop: 40, position: 'relative', zIndex: 2 }}>
        <div className="mono" style={{ fontSize: 13, color: 'var(--text-dim)', letterSpacing: '0.14em', textTransform: 'uppercase', marginBottom: 16 }}>
          Événements marquants
        </div>
        <div className="glass" style={{ padding: '22px 28px', position: 'relative' }}>
          <div style={{ position: 'relative', height: 60 }}>
            <div style={{ position: 'absolute', top: 28, left: 12, right: 12, height: 1, background: 'rgba(255,255,255,0.12)' }} />
            {[1980, 1990, 2000, 2010, 2020].map(y => {
              const t = (y - 1979) / 46;
              return (
                <div key={y} style={{ position: 'absolute', left: `calc(12px + ${t * 100}% - ${t * 24}px)`, top: 36, fontSize: 10, color: 'var(--text-dim)', fontFamily: 'JetBrains Mono', transform: 'translateX(-50%)' }}>
                  {y}
                </div>
              );
            })}
            {events.map((ev, i) => {
              const t = (ev.year - 1979) / 46;
              const isPicked = pickedEvent && pickedEvent.name === ev.name;
              return (
                <button key={i}
                  onClick={() => setPickedEvent(isPicked ? null : ev)}
                  style={{
                    position: 'absolute', left: `calc(12px + ${t * 100}% - ${t * 24}px)`, top: 18,
                    transform: 'translateX(-50%)',
                    width: 22, height: 22, borderRadius: '50%',
                    background: isPicked ? ev.color : 'transparent',
                    border: `1.5px solid ${ev.color}`,
                    cursor: 'pointer',
                    padding: 0,
                    transition: 'all 280ms var(--ease-expo)',
                    boxShadow: isPicked ? `0 0 0 6px ${ev.color}22` : 'none',
                  }}
                  title={ev.name}
                />
              );
            })}
          </div>
          {pickedEvent && (
            <div style={{ marginTop: 18, padding: '16px 18px', background: 'rgba(255,255,255,0.03)', borderRadius: 10, border: '1px solid rgba(255,255,255,0.06)' }}>
              <div className="hstack" style={{ gap: 12, alignItems: 'baseline', marginBottom: 6 }}>
                <span className="display" style={{ fontSize: 22, color: pickedEvent.color }}>{pickedEvent.name}</span>
                <span className="mono" style={{ fontSize: 14, color: 'var(--text-dim)' }}>· {Math.floor(pickedEvent.year)}</span>
              </div>
              <div style={{ fontSize: 15, color: 'var(--text-dim)' }}>{pickedEvent.desc}</div>
            </div>
          )}
          {!pickedEvent && (
            <div style={{ marginTop: 14, fontSize: 14, color: 'var(--text-dim)' }}>
              Cliquez un marqueur pour détailler.
            </div>
          )}
        </div>
      </div>
    </section>
  );
}

window.Trajectory = Trajectory;
