// Section 1 — HERO: "L'atmosphère qui s'épaissit"

function Hero() {
  const [ref, , seen] = useInView({ threshold: 0.1 });
  const tw = useContext(window.TweaksContext) || {};
  const heroSize = tw.heroSize ?? 95;
  const heroOffsetX = tw.heroOffsetX ?? -14;
  const trendStrength = tw.trendStrength ?? 1.0;
  const segments = tw.detail ?? 96;

  return (
    <section ref={ref} className="section" id="sec-1" data-screen-label="01 Hero" style={{
      minHeight: '100vh', height: '100vh', padding: 0, position: 'relative', overflow: 'hidden',
    }}>
      {/* 3D globe — positioned to the right side */}
      <div style={{
        position: 'absolute',
        top: '50%', right: `${heroOffsetX}vw`,
        transform: 'translateY(-50%)',
        width: `min(${heroSize}vh, ${heroSize}vw)`, height: `min(${heroSize}vh, ${heroSize}vw)`,
        zIndex: 1,
      }}>
        <Globe
          autoRotate
          rotationSpeed={0.05}
          showTrend={0.95 * trendStrength}
          cameraDistance={3.0}
          segments={segments}
          paused={!seen}
          interactive={false}
          showGrid={tw.showGridLines !== false}
          showAtmosphere={tw.atmosphere !== false}
          showStars
          starCount={500}
        />
      </div>

      {/* Particle field overlay */}
      <div style={{ position: 'absolute', inset: 0, zIndex: 2 }}>
        <ParticleField count={240} />
      </div>

      {/* Gradient veil for legibility — narrowed so the globe atmosphere isn't masked */}
      <div style={{
        position: 'absolute', inset: 0, zIndex: 3,
        background: 'linear-gradient(90deg, rgba(10,14,26,0.85) 0%, rgba(10,14,26,0.55) 15%, rgba(10,14,26,0.15) 32%, rgba(10,14,26,0.0) 42%)',
        pointerEvents: 'none',
      }} />
      <div style={{
        position: 'absolute', inset: 0, zIndex: 3,
        background: 'linear-gradient(to top, rgba(10,14,26,0.75) 0%, rgba(10,14,26,0.0) 28%)',
        pointerEvents: 'none',
      }} />

      {/* Main content stack */}
      <div style={{
        position: 'relative', zIndex: 5, height: '100%',
        display: 'flex', flexDirection: 'column', justifyContent: 'space-between',
        padding: '78px 56px 32px',
      }}>
        {/* Top — meta */}
        <div className="hstack" style={{ justifyContent: 'space-between', alignItems: 'flex-start' }}>
          <div>
            <div className="mono" style={{ fontSize: 20, letterSpacing: '0.22em', color: 'var(--hot1)', textTransform: 'uppercase' }}>
              Climate Change Intelligence
            </div>
            <div className="mono" style={{ fontSize: 20, letterSpacing: '0.18em', color: 'var(--text-dim)', textTransform: 'uppercase', marginTop: 8 }}>
              47 ans · 21 variables · 11 844 points-mois
            </div>
          </div>
          <div className="mono" style={{ fontSize: 20, letterSpacing: '0.18em', color: 'var(--text-dim)', textTransform: 'uppercase', textAlign: 'right' }}>
            1979<br/>→ 2025
          </div>
        </div>

        {/* Middle — headline */}
        <div style={{ maxWidth: 920 }}>
          <h1 className="display" style={{
            fontSize: 'clamp(56px, 11vw, 168px)',
            lineHeight: 0.88,
            letterSpacing: '-0.035em',
            fontWeight: 600,
          }}>
            <span style={{
              background: 'linear-gradient(135deg, #FFB627 0%, #FF6B35 50%, #FFB627 100%)',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
              backgroundClip: 'text',
            }}>
              +<CountUp value={89} duration={2200} /> ppm
            </span>
          </h1>
          <h1 className="display" style={{
            fontSize: 'clamp(40px, 7.5vw, 116px)',
            lineHeight: 0.95,
            letterSpacing: '-0.035em',
            fontWeight: 500,
            color: 'var(--text)',
          }}>
            en 47 ans.
          </h1>
          <h1 className="display" style={{
            fontSize: 'clamp(28px, 5vw, 82px)',
            lineHeight: 1,
            letterSpacing: '-0.03em',
            fontWeight: 300,
            color: 'var(--text-dim)',
            fontStyle: 'italic',
            marginTop: 16,
          }}>
            Et après ?
          </h1>
          <p style={{
            maxWidth: 540, marginTop: 22,
            fontSize: 19, color: 'var(--text-dim)', lineHeight: 1.55,
          }}>
            Une étude longitudinale du couplage atmosphère ↔ CO₂ sur 47 ans, à partir
            de 18 variables climatiques NOAA et de la série Mauna Loa. Cinq
            représentations, dix zones, quatre hotspots.
          </p>
        </div>

        {/* Bottom — KPIs */}
        <div className="hstack" style={{ gap: 12, flexWrap: 'wrap', justifyContent: 'flex-start' }}>
          <KPIChip value="1.881" unit="ppm/an" label="Pente Sen" accent="var(--hot2)" delay={400} />
          <KPIChip value="+0.78" unit="K T2m" label="Réchauffement global" accent="var(--hot1)" delay={500} />
          <KPIChip value="4.0×" unit="" label="Amplification arctique" accent="var(--hot3)" delay={600} />
          <KPIChip value="30×" unit="" label="Vitesse vs paléo (Vostok)" accent="var(--green)" delay={700} />
        </div>
      </div>

      {/* Scroll CTA */}
      <div style={{
        position: 'absolute', bottom: 16, left: '50%', transform: 'translateX(-50%)',
        zIndex: 6, textAlign: 'center',
        animation: 'bob 2.4s ease-in-out infinite',
      }}>
        <div style={{ fontFamily: 'JetBrains Mono, monospace', fontSize: 12, letterSpacing: '0.22em', color: 'var(--text-dim)', textTransform: 'uppercase', marginBottom: 4 }}>
          Faites défiler
        </div>
        <svg width="14" height="18" viewBox="0 0 16 22" fill="none">
          <path d="M8 1V19M8 19L1 13M8 19L15 13" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round" strokeLinejoin="round" style={{ color: 'var(--text-dim)' }} />
        </svg>
      </div>
    </section>
  );
}

window.Hero = Hero;
