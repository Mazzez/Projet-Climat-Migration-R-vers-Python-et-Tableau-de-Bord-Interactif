// Section 4 — LE LIEN CLIMAT ↔ CO2: "Qui cause qui ?"

function ClimateCO2Link() {
  const [ref, , seen] = useInView({ threshold: 0.15 });
  const [repr, setRepr] = useState('rResid');
  const vars = window.ALL_VARS_FULL;

  const reprs = [
    { key: 'rLevel', label: 'Niveaux bruts',
      desc: 'Niveaux non transformés. Dominés par la trend commune entre CO₂ et la plupart des variables. Beaucoup de corrélations spurieuses, peu interprétables.' },
    { key: 'rAnom', label: 'Anomalies',
      desc: 'Cycle saisonnier retiré, mais la trend de long terme reste. Encore confondu par la dérive partagée — utile pour visualiser le climat sans bruit annuel.' },
    { key: 'rResid', label: 'Résidus (détendrés)',
      desc: 'Signal interannuel propre, sans la trend commune. C’est le test rigoureux du couplage climat ↔ CO₂. La plupart des liens ici sont causaux.' },
    { key: 'rD1', label: 'Δ 1 mois',
      desc: 'Différences mois-à-mois. Met en avant les chocs rapides (volcans, ENSO). Bruit élevé, signal de court terme.' },
    { key: 'rD12', label: 'Δ 12 mois',
      desc: 'Anomalies annuelles glissantes. Retire l’effet saisonnier ET la trend basse fréquence. Plus exigeant que les résidus.' },
  ];
  const reprObj = reprs.find(r => r.key === repr);

  // Heatmap: 21 vars × 5 reprs as a 3D-feeling bar grid
  // For the focused repr, show bars with height = |r|, color = sign.

  // Granger Sankey data
  const grangerGroups = {
    'X -> CO2': [], 'CO2 -> X': [], 'bidirectionnel': [], 'aucun': [],
  };
  vars.forEach(v => { grangerGroups[v.sens].push(v); });
  const groupColors = {
    'X -> CO2': '#52FFB8',
    'CO2 -> X': '#00D9FF',
    'bidirectionnel': '#FF6B35',
    'aucun': 'rgba(255,255,255,0.3)',
  };

  return (
    <section ref={ref} className="section" id="sec-4" data-screen-label="04 Link" style={{ background: 'radial-gradient(80% 60% at 50% 50%, rgba(0,217,255,0.03), transparent), var(--bg)' }}>
      <SectionHeader
        act="04"
        kicker="Qui cause qui ?"
        title='Sur <span class="text-cold">15 variables sur 21</span>, le climat précède le CO₂. <br/>Ce n’est pas une rétroaction. C’est une <span class="text-hot">empreinte humaine</span>.'
        accent="var(--green)"
      />

      {/* Big number with Granger summary */}
      <div data-presenter="link-kpis" style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 32, marginBottom: 56, position: 'relative', zIndex: 2 }}>
        <div className="glass" style={{ padding: '36px 40px' }}>
          <div className="mono" style={{ fontSize: 13, letterSpacing: '0.16em', color: 'var(--text-dim)', textTransform: 'uppercase' }}>
            <GlossaryTerm term="Granger">Granger</GlossaryTerm> global — lag 6 mois
          </div>
          <div style={{ marginTop: 18, display: 'flex', alignItems: 'baseline', gap: 16 }}>
            <span className="display tabular" style={{ fontSize: 140, lineHeight: 0.9, color: 'var(--green)', letterSpacing: '-0.04em' }}>
              <CountUp value={15} duration={1800} />
            </span>
            <span className="mono" style={{ fontSize: 36, color: 'var(--text-dim)' }}>/ 21</span>
          </div>
          <div style={{ marginTop: 8, fontSize: 18, color: 'var(--text)', maxWidth: 480 }}>
            variables climatiques <span className="text-green">précèdent</span> le CO₂ atmosphérique avec une significativité statistique (<span className="mono">p &lt; 0.05</span>).
          </div>
          <div className="hstack" style={{ gap: 14, marginTop: 24, flexWrap: 'wrap' }}>
            <div className="pill pill-x">15 X → CO₂</div>
            <div className="pill pill-c">8 CO₂ → X</div>
            <div className="pill pill-bi">5 bidir.</div>
            <div className="pill pill-none">3 aucun</div>
          </div>
        </div>

        <div className="glass" style={{ padding: '36px 40px' }}>
          <div className="mono" style={{ fontSize: 13, letterSpacing: '0.16em', color: 'var(--text-dim)', textTransform: 'uppercase' }}>
            Modèle multivarié sur <GlossaryTerm term="résidus">résidus</GlossaryTerm>
          </div>
          <div style={{ marginTop: 18, display: 'flex', alignItems: 'baseline', gap: 16 }}>
            <span className="display tabular" style={{ fontSize: 100, lineHeight: 0.9, color: 'var(--hot1)', letterSpacing: '-0.04em' }}><GlossaryTerm term="R²">R²</GlossaryTerm>=<CountUp value={0.748} decimals={3} duration={1800} /></span>
          </div>
          <div style={{ marginTop: 12, fontSize: 17, color: 'var(--text-dim)' }}>
            12 variables climatiques résiduelles expliquent <strong className="text-hot">~75%</strong> du
            CO₂ résiduel — robuste à la dé-trend, et à l’autocorrélation (Newey-West).
          </div>
          <div className="divider" style={{ margin: '20px 0' }} />
          <div className="hstack" style={{ gap: 28 }}>
            <div>
              <div className="mono text-dim" style={{ fontSize: 13, letterSpacing: '0.1em' }}>CSDLF</div>
              <div className="mono tabular" style={{ fontSize: 22, color: 'var(--hot1)' }}>+7.84</div>
              <div className="mono text-dim" style={{ fontSize: 13 }}>W/m² · 47 ans</div>
            </div>
            <div style={{ fontSize: 15, color: 'var(--text-dim)', maxWidth: 240 }}>
              Le LW descendant ciel clair (signature directe des GES) monte de
              <strong className="text-hot"> +7.84 W/m²</strong>. C’est <em>la</em> preuve physique.
            </div>
          </div>
        </div>
      </div>

      {/* Heatmap + repr selector */}
      <div data-presenter="link-heatmap" style={{ display: 'grid', gridTemplateColumns: '1.7fr 1fr', gap: 32, marginBottom: 56, position: 'relative', zIndex: 2, alignItems: 'start' }}>
        <div className="glass" style={{ padding: 24, overflow: 'hidden' }}>
          <div className="hstack" style={{ justifyContent: 'space-between', marginBottom: 16 }}>
            <div>
              <div className="mono" style={{ fontSize: 13, color: 'var(--text-dim)', letterSpacing: '0.14em', textTransform: 'uppercase' }}>Corrélation Pearson · climat ↔ CO₂</div>
              <div style={{ fontSize: 15, color: 'var(--text-dim)' }}>21 variables × 5 représentations · saturation = |r|</div>
            </div>
          </div>
          <Heatmap vars={vars} repr={repr} reprs={reprs} setRepr={setRepr} />
        </div>

        <div className="glass" style={{ padding: 24, position: 'sticky', top: 80 }}>
          <div className="mono" style={{ fontSize: 13, color: 'var(--text-dim)', letterSpacing: '0.14em', textTransform: 'uppercase', marginBottom: 12 }}>
            Pédagogie — {reprObj.label}
          </div>
          <div className="display" style={{ fontSize: 32, color: 'var(--cold1)', marginBottom: 12 }}>
            {repr === 'rResid' && '🎯'}
            {reprObj.label}
          </div>
          <div style={{ fontSize: 17, color: 'var(--text-dim)', lineHeight: 1.55, marginBottom: 16 }}>
            {reprObj.desc}
          </div>
          <div className="divider" style={{ margin: '16px 0' }} />
          <div className="mono" style={{ fontSize: 13, color: 'var(--text-dim)', letterSpacing: '0.14em', textTransform: 'uppercase', marginBottom: 10 }}>Top 5 absolu</div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 7 }}>
            {vars.slice().sort((a, b) => Math.abs(b[repr]) - Math.abs(a[repr])).slice(0, 5).map(v => (
              <div key={v.var} className="hstack" style={{ justifyContent: 'space-between', fontSize: 15 }}>
                <span className="mono" style={{ color: 'var(--text)' }}>{v.var}</span>
                <span className="mono tabular" style={{ color: v[repr] > 0 ? 'var(--hot1)' : 'var(--cold1)' }}>{v[repr] > 0 ? '+' : ''}{v[repr].toFixed(3)}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Sankey */}
      <div className="glass" data-presenter="link-sankey" style={{ padding: 28, position: 'relative', zIndex: 2 }}>
        <div className="hstack" style={{ justifyContent: 'space-between', marginBottom: 14 }}>
          <div>
            <div className="mono" style={{ fontSize: 13, color: 'var(--text-dim)', letterSpacing: '0.14em', textTransform: 'uppercase' }}>Causalité de Granger · global · lag 6 mois</div>
            <div style={{ fontSize: 16, color: 'var(--text-dim)' }}>Chaque variable est classée dans <strong>une</strong> des 4 catégories selon le test bidirectionnel.</div>
          </div>
        </div>
        <Sankey grangerGroups={grangerGroups} groupColors={groupColors} />
      </div>
    </section>
  );
}

// ----- Heatmap -----
function Heatmap({ vars, repr, reprs, setRepr }) {
  const cellW = 78;
  const cellH = 34;
  const labelW = 70;   // just the variable name
  const sensW = 96;    // dedicated column for the sens pill
  const reprKeys = reprs.map(r => r.key);

  // Cell color: dense blue→neutral→red divergent (more contrasted than previous)
  const cellColor = (val) => {
    const t = Math.max(-1, Math.min(1, val / 0.7));      // normalize
    const a = Math.min(1, Math.abs(t) * 0.92 + 0.10);    // opacity follows |val|
    if (t >= 0) {
      // 0 → +1 : (33, 56, 88) deep neutral → (255, 107, 53) hot orange
      const r = Math.round(33 + t * (255 - 33));
      const g = Math.round(56 + t * (107 - 56));
      const b = Math.round(88 + t * (53 - 88));
      return { bg: `rgba(${r},${g},${b},${a})`, lum: 0.299*r + 0.587*g + 0.114*b };
    } else {
      const k = -t;
      // 0 → -1 : neutral → (0, 119, 182) cold blue
      const r = Math.round(33 + k * (0 - 33));
      const g = Math.round(56 + k * (119 - 56));
      const b = Math.round(88 + k * (182 - 88));
      return { bg: `rgba(${r},${g},${b},${a})`, lum: 0.299*r + 0.587*g + 0.114*b };
    }
  };

  return (
    <div style={{ position: 'relative', overflow: 'visible' }}>
      {/* Header row */}
      <div className="hstack" style={{ gap: 3, marginLeft: labelW + sensW, marginBottom: 8 }}>
        {reprs.map(r => (
          <button key={r.key}
            onClick={() => setRepr(r.key)}
            className={`btn-glass ${repr === r.key ? 'active' : ''}`}
            style={{ width: cellW, padding: '8px 4px', fontSize: 12 }}>
            {r.label.split(' ')[0]}
          </button>
        ))}
      </div>

      {/* Rows sorted by current repr's |r| */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
        {vars.slice().sort((a, b) => Math.abs(b[repr]) - Math.abs(a[repr])).map(v => (
          <div key={v.var} className="hstack" style={{ gap: 3, height: cellH }}>
            {/* Variable name */}
            <div style={{
              width: labelW, paddingRight: 6,
              display: 'flex', alignItems: 'center',
              fontFamily: 'JetBrains Mono, monospace',
              fontSize: 13,
              color: 'var(--text)',
              fontWeight: 500,
            }}>
              {v.var}
            </div>
            {/* Sens pill in its own column */}
            <div style={{
              width: sensW, paddingRight: 6,
              display: 'flex', alignItems: 'center', justifyContent: 'flex-start',
            }}>
              <SensPill sens={v.sens} />
            </div>
            {/* Cells */}
            {reprKeys.map(rk => {
              const val = v[rk];
              const abs = Math.abs(val);
              const { bg, lum } = cellColor(val);
              const isActive = rk === repr;
              const textColor = lum > 140 ? '#0A0E1A' : '#FFFFFF';
              return (
                <div key={rk}
                  title={`${v.var} · ${rk} · r = ${val.toFixed(3)}`}
                  onClick={() => setRepr(rk)}
                  style={{
                    width: cellW, height: cellH,
                    background: bg,
                    borderRadius: 5,
                    cursor: 'pointer',
                    transition: 'all 360ms var(--ease-expo)',
                    outline: isActive ? '2px solid rgba(255,255,255,0.85)' : '1px solid rgba(255,255,255,0.04)',
                    outlineOffset: isActive ? -2 : 0,
                    transform: isActive ? 'scale(1.04)' : 'scale(1)',
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                    fontFamily: 'JetBrains Mono, monospace',
                    fontSize: 13,
                    fontWeight: abs > 0.3 ? 600 : 400,
                    color: textColor,
                    fontVariantNumeric: 'tabular-nums',
                    textShadow: lum < 100 ? '0 1px 2px rgba(0,0,0,0.3)' : 'none',
                  }}>
                  {val >= 0 ? '+' : ''}{val.toFixed(2)}
                </div>
              );
            })}
          </div>
        ))}
      </div>

      {/* Legend */}
      <div className="hstack" style={{ gap: 12, marginTop: 14, alignItems: 'center', flexWrap: 'wrap', fontSize: 12, color: 'var(--text-dim)' }}>
        <span className="mono" style={{ letterSpacing: '0.1em' }}>r =</span>
        <div className="hstack" style={{ gap: 0, alignItems: 'center' }}>
          {[-0.7, -0.5, -0.3, -0.1, 0.1, 0.3, 0.5, 0.7].map(t => {
            const { bg } = cellColor(t);
            return (
              <div key={t} style={{
                width: 28, height: 14, background: bg,
                borderTop: '1px solid rgba(255,255,255,0.05)',
                borderBottom: '1px solid rgba(255,255,255,0.05)',
              }} />
            );
          })}
        </div>
        <span className="mono tabular">−0.7</span>
        <span style={{ marginLeft: 'auto' }} className="mono tabular">+0.7</span>
        <span style={{ marginLeft: 12 }}>· Bleu = négatif · Orange = positif · Intensité = |r|</span>
      </div>
    </div>
  );
}

// ----- Sankey -----
function Sankey({ grangerGroups, groupColors }) {
  const W = 1100, H = 580;
  const leftX = 60, rightX = W - 200;
  const vars = window.ALL_VARS_FULL;
  const N = vars.length;
  const rowH = (H - 40) / N;
  // assign y per var on left
  const leftY = {};
  vars.forEach((v, i) => { leftY[v.var] = 20 + i * rowH + rowH / 2; });

  // Right groups — explicit fixed dimensions so labels never overlap.
  const HEADER_H = 26;   // space for category title + count number
  const ITEM_H = 16;     // per variable label height
  const BOX_PAD = 6;     // bottom padding inside box
  const GROUP_GAP = 14;  // vertical gap between two group boxes

  const groupOrder = ['X -> CO2', 'CO2 -> X', 'bidirectionnel', 'aucun'];
  const groupTop = {};
  const groupBottom = {};
  let totalY = 20;
  groupOrder.forEach(g => {
    const items = grangerGroups[g];
    const h = HEADER_H + items.length * ITEM_H + BOX_PAD;
    groupTop[g] = totalY;
    groupBottom[g] = totalY + h;
    totalY += h + GROUP_GAP;
  });
  const totalUsed = totalY - GROUP_GAP;
  const offY = Math.max(0, (H - totalUsed) / 2 - 10);
  groupOrder.forEach(k => { groupTop[k] += offY; groupBottom[k] += offY; });

  // per-var y on right within group : centered on each item row
  const rightY = {};
  groupOrder.forEach(g => {
    const items = grangerGroups[g];
    items.forEach((v, i) => {
      rightY[v.var] = groupTop[g] + HEADER_H + i * ITEM_H + ITEM_H / 2;
    });
  });

  // path: cubic bezier from (leftX, leftY) → (rightX, rightY)
  const link = (x1, y1, x2, y2) => {
    const cx1 = x1 + (x2 - x1) * 0.5;
    const cx2 = x2 - (x2 - x1) * 0.5;
    return `M${x1},${y1} C${cx1},${y1} ${cx2},${y2} ${x2},${y2}`;
  };

  const [hoverVar, setHoverVar] = useState(null);

  return (
    <svg viewBox={`0 0 ${W} ${H}`} style={{ width: '100%', height: 'auto', display: 'block' }}>
      <defs>
        {Object.entries(groupColors).map(([g, c]) => (
          <linearGradient key={g} id={`sg-${g.replace(/[^a-z]/gi, '')}`} x1="0" y1="0" x2="1" y2="0">
            <stop offset="0%" stopColor="#ffffff" stopOpacity="0.08" />
            <stop offset="100%" stopColor={c} stopOpacity="0.45" />
          </linearGradient>
        ))}
      </defs>

      {/* Links */}
      {vars.map(v => {
        const c = groupColors[v.sens];
        const gradId = `sg-${v.sens.replace(/[^a-z]/gi, '')}`;
        const isHover = hoverVar === v.var;
        return (
          <g key={v.var}>
            <path
              d={link(leftX + 6, leftY[v.var], rightX - 6, rightY[v.var])}
              stroke={isHover ? c : `url(#${gradId})`}
              strokeWidth={isHover ? 4 : 2}
              fill="none"
              strokeOpacity={isHover ? 1 : (hoverVar ? 0.15 : 0.55)}
              style={{ transition: 'all 280ms var(--ease-expo)' }}
            />
          </g>
        );
      })}

      {/* Left labels */}
      {vars.map(v => (
        <g key={v.var}
          onMouseEnter={() => setHoverVar(v.var)}
          onMouseLeave={() => setHoverVar(null)}
          style={{ cursor: 'pointer' }}>
          <rect x={leftX - 56} y={leftY[v.var] - 9} width={62} height={18} rx={3}
            fill="rgba(255,255,255,0.03)" stroke="rgba(255,255,255,0.08)" />
          <text x={leftX - 25} y={leftY[v.var] + 4} textAnchor="middle"
            fontSize="11" fontFamily="JetBrains Mono" fill={hoverVar === v.var ? groupColors[v.sens] : '#F5F5F7'}
            style={{ transition: 'fill 200ms' }}>
            {v.var}
          </text>
          <circle cx={leftX + 6} cy={leftY[v.var]} r="2.5" fill={groupColors[v.sens]} />
        </g>
      ))}

      {/* Right groups */}
      {groupOrder.map(g => {
        const c = groupColors[g];
        const items = grangerGroups[g];
        const boxTop = groupTop[g];
        const boxBottom = groupBottom[g];
        return (
          <g key={g}>
            {/* Box */}
            <rect x={rightX} y={boxTop}
              width={170} height={boxBottom - boxTop} rx={6}
              fill={c} fillOpacity="0.08" stroke={c} strokeOpacity="0.3" />
            {/* Header separator under the title */}
            <line x1={rightX + 8} x2={rightX + 162}
              y1={boxTop + HEADER_H - 4} y2={boxTop + HEADER_H - 4}
              stroke={c} strokeOpacity="0.25" />
            {/* Category title */}
            <text x={rightX + 14} y={boxTop + 16}
              fontSize="11" fontFamily="JetBrains Mono" fill={c}
              fontWeight="600" style={{ textTransform: 'uppercase' }}>
              {g.replace('->', '→')}
            </text>
            {/* Count on the right */}
            <text x={rightX + 156} y={boxTop + 19}
              textAnchor="end" fontSize="18" fontFamily="Space Grotesk" fill={c}
              fontWeight="600">
              {items.length}
            </text>
            {/* Variable list — guaranteed inside the box thanks to fixed ITEM_H */}
            {items.map((v, i) => (
              <text key={v.var}
                x={rightX + 14}
                y={boxTop + HEADER_H + i * ITEM_H + ITEM_H - 4}
                fontSize="11" fontFamily="JetBrains Mono"
                fill={hoverVar === v.var ? c : 'rgba(245,245,247,0.7)'}
                onMouseEnter={() => setHoverVar(v.var)}
                onMouseLeave={() => setHoverVar(null)}
                style={{ cursor: 'pointer', transition: 'fill 200ms' }}>
                {v.var}
              </text>
            ))}
          </g>
        );
      })}
    </svg>
  );
}

window.ClimateCO2Link = ClimateCO2Link;
