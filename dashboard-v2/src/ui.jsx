// UI primitives: CountUp, Sparkline, GlassCard, KPIChip, useInView

const { useState, useEffect, useRef, useMemo, useCallback, useContext } = React;

// Easing
const easeOutExpo = (t) => (t === 1 ? 1 : 1 - Math.pow(2, -10 * t));
const easeOutCubic = (t) => 1 - Math.pow(1 - t, 3);

// Intersection hook
function useInView(opts = {}) {
  const ref = useRef(null);
  const [inView, setInView] = useState(false);
  const [seen, setSeen] = useState(false);
  useEffect(() => {
    if (!ref.current) return;
    const io = new IntersectionObserver(([entry]) => {
      setInView(entry.isIntersecting);
      if (entry.isIntersecting) setSeen(true);
    }, { threshold: opts.threshold ?? 0.2, rootMargin: opts.rootMargin ?? '0px' });
    io.observe(ref.current);
    return () => io.disconnect();
  }, []);
  return [ref, inView, seen];
}

// CountUp: animates from 0 to value once visible
function CountUp({ value, decimals = 0, duration = 1800, prefix = '', suffix = '', className = '' }) {
  const [ref, , seen] = useInView({ threshold: 0.4 });
  const [n, setN] = useState(0);
  useEffect(() => {
    if (!seen) return;
    let raf;
    const start = performance.now();
    const tick = (t) => {
      const p = Math.min(1, (t - start) / duration);
      setN(value * easeOutExpo(p));
      if (p < 1) raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, [seen, value, duration]);
  return (
    <span ref={ref} className={`mono tabular ${className}`}>
      {prefix}{n.toFixed(decimals)}{suffix}
    </span>
  );
}

// Sparkline SVG
function Sparkline({ data, width = 120, height = 32, stroke = '#00D9FF', fill = true, strokeWidth = 1.5 }) {
  const path = useMemo(() => {
    if (!data || data.length < 2) return '';
    const min = Math.min(...data);
    const max = Math.max(...data);
    const range = max - min || 1;
    return data.map((v, i) => {
      const x = (i / (data.length - 1)) * width;
      const y = height - ((v - min) / range) * (height - 4) - 2;
      return `${i === 0 ? 'M' : 'L'}${x.toFixed(1)},${y.toFixed(1)}`;
    }).join(' ');
  }, [data, width, height]);
  const fillPath = path + ` L${width},${height} L0,${height} Z`;
  const id = useMemo(() => 'sg' + Math.random().toString(36).slice(2, 8), []);
  return (
    <svg width={width} height={height} style={{ display: 'block' }}>
      <defs>
        <linearGradient id={id} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor={stroke} stopOpacity="0.35" />
          <stop offset="100%" stopColor={stroke} stopOpacity="0" />
        </linearGradient>
      </defs>
      {fill && <path d={fillPath} fill={`url(#${id})`} />}
      <path d={path} stroke={stroke} strokeWidth={strokeWidth} fill="none" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

// KPI Chip — for hero tickers
function KPIChip({ value, unit, label, accent = '#FFB627', delay = 0 }) {
  return (
    <div className="glass" style={{
      padding: '14px 20px',
      minWidth: 180,
      animation: `slideUp 800ms var(--ease-expo) ${delay}ms both`,
    }}>
      <div className="hstack" style={{ gap: 10, alignItems: 'baseline' }}>
        <span className="display tabular" style={{ fontSize: 30, color: accent, letterSpacing: '-0.03em' }}>{value}</span>
        <span className="mono" style={{ fontSize: 14, color: 'var(--text-dim)' }}>{unit}</span>
      </div>
      <div className="mono" style={{ fontSize: 13, color: 'var(--text-dim)', textTransform: 'uppercase', letterSpacing: '0.12em', marginTop: 4 }}>
        {label}
      </div>
    </div>
  );
}

// Metric card with optional sparkline
function MetricCard({ label, value, unit, sub, spark, accent = '#FFB627', children }) {
  return (
    <div className="glass" style={{ padding: 22, display: 'flex', flexDirection: 'column', gap: 8 }}>
      <div className="mono" style={{ fontSize: 13, color: 'var(--text-dim)', textTransform: 'uppercase', letterSpacing: '0.14em' }}>{label}</div>
      <div className="hstack" style={{ gap: 10, alignItems: 'baseline' }}>
        <span className="display tabular" style={{ fontSize: 40, color: accent, letterSpacing: '-0.03em', lineHeight: 1 }}>{value}</span>
        {unit && <span className="mono" style={{ fontSize: 15, color: 'var(--text-dim)' }}>{unit}</span>}
      </div>
      {sub && <div style={{ fontSize: 15, color: 'var(--text-dim)' }}>{sub}</div>}
      {spark && <div style={{ marginTop: 6 }}><Sparkline data={spark} stroke={accent} width={220} height={36} /></div>}
      {children}
    </div>
  );
}

// Section header
function SectionHeader({ act, title, kicker, accent = '#FF6B35' }) {
  return (
    <div style={{ position: 'relative', zIndex: 2, marginBottom: 48 }}>
      <div className="eyebrow">
        <span>Act {act} / 06</span>
        <span style={{ color: accent }}>—</span>
        <span style={{ color: 'var(--text-dim)' }}>{kicker}</span>
      </div>
      <h2 style={{ maxWidth: 980 }} dangerouslySetInnerHTML={{ __html: title }} />
    </div>
  );
}

// Pill for Granger sens
function SensPill({ sens }) {
  const map = {
    'X -> CO2': { cls: 'pill-x', label: 'X \u2192 CO2' },
    'CO2 -> X': { cls: 'pill-c', label: 'CO2 \u2192 X' },
    'bidirectionnel': { cls: 'pill-bi', label: 'bidir.' },
    'aucun': { cls: 'pill-none', label: 'aucun' },
  };
  const m = map[sens] || map['aucun'];
  return <span className={`pill mono ${m.cls}`}>{m.label}</span>;
}

// Hex colormap RdBu_r divergent
function divergentColor(value, vmax = 0.1) {
  const t = Math.max(-1, Math.min(1, value / vmax));
  if (t >= 0) {
    // 0..1 cyan->white->hot1
    const r = Math.round(255 * Math.min(1, 0.05 + t));
    const g = Math.round(255 * Math.max(0, 0.95 - t * 0.6));
    const b = Math.round(255 * Math.max(0, 0.95 - t * 0.95));
    return `rgb(${r},${g},${b})`;
  } else {
    const k = -t;
    const r = Math.round(255 * Math.max(0, 0.85 - k * 0.85));
    const g = Math.round(255 * Math.max(0, 0.95 - k * 0.5));
    const b = Math.round(255 * Math.min(1, 0.85 + k * 0.15));
    return `rgb(${r},${g},${b})`;
  }
}

// Glossary — definitions for technical terms (jury non-spécialiste)
const GLOSSARY = {
  'Sen': {
    title: 'Pente de Sen',
    text: 'Estimateur non-paramétrique robuste de la pente d\'une série temporelle, basé sur la médiane de toutes les pentes entre paires de points. Insensible aux valeurs aberrantes — contrairement aux moindres carrés.',
  },
  'Granger': {
    title: 'Causalité de Granger',
    text: 'Test statistique : on dit que X "cause au sens de Granger" Y si les valeurs passées de X améliorent significativement la prédiction de Y au-delà de ses propres valeurs passées. Ce n\'est pas une preuve de mécanisme physique, mais d\'antériorité prédictive.',
  },
  'IC95': {
    title: 'Intervalle de Confiance 95%',
    text: 'Fourchette dans laquelle se situe la vraie valeur avec 95% de probabilité. Ici calculé par bootstrap (10 000 rééchantillonnages aléatoires de la série).',
  },
  'R²': {
    title: 'Coefficient de détermination',
    text: 'Fraction de la variance de la variable cible (CO₂ résiduel) expliquée par les variables prédictrices. 0 = aucun pouvoir explicatif, 1 = explication parfaite.',
  },
  'STL': {
    title: 'Seasonal-Trend Loess',
    text: 'Décomposition d\'une série temporelle en trois composantes : tendance lente, cycle saisonnier répétitif, résidus. Permet d\'isoler le signal interannuel.',
  },
  'Anomalie': {
    title: 'Anomalie',
    text: 'Déviation à la climatologie mensuelle (moyenne 1991-2020). Retire le cycle saisonnier pour révéler les variations interannuelles.',
  },
  'résidus': {
    title: 'Résidus détendrés',
    text: 'Ce qui reste d\'une série après avoir retiré la tendance linéaire ET le cycle saisonnier. C\'est le signal interannuel propre — le seul niveau auquel on peut tester un couplage causal sans confondre avec la dérive commune.',
  },
  'CRE': {
    title: 'Cloud Radiative Effect',
    text: 'Effet radiatif des nuages = différence entre rayonnement net "all-sky" et "clear-sky". CRE_LW (absorption infrarouge), CRE_SW (réflexion solaire), CRE_net = somme.',
  },
  'CSDLF': {
    title: 'Clear-Sky Downward Longwave Flux',
    text: 'Rayonnement infrarouge descendant en l\'absence de nuages. Signature directe de l\'effet de serre par les GES (CO₂, H₂O, CH₄…). Sa montée +7.84 W/m² sur 47 ans est LA preuve physique du forçage.',
  },
};

function GlossaryTerm({ term, children }) {
  const def = GLOSSARY[term];
  const [open, setOpen] = useState(false);
  if (!def) return <>{children}</>;
  return (
    <span
      style={{
        borderBottom: '1px dotted rgba(0,217,255,0.5)',
        cursor: 'help',
        position: 'relative',
        display: 'inline-block',
      }}
      onMouseEnter={() => setOpen(true)}
      onMouseLeave={() => setOpen(false)}
      onClick={(e) => { e.stopPropagation(); setOpen((o) => !o); }}
    >
      {children}
      {open && (
        <span style={{
          position: 'absolute', bottom: 'calc(100% + 8px)', left: '50%',
          transform: 'translateX(-50%)',
          background: 'rgba(15,20,32,0.97)',
          border: '1px solid rgba(0,217,255,0.4)',
          borderRadius: 10,
          padding: '14px 16px',
          width: 320,
          fontSize: 13,
          color: 'var(--text)',
          lineHeight: 1.55,
          zIndex: 999,
          fontFamily: 'Inter, sans-serif',
          fontWeight: 400,
          fontStyle: 'normal',
          textTransform: 'none',
          letterSpacing: 0,
          textAlign: 'left',
          boxShadow: '0 10px 36px rgba(0,0,0,0.5)',
          pointerEvents: 'none',
        }}>
          <span className="mono" style={{
            display: 'block',
            fontSize: 10,
            color: 'var(--cold1)',
            letterSpacing: '0.16em',
            marginBottom: 8,
            textTransform: 'uppercase',
            fontWeight: 600,
          }}>{def.title}</span>
          <span style={{ display: 'block', color: 'var(--text-dim)' }}>{def.text}</span>
        </span>
      )}
    </span>
  );
}

// ExportButton — capture a DOM node to PNG via html2canvas (lazy-loaded CDN)
function ExportButton({ targetSelector, filename, label = 'Capturer', style = {} }) {
  const [busy, setBusy] = useState(false);
  const ensureLib = () => new Promise((resolve, reject) => {
    if (window.html2canvas) return resolve(window.html2canvas);
    const s = document.createElement('script');
    s.src = 'https://cdn.jsdelivr.net/npm/html2canvas@1.4.1/dist/html2canvas.min.js';
    s.onload = () => resolve(window.html2canvas);
    s.onerror = () => reject(new Error('html2canvas load failed'));
    document.head.appendChild(s);
  });
  const onClick = async () => {
    if (busy) return;
    setBusy(true);
    try {
      const node = document.querySelector(targetSelector);
      if (!node) throw new Error('cible introuvable');
      const h2c = await ensureLib();
      const canvas = await h2c(node, {
        backgroundColor: '#0A0E1A',
        scale: 2,
        useCORS: true,
        logging: false,
        ignoreElements: (el) => el.classList && (el.classList.contains('export-ignore') || el.classList.contains('grain')),
      });
      const url = canvas.toDataURL('image/png');
      const a = document.createElement('a');
      a.href = url;
      a.download = (filename || 'capture') + '.png';
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
    } catch (err) {
      console.warn('[ExportButton]', err);
      alert('Capture impossible : ' + err.message);
    } finally {
      setBusy(false);
    }
  };
  return (
    <button onClick={onClick} className="btn-glass export-ignore" disabled={busy}
      style={{
        display: 'inline-flex', alignItems: 'center', gap: 6,
        fontSize: 12, padding: '6px 12px',
        opacity: busy ? 0.6 : 1, cursor: busy ? 'wait' : 'pointer',
        ...style,
      }}>
      <svg width="14" height="14" viewBox="0 0 16 16" fill="none">
        <path d="M8 1.5V10M8 10L4.5 6.5M8 10L11.5 6.5M2 11V13.5C2 14.05 2.45 14.5 3 14.5H13C13.55 14.5 14 14.05 14 13.5V11"
              stroke="currentColor" strokeWidth="1.3" strokeLinecap="round" strokeLinejoin="round" />
      </svg>
      {busy ? 'Capture…' : label}
    </button>
  );
}

Object.assign(window, {
  useInView, CountUp, Sparkline, KPIChip, MetricCard, SectionHeader, SensPill,
  easeOutExpo, easeOutCubic, divergentColor,
  GLOSSARY, GlossaryTerm, ExportButton,
});
