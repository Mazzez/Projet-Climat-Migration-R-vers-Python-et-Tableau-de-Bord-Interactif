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

Object.assign(window, {
  useInView, CountUp, Sparkline, KPIChip, MetricCard, SectionHeader, SensPill,
  easeOutExpo, easeOutCubic, divergentColor,
});
