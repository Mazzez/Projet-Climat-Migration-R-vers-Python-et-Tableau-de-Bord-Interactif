// Mode Présentation v3 — chaque étape cible un ÉLÉMENT précis (data-presenter)
// au lieu de scroller des sections entières. L'élément est centré dans le viewport
// et reçoit un halo de focus. Plus aucun contenu n'est caché.

const PRESENTER_STEPS = [
  { target:'#sec-1',
    dur:12,
    title:'L\'atmosphère qui s\'épaissit',
    caption:'+91 ppm en 47 ans. Quatre chiffres clés : pente Sen 1.881 ppm/an, ΔT2m +0.78K, amplification arctique 4×, vitesse 100-200× vs paléo.' },

  { target:'[data-presenter="trajectory-chart"]',
    dur:14,
    title:'Trajectoire CO₂ · 1979 → 2025',
    caption:'564 mesures NOAA mensuelles. Trois modèles linéaire / quadratique / cubique. Bouton "Voir 2050" : scénarios IPCC SSP1-2.6 vs SSP5-8.5.' },

  { target:'[data-presenter="trajectory-vostok"]',
    dur:12,
    title:'Vostok 414 ka · vitesse 100-200× plus rapide',
    caption:'La pente actuelle (+1.88 ppm/an) face aux transitions glaciaires-interglaciaires (~0.01 ppm/an). La plage naturelle paléo n\'a jamais dépassé 300 ppm.' },

  { target:'[data-presenter="trajectory-events"]',
    dur:12,
    title:'Événements marquants · impact mesuré',
    caption:'Pinatubo 91 (-0.6 ppm/an), El Niño 97-98 (+2.9 ppm/an), COVID (-0.3 ppm), Hunga Tonga. Chaque marqueur affiche la perturbation chiffrée + source.' },

  { target:'[data-presenter="earth-globe"]',
    dur:18,
    title:'La carte du climat · 18 variables × 47 ans',
    caption:'Grille 0.5° × 0.5°. Tendance Sen ou corrélation CO₂ par pixel. Slider Avant 1980-2000 / Après 2005-2025 montre l\'accélération récente.' },

  { target:'[data-presenter="link-kpis"]',
    dur:11,
    title:'Granger 15/21 · R²=0.748',
    caption:'15 variables sur 21 précèdent le CO₂ statistiquement. 12 résiduelles expliquent 75% du CO₂. CSDLF +7.84 W/m² : preuve physique du forçage radiatif.' },

  { target:'[data-presenter="link-heatmap"]',
    dur:13,
    title:'Heatmap 21 × 5 représentations',
    caption:'Cinq lectures de la même série : niveaux / anomalies / résidus détendrés / Δ1 mois / Δ12 mois. Le panneau pédagogique adapte l\'explication.' },

  { target:'[data-presenter="link-sankey"]',
    dur:10,
    title:'Sankey de causalité Granger',
    caption:'Assignation par variable : X→CO₂ (15), CO₂→X (3), bidirectionnel (5), aucun. Survol isole le flux.' },

  { target:'[data-presenter="hotspots-cards"]',
    dur:14,
    title:'4 hotspots · 5 latitudes',
    caption:'Sahel, Sibérie centrale, Amazonie, Indonésie. Mini-globes centrés sur la zone + Sen + p Mann-Kendall pour 4 variables × 4 régions.' },

  { target:'[data-presenter="hotspots-amp"]',
    dur:10,
    title:'Amplification arctique · R² par zone',
    caption:'NH s\'amplifie 4× plus que SH. R² zonaux : global=0.75, tropical=0.69, hotspots locaux < 10%.' },

  { target:'[data-presenter="critical-timeline"]',
    dur:14,
    title:'Limites · Saut CFSR/CFSv2 janvier 2011',
    caption:'5 variables ont subi un saut artificiel. R² passe de 0.75 → 0.46 après homogénéisation. Le couplage reste réel mais une partie de sa force venait de l\'artefact.' },
];

const PRESENTER_TOTAL_S = PRESENTER_STEPS.reduce((a, s) => a + s.dur, 0);

function PresenterMode({ open, onClose }) {
  const [step, setStep] = useState(0);
  const [paused, setPaused] = useState(false);
  const [progress, setProgress] = useState(0);

  // Auto-advance timer
  useEffect(() => {
    if (!open || paused) return;
    const ms = PRESENTER_STEPS[step].dur * 1000;
    const t0 = performance.now();
    let raf;
    const tick = (t) => {
      const p = Math.min(1, (t - t0) / ms);
      setProgress(p);
      if (p < 1) {
        raf = requestAnimationFrame(tick);
      } else if (step < PRESENTER_STEPS.length - 1) {
        setStep(step + 1);
        setProgress(0);
      } else {
        setPaused(true);
      }
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, [open, step, paused]);

  // Smooth scroll on step change. We scroll to the SPECIFIC anchor element
  // and center it in the viewport. If the element is taller than the viewport,
  // we align its top with the viewport top + 20px.
  useEffect(() => {
    if (!open) return;
    const s = PRESENTER_STEPS[step];
    const el = document.querySelector(s.target);
    if (!el) {
      console.warn('[Presenter] target not found:', s.target);
      return;
    }
    const rect = el.getBoundingClientRect();
    const elTop = window.scrollY + rect.top;
    const elH = rect.height;
    const winH = window.innerHeight;
    let targetY;
    if (elH > winH - 40) {
      // taller than viewport: align top with viewport top + small margin
      targetY = elTop - 20;
    } else {
      // smaller than viewport: center it
      targetY = elTop - (winH - elH) / 2;
    }
    targetY = Math.max(0, targetY);
    window.scrollTo({ top: targetY, behavior: 'smooth' });
  }, [open, step]);

  // Apply a focus halo on the target element
  useEffect(() => {
    if (!open) return;
    document.querySelectorAll('.presenter-focus').forEach(el => el.classList.remove('presenter-focus'));
    const s = PRESENTER_STEPS[step];
    const el = document.querySelector(s.target);
    if (el) el.classList.add('presenter-focus');
    return () => {
      document.querySelectorAll('.presenter-focus').forEach(el => el.classList.remove('presenter-focus'));
    };
  }, [open, step]);

  // Body class toggle
  useEffect(() => {
    if (open) document.body.classList.add('presenter-active');
    else document.body.classList.remove('presenter-active');
    return () => document.body.classList.remove('presenter-active');
  }, [open]);

  // Keyboard shortcuts
  useEffect(() => {
    if (!open) return;
    const onKey = (e) => {
      if (e.key === 'ArrowRight') { e.preventDefault(); next(); }
      else if (e.key === 'ArrowLeft')  { e.preventDefault(); prev(); }
      else if (e.key === ' ')          { e.preventDefault(); setPaused(p => !p); }
      else if (e.key === 'Escape')     { e.preventDefault(); onClose(); }
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [open, step]);

  const next = () => { setStep(s => Math.min(PRESENTER_STEPS.length - 1, s + 1)); setProgress(0); };
  const prev = () => { setStep(s => Math.max(0, s - 1)); setProgress(0); };
  const restart = () => { setStep(0); setProgress(0); setPaused(false); };

  if (!open) return null;
  const current = PRESENTER_STEPS[step];
  const isLast = step === PRESENTER_STEPS.length - 1;

  // Cumulative time elapsed
  let elapsed = progress * current.dur;
  for (let i = 0; i < step; i++) elapsed += PRESENTER_STEPS[i].dur;
  const totalProgress = elapsed / PRESENTER_TOTAL_S;

  return (
    <>
      {/* Thin top progress bar — non-intrusive */}
      <div className="export-ignore" style={{
        position: 'fixed', top: 0, left: 0, right: 0, height: 3, zIndex: 250,
        background: 'rgba(5,8,17,0.6)',
        pointerEvents: 'none',
      }}>
        <div style={{
          width: `${totalProgress * 100}%`, height: '100%',
          background: 'linear-gradient(to right, var(--cold1), var(--hot1))',
          transition: 'width 100ms linear',
        }} />
      </div>

      {/* Compact caption card — top-left corner (doesn't span the screen) */}
      <div className="export-ignore" style={{
        position: 'fixed', top: 16, left: 16, zIndex: 250,
        maxWidth: 460,
        padding: '12px 16px',
        background: 'rgba(15,20,32,0.92)',
        border: '1px solid rgba(255,107,53,0.25)',
        borderRadius: 12,
        backdropFilter: 'blur(20px)',
        WebkitBackdropFilter: 'blur(20px)',
        boxShadow: '0 8px 28px rgba(0,0,0,0.4)',
        animation: 'fadeIn 360ms var(--ease-expo)',
      }}>
        <div className="mono" style={{
          fontSize: 10, letterSpacing: '0.18em',
          color: 'var(--hot1)', textTransform: 'uppercase',
          marginBottom: 3,
        }}>
          ▶ Étape {step + 1} / {PRESENTER_STEPS.length}
        </div>
        <div className="display" style={{
          fontSize: 15, color: 'var(--text)', fontWeight: 600,
          letterSpacing: '-0.005em', marginBottom: 4, lineHeight: 1.2,
        }}>
          {current.title}
        </div>
        <div style={{ fontSize: 12, color: 'var(--text-dim)', lineHeight: 1.45 }}>
          {current.caption}
        </div>
      </div>

      {/* Compact control card — bottom-right corner (frees the centre & bottom of the screen) */}
      <div className="export-ignore" style={{
        position: 'fixed', bottom: 16, right: 16,
        zIndex: 250,
        display: 'flex', alignItems: 'center', gap: 8,
        padding: '8px 10px',
        background: 'rgba(15,20,32,0.92)',
        border: '1px solid rgba(255,255,255,0.12)',
        borderRadius: 999,
        backdropFilter: 'blur(20px)',
        WebkitBackdropFilter: 'blur(20px)',
        boxShadow: '0 8px 28px rgba(0,0,0,0.4)',
        animation: 'slideUp 360ms var(--ease-expo)',
      }}>
        {/* Step indicator pills */}
        <div className="hstack" style={{ gap: 4, padding: '0 6px' }}>
          {PRESENTER_STEPS.map((s, i) => (
            <button key={i} onClick={() => { setStep(i); setProgress(0); }}
              style={{
                width: i === step ? 22 : 8,
                height: 8,
                borderRadius: 4,
                background: i === step ? 'var(--hot1)' : i < step ? 'rgba(255,107,53,0.5)' : 'rgba(255,255,255,0.18)',
                border: 'none',
                cursor: 'pointer',
                transition: 'all 320ms var(--ease-expo)',
                padding: 0,
              }}
              title={`Étape ${i + 1} · ${s.title}`} />
          ))}
        </div>

        <div style={{ width: 1, height: 20, background: 'rgba(255,255,255,0.1)', margin: '0 4px' }} />

        {/* Prev */}
        <button onClick={prev} disabled={step === 0} className="btn-glass"
          style={{ padding: 8, opacity: step === 0 ? 0.4 : 1, borderRadius: 8 }} title="Précédent (←)">
          <svg width="14" height="14" viewBox="0 0 16 16" fill="none">
            <path d="M10 12L6 8L10 4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
        </button>

        {/* Play/Pause or Restart */}
        {isLast && paused ? (
          <button onClick={restart} className="btn-glass"
            style={{ padding: '8px 14px', borderRadius: 8, color: 'var(--hot1)' }} title="Recommencer">
            <svg width="14" height="14" viewBox="0 0 16 16" fill="none" style={{ verticalAlign: 'middle' }}>
              <path d="M2 8a6 6 0 1 0 1.5-3.97L2 6M2 2v4h4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
            <span style={{ marginLeft: 6, fontSize: 12, fontFamily: 'JetBrains Mono' }}>Recommencer</span>
          </button>
        ) : (
          <button onClick={() => setPaused(p => !p)} className="btn-glass"
            style={{ padding: 10, borderRadius: 999, color: 'var(--hot1)', borderColor: 'rgba(255,107,53,0.45)' }}
            title={paused ? 'Lecture (espace)' : 'Pause (espace)'}>
            {paused ? (
              <svg width="14" height="14" viewBox="0 0 16 16" fill="currentColor">
                <path d="M4 3l9 5-9 5V3z" />
              </svg>
            ) : (
              <svg width="14" height="14" viewBox="0 0 16 16" fill="currentColor">
                <rect x="3.5" y="3" width="3" height="10" rx="0.5" />
                <rect x="9.5" y="3" width="3" height="10" rx="0.5" />
              </svg>
            )}
          </button>
        )}

        {/* Next */}
        <button onClick={next} disabled={isLast} className="btn-glass"
          style={{ padding: 8, opacity: isLast ? 0.4 : 1, borderRadius: 8 }} title="Suivant (→)">
          <svg width="14" height="14" viewBox="0 0 16 16" fill="none">
            <path d="M6 4L10 8L6 12" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
        </button>

        <div style={{ width: 1, height: 20, background: 'rgba(255,255,255,0.1)', margin: '0 4px' }} />

        {/* Counter */}
        <div className="mono tabular" style={{
          fontSize: 12, color: 'var(--text-dim)',
          minWidth: 64, textAlign: 'center', letterSpacing: '0.06em',
        }}>
          {Math.floor(elapsed).toString().padStart(2, '0')}s / {PRESENTER_TOTAL_S}s
        </div>

        {/* Exit */}
        <button onClick={onClose} className="btn-glass"
          style={{ padding: '8px 12px', borderRadius: 8, fontSize: 11, color: 'var(--text-dim)' }}
          title="Quitter (Échap)">
          ✕ Quitter
        </button>
      </div>
    </>
  );
}

// Trigger button — sits next to "À propos" with breathing room
function PresenterButton({ onClick }) {
  return (
    <button onClick={onClick} className="btn-glass export-ignore"
      style={{
        position: 'fixed', bottom: 24, left: 190, zIndex: 80,
        borderColor: 'rgba(255,107,53,0.35)',
        color: 'var(--hot1)',
        display: 'inline-flex', alignItems: 'center', gap: 6,
      }}>
      <svg width="13" height="13" viewBox="0 0 16 16" fill="currentColor">
        <path d="M4 3l9 5-9 5V3z" />
      </svg>
      <span className="mono" style={{ fontSize: 12, letterSpacing: '0.08em' }}>Présentation</span>
    </button>
  );
}

window.PresenterMode = PresenterMode;
window.PresenterButton = PresenterButton;
window.PRESENTER_STEPS = PRESENTER_STEPS;
