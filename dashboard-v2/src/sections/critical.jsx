// Section 6 — REGARD CRITIQUE: "Ce que les données ne disent pas"

function Critical() {
  const [ref, , seen] = useInView({ threshold: 0.1 });
  const jumps = window.CFSR_JUMPS;
  const [hover, setHover] = useState(null);
  const [picked, setPicked] = useState(null);
  // Detail = picked has priority over hover (click sticks until next click)
  const selected = picked || hover;

  return (
    <section ref={ref} className="section" id="sec-6" data-screen-label="06 Critical">
      <SectionHeader
        act="06"
        kicker="Regard critique"
        title='Trois <span class="text-hot">limites</span> que cette analyse ne cache pas.'
        accent="var(--hot1)"
      />

      {/* CFSR jump timeline */}
      <div className="glass" style={{ padding: 28, marginBottom: 32, position: 'relative', zIndex: 2 }}>
        <div className="hstack" style={{ justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 14 }}>
          <div>
            <div className="mono" style={{ fontSize: 13, color: 'var(--text-dim)', letterSpacing: '0.14em', textTransform: 'uppercase' }}>Discontinuité instrumentale</div>
            <div className="display" style={{ fontSize: 26, color: 'var(--text)', marginTop: 4 }}>Saut CFSR → CFSv2 · janvier 2011</div>
          </div>
          <div style={{ textAlign: 'right' }}>
            <div className="mono" style={{ fontSize: 13, color: 'var(--text-dim)' }}>significatif sur</div>
            <div className="display tabular" style={{ fontSize: 28, color: 'var(--hot1)' }}>17/21<span className="mono" style={{ fontSize: 14, color: 'var(--text-dim)' }}> vars</span></div>
          </div>
        </div>

        <p style={{ fontSize: 16, marginBottom: 24, maxWidth: 760 }}>
          La fusion des séries CFSR (1979-2010) et CFSv2 (2011-) introduit un saut
          artificiel dans plusieurs variables. R² du modèle multivarié sur résidus
          passe de <span className="mono text-hot">0.75</span> →
          <span className="mono text-cold"> 0.46</span> après homogénéisation. Le couplage
          climat-CO₂ est <strong>réel</strong>, mais une partie de sa force apparente
          venait de cette discontinuité.
        </p>

        {/* Timeline with jump */}
        <CFSRTimeline jumps={jumps} hover={hover} setHover={setHover} picked={picked} setPicked={setPicked} />

        {/* Selected variable detail (click sticks, hover is transient preview) */}
        {selected && (
          <div style={{ marginTop: 20, padding: '16px 20px', background: 'rgba(255,107,53,0.06)', borderRadius: 10, border: '1px solid rgba(255,107,53,0.2)', position: 'relative' }}>
            <div className="hstack" style={{ gap: 24, alignItems: 'center', flexWrap: 'wrap' }}>
              <div>
                <div className="mono" style={{ fontSize: 13, color: 'var(--text-dim)' }}>Variable</div>
                <div className="display" style={{ fontSize: 22, color: 'var(--hot1)' }}>{selected.var}</div>
              </div>
              <div>
                <div className="mono" style={{ fontSize: 13, color: 'var(--text-dim)' }}>Saut</div>
                <div className="mono tabular" style={{ fontSize: 22, color: 'var(--text)' }}>{selected.jumpSD > 0 ? '+' : ''}{selected.jumpSD.toFixed(2)} σ</div>
              </div>
              <div>
                <div className="mono" style={{ fontSize: 13, color: 'var(--text-dim)' }}>Variation</div>
                <div className="mono tabular" style={{ fontSize: 22, color: selected.jumpPct < 0 ? 'var(--cold1)' : 'var(--hot1)' }}>{selected.jumpPct > 0 ? '+' : ''}{selected.jumpPct.toFixed(1)}%</div>
              </div>
              <div>
                <div className="mono" style={{ fontSize: 13, color: 'var(--text-dim)' }}>p-value</div>
                <div className="mono tabular" style={{ fontSize: 22, color: 'var(--green)' }}>&lt; 0.001</div>
              </div>
              {picked && (
                <button
                  onClick={() => setPicked(null)}
                  title="Désélectionner"
                  style={{
                    marginLeft: 'auto', background: 'rgba(255,255,255,0.06)',
                    border: '1px solid rgba(255,255,255,0.1)', color: 'var(--text-dim)',
                    fontSize: 12, padding: '6px 12px', borderRadius: 6, cursor: 'pointer',
                  }}
                >× Désélectionner</button>
              )}
            </div>
          </div>
        )}
      </div>

      {/* 3 limitations cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 18, marginBottom: 32, position: 'relative', zIndex: 2 }}>
        <LimitCard num="01" title="Détendrage linéaire" desc="Nos résidus sont obtenus en retirant une droite. Or la croissance CO₂ est très bien décrite par un polynôme cubique. Une partie du signal détendré contient encore du résidu de courbure." />
        <LimitCard num="02" title="Échelle globale masque" desc="Les puits de carbone (forêts boréales, océans) et les sources (déforestation, feux) ont des dynamiques locales opposées. La moyenne globale annule des phénomènes physiquement majeurs." />
        <LimitCard num="03" title="Discontinuités d'instruments" desc="CFSR → CFSv2 (2011), mais aussi les changements de satellites, la couverture station-météo, créent des sauts non-climatiques que la méthode statistique peut prendre pour du signal." />
      </div>

      {/* Footer */}
      <div className="glass" style={{ padding: '20px 28px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 24, flexWrap: 'wrap' }}>
        <div>
          <div className="mono" style={{ fontSize: 13, color: 'var(--text-dim)', letterSpacing: '0.14em', textTransform: 'uppercase', marginBottom: 4 }}>Sources données</div>
          <div className="hstack" style={{ gap: 14, fontFamily: 'JetBrains Mono', fontSize: 14, color: 'var(--text)', flexWrap: 'wrap' }}>
            <span>NOAA·GMD</span>
            <span style={{ color: 'var(--text-dim)' }}>·</span>
            <span>NCAR / NCEP CFSR / CFSv2</span>
            <span style={{ color: 'var(--text-dim)' }}>·</span>
            <span>Global Carbon Project</span>
            <span style={{ color: 'var(--text-dim)' }}>·</span>
            <span>Vostok ice core (Petit et al. 1999)</span>
          </div>
        </div>
        <div style={{ textAlign: 'right' }}>
          <div className="mono" style={{ fontSize: 10, color: 'var(--text-dim)', letterSpacing: '0.14em' }}>ESSAI 1A · Migration R → Python</div>
          <div className="mono" style={{ fontSize: 10, color: 'var(--text-dim)', marginTop: 4 }}>Climate × CO₂ · 2025</div>
        </div>
      </div>
    </section>
  );
}

function CFSRTimeline({ jumps, hover, setHover, picked, setPicked }) {
  const W = 1080, H = 200;
  const padL = 80, padR = 80;
  const yearToX = (y) => padL + ((y - 1979) / (2025 - 1979)) * (W - padL - padR);
  const splitX = yearToX(2011);

  const onLineClick = (j) => {
    // Toggle : click again on same line → unpick. Click another → switch.
    if (picked && picked.var === j.var) setPicked(null);
    else setPicked(j);
  };

  return (
    <svg viewBox={`0 0 ${W} ${H}`} style={{ width: '100%', height: 'auto', display: 'block' }}>
      {/* Period bands */}
      <rect x={padL} y={30} width={splitX - padL} height={H - 70} fill="rgba(0,217,255,0.04)" />
      <rect x={splitX} y={30} width={W - padR - splitX} height={H - 70} fill="rgba(255,107,53,0.04)" />
      <text x={(padL + splitX) / 2} y={48} textAnchor="middle" fontFamily="JetBrains Mono" fontSize="10" fill="rgba(0,217,255,0.7)">CFSR · 1979-2010</text>
      <text x={(splitX + W - padR) / 2} y={48} textAnchor="middle" fontFamily="JetBrains Mono" fontSize="10" fill="rgba(255,107,53,0.7)">CFSv2 · 2011-2025</text>

      {/* Split line */}
      <line x1={splitX} y1={30} x2={splitX} y2={H - 40} stroke="#FF6B35" strokeWidth="1.4" strokeDasharray="4 4" />
      <text x={splitX} y={H - 24} textAnchor="middle" fontFamily="JetBrains Mono" fontSize="11" fill="#FF6B35" fontWeight="600">JAN 2011</text>

      {/* Variables as horizontal lines, with jump indicated */}
      {jumps.map((j, i) => {
        const y = 70 + i * 22;
        const isHover = hover && hover.var === j.var;
        const isPicked = picked && picked.var === j.var;
        const isActive = isHover || isPicked;
        const dx = (j.jumpSD / 2) * 30; // visual jump amplitude
        return (
          <g key={j.var}
            onMouseEnter={() => setHover(j)}
            onMouseLeave={() => setHover(null)}
            onClick={() => onLineClick(j)}
            style={{ cursor: 'pointer' }}>
            {/* Selection highlight: precise polyline along the actual L-shape (before → jump → after) */}
            {isPicked && (
              <polyline
                points={`${padL - 50},${y} ${splitX},${y} ${splitX},${y - dx} ${W - padR + 50},${y - dx}`}
                fill="none"
                stroke="rgba(255,107,53,0.18)"
                strokeWidth={14}
                strokeLinecap="round"
                strokeLinejoin="round" />
            )}
            {/* Invisible thick hit-area for easier clicking — follows the actual L-shape */}
            <polyline
              points={`${padL - 40},${y} ${splitX},${y} ${splitX},${y - dx} ${W - padR + 40},${y - dx}`}
              fill="none"
              stroke="transparent"
              strokeWidth={20}
              style={{ pointerEvents: 'stroke' }} />
            {/* before */}
            <line x1={padL} x2={splitX} y1={y} y2={y}
              stroke={isActive ? '#00D9FF' : 'rgba(0,217,255,0.4)'}
              strokeWidth={isPicked ? 2.5 : (isHover ? 2 : 1.4)} />
            {/* jump */}
            <line x1={splitX} x2={splitX} y1={y} y2={y - dx}
              stroke="#FF6B35"
              strokeWidth={isPicked ? 3 : (isHover ? 2.5 : 1.5)} />
            {/* after */}
            <line x1={splitX} x2={W - padR} y1={y - dx} y2={y - dx}
              stroke={isActive ? '#FF6B35' : 'rgba(255,107,53,0.4)'}
              strokeWidth={isPicked ? 2.5 : (isHover ? 2 : 1.4)} />
            {/* label */}
            <text x={padL - 10} y={y + 3.5} textAnchor="end"
              fontFamily="JetBrains Mono" fontSize="11"
              fontWeight={isPicked ? 700 : 400}
              fill={isActive ? '#fff' : 'rgba(245,245,247,0.7)'}>
              {j.var}
            </text>
            <text x={W - padR + 8} y={y - dx + 3.5}
              fontFamily="JetBrains Mono" fontSize="10"
              fontWeight={isPicked ? 700 : 400}
              fill={isActive ? '#FF6B35' : 'rgba(255,107,53,0.5)'}>
              {j.jumpSD > 0 ? '+' : ''}{j.jumpSD.toFixed(2)}σ
            </text>
          </g>
        );
      })}
    </svg>
  );
}

function LimitCard({ num, title, desc }) {
  return (
    <div className="glass" style={{ padding: '24px 24px', display: 'flex', flexDirection: 'column', gap: 12 }}>
      <div className="mono" style={{ fontSize: 28, color: 'var(--hot1)', fontWeight: 600, letterSpacing: '-0.04em' }}>{num}</div>
      <div className="display" style={{ fontSize: 20, color: 'var(--text)' }}>{title}</div>
      <p style={{ fontSize: 15, lineHeight: 1.55 }}>{desc}</p>
    </div>
  );
}

// About modal
function AboutModal({ open, onClose }) {
  if (!open) return null;
  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal" onClick={(e) => e.stopPropagation()}>
        <div className="hstack" style={{ justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 18 }}>
          <div>
            <div className="mono" style={{ fontSize: 10, letterSpacing: '0.16em', color: 'var(--text-dim)', textTransform: 'uppercase' }}>À propos</div>
            <div className="display" style={{ fontSize: 24, color: 'var(--text)', marginTop: 4 }}>ESSAI 1A · Migration R → Python</div>
          </div>
          <button onClick={onClose} style={{ background: 'none', border: 'none', color: 'var(--text-dim)', fontSize: 22, cursor: 'pointer', padding: 4 }}>×</button>
        </div>

        <p style={{ fontSize: 14, color: 'var(--text)', marginBottom: 14, lineHeight: 1.6 }}>
          Ce dashboard est l'aboutissement d'un travail d'étudiant ingénieur :
          migrer un pipeline statistique R vers Python, l'industrialiser, et
          rendre <strong>visible</strong> ce que les chiffres expriment.
        </p>

        <div className="divider" style={{ margin: '16px 0' }} />

        <div style={{ display: 'flex', flexDirection: 'column', gap: 10, fontSize: 13, color: 'var(--text-dim)' }}>
          <div className="hstack" style={{ gap: 12 }}>
            <span className="mono" style={{ minWidth: 80, color: 'var(--text-dim)' }}>DONNÉES</span>
            <span>NOAA Global Monitoring · NCAR/NCEP CFSR & CFSv2 · 1979 — 2025</span>
          </div>
          <div className="hstack" style={{ gap: 12 }}>
            <span className="mono" style={{ minWidth: 80, color: 'var(--text-dim)' }}>VARIABLES</span>
            <span>21 variables climatiques + CO₂ atmosphérique Mauna Loa</span>
          </div>
          <div className="hstack" style={{ gap: 12 }}>
            <span className="mono" style={{ minWidth: 80, color: 'var(--text-dim)' }}>MÉTHODES</span>
            <span>Mann-Kendall · Sen slope · Pearson/Spearman · Granger · Régression Newey-West</span>
          </div>
          <div className="hstack" style={{ gap: 12 }}>
            <span className="mono" style={{ minWidth: 80, color: 'var(--text-dim)' }}>RÉSOLUTION</span>
            <span>0.5° (720×361 px) → grille 36×18 pour visualisation 3D</span>
          </div>
        </div>

        <div className="divider" style={{ margin: '20px 0' }} />

        <p style={{ fontSize: 12, color: 'var(--text-dim)' }}>
          Toutes les valeurs affichées sont issues du pipeline. Aucune
          interpolation décorative. Les hotspots ont été sélectionnés a priori
          pour leur rôle dans le cycle global du carbone.
        </p>
      </div>
    </div>
  );
}

window.Critical = Critical;
window.AboutModal = AboutModal;
