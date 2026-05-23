// App — orchestrator + nav + scroll progress + tweaks

const TweaksContext = React.createContext(null);

const TWEAK_DEFAULTS = /*EDITMODE-BEGIN*/{
  "trendStrength": 1.0,
  "detail": "medium",
  "heroGlobeSize": 110,
  "heroGlobeOffsetX": -5,
  "bigGlobeDistance": 3.35,
  "bigGlobeSegments": "high",
  "showGridLines": true,
  "atmosphere": true
}/*EDITMODE-END*/;

const DETAIL_MAP = { low: 48, medium: 96, high: 144 };
const BIG_SEG_MAP = { low: 64, medium: 96, high: 128, ultra: 192 };

function App() {
  const [progress, setProgress] = useState(0);
  const [active, setActive] = useState(1);
  const [aboutOpen, setAboutOpen] = useState(false);
  const [presenterOpen, setPresenterOpen] = useState(false);
  const [t, setTweak] = useTweaks(TWEAK_DEFAULTS);

  useEffect(() => {
    const onScroll = () => {
      const doc = document.documentElement;
      const total = doc.scrollHeight - doc.clientHeight;
      const p = total > 0 ? doc.scrollTop / total : 0;
      setProgress(p);
      const secs = [1, 2, 3, 4, 5, 6];
      for (const i of secs) {
        const el = document.getElementById(`sec-${i}`);
        if (!el) continue;
        const r = el.getBoundingClientRect();
        if (r.top < window.innerHeight * 0.5 && r.bottom > window.innerHeight * 0.5) {
          setActive(i); break;
        }
      }
    };
    onScroll();
    window.addEventListener('scroll', onScroll, { passive: true });
    return () => window.removeEventListener('scroll', onScroll);
  }, []);

  const goto = (n) => {
    const el = document.getElementById(`sec-${n}`);
    if (el) el.scrollIntoView({ behavior: 'smooth' });
  };

  const labels = {
    1: 'Hero', 2: 'Trajectoire', 3: 'Terre 3D', 4: 'Lien', 5: 'Hotspots', 6: 'Critique',
  };

  // Resolved tweak values exposed via context
  const tweakValues = {
    trendStrength: t.trendStrength,
    detail: DETAIL_MAP[t.detail] ?? 96,
    bigSegments: BIG_SEG_MAP[t.bigGlobeSegments] ?? 128,
    heroSize: t.heroGlobeSize,
    heroOffsetX: t.heroGlobeOffsetX,
    bigDistance: t.bigGlobeDistance,
    showGridLines: t.showGridLines,
    atmosphere: t.atmosphere,
  };

  return (
    <TweaksContext.Provider value={tweakValues}>
      <div className="grain" />
      <div className="progress-bar" style={{ width: `${progress * 100}%` }} />

      <div className="top-brand">
        <div className="top-brand-mark" />
        <span>Climate · CO₂ · 1979–2025</span>
      </div>

      <div className="nav-dots">
        {[1,2,3,4,5,6].map(n => (
          <a key={n} className={`nav-dot ${active === n ? 'active' : ''}`} data-label={labels[n]}
            onClick={(e) => { e.preventDefault(); goto(n); }} href={`#sec-${n}`} />
        ))}
      </div>

      <button className="btn-glass about-fab" onClick={() => setAboutOpen(true)}>
        <span className="mono" style={{ fontSize: 12, letterSpacing: '0.08em' }}>ℹ À propos</span>
      </button>
      <AboutModal open={aboutOpen} onClose={() => setAboutOpen(false)} />

      <PresenterButton onClick={() => setPresenterOpen(true)} />
      <PresenterMode open={presenterOpen} onClose={() => setPresenterOpen(false)} />

      {!presenterOpen && (
        <div style={{ position: 'fixed', bottom: 24, left: 380, zIndex: 80 }}>
          <ExportButton
            targetSelector={`#sec-${active}`}
            filename={`section-${active}-${(labels[active]||'').toLowerCase().replace(/\s+/g,'-')}`}
            label={`Capturer · ${labels[active] || ''}`}
            style={{ borderColor: 'rgba(82,255,184,0.35)', color: 'var(--green)' }}
          />
        </div>
      )}

      <TweaksPanel>
        <TweakSection label="Globe · Hero" />
        <TweakSlider label="Taille" value={t.heroGlobeSize} min={50} max={130} step={5} unit="vh"
                     onChange={(v) => setTweak('heroGlobeSize', v)} />
        <TweakSlider label="Position X" value={t.heroGlobeOffsetX} min={-40} max={40} step={2} unit="vw"
                     onChange={(v) => setTweak('heroGlobeOffsetX', v)} />

        <TweakSection label="Globe · Section 3 (carte du climat)" />
        <TweakSlider label="Distance caméra" value={t.bigGlobeDistance} min={1.6} max={3.4} step={0.05}
                     onChange={(v) => setTweak('bigGlobeDistance', v)} />
        <TweakRadio  label="Détail" value={t.bigGlobeSegments}
                     options={['low','medium','high','ultra']}
                     onChange={(v) => setTweak('bigGlobeSegments', v)} />

        <TweakSection label="Globe · Tous" />
        <TweakSlider label="Intensité tendance" value={t.trendStrength} min={0.0} max={1.6} step={0.05}
                     onChange={(v) => setTweak('trendStrength', v)} />
        <TweakRadio  label="Détail hero & mini" value={t.detail}
                     options={['low','medium','high']}
                     onChange={(v) => setTweak('detail', v)} />
        <TweakToggle label="Grille lat/lon" value={t.showGridLines}
                     onChange={(v) => setTweak('showGridLines', v)} />
        <TweakToggle label="Halo atmosphère" value={t.atmosphere}
                     onChange={(v) => setTweak('atmosphere', v)} />
      </TweaksPanel>

      <main>
        <Hero />
        <Trajectory />
        <Earth3D />
        <ClimateCO2Link />
        <Hotspots />
        <Critical />
      </main>
    </TweaksContext.Provider>
  );
}

window.App = App;
window.TweaksContext = TweaksContext;
