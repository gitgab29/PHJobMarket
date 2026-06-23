import { BarChart, Bar, PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, LabelList } from 'recharts'

/*
 * EngineeringPage — a dedicated, self-contained narrative of how this project was
 * built, aimed at potential employers. All figures here are STATIC on purpose
 * (sourced from PROJECT_REVIEW.md) so the page tells the engineering story
 * reliably even when the local database / API isn't running.
 */

const ACCENT = 'oklch(0.55 0.17 250)'
const ACCENT_SOFT = 'oklch(0.78 0.10 250)'

// --- Static, grounded build data -------------------------------------------

const RECORDS_BY_SOURCE = [
  { source: 'JobStreet', records: 930, technique: 'HTML + Redux extraction' },
  { source: 'PhilJobNet', records: 500, technique: 'HTML (ASP.NET pagination)' },
  { source: 'Kalibrr', records: 489, technique: 'Internal API interception' },
  { source: 'OnlineJobs', records: 120, technique: 'CSS scraping (remote/USD)' },
  { source: 'Indeed', records: 32, technique: 'HTML w/ CAPTCHA bail-out' },
  { source: 'Facebook', records: 0, technique: 'Stub (ToS / cookie capture)' },
]

const DBT_COMPOSITION = [
  { name: 'Tests', value: 36 },
  { name: 'Models', value: 11 },
  { name: 'Seeds', value: 2 },
]
const DBT_COLORS = [ACCENT, ACCENT_SOFT, 'oklch(0.88 0.05 250)']

const PIPELINE = [
  { n: '01', verb: 'Scrape', tool: 'Playwright', note: '6 job sites → raw JSON, driving a real browser so JS-heavy sites render.' },
  { n: '02', verb: 'Store', tool: 'PostgreSQL · JSONB', note: 'Raw data saved exactly as scraped, untouched and immutable.' },
  { n: '03', verb: 'Transform', tool: 'dbt Core', note: 'Staging → intermediate → marts. Builds a tested star-schema warehouse.' },
  { n: '04', verb: 'Serve', tool: 'Django REST', note: '12 read-only endpoints over the warehouse (models are managed=False).' },
  { n: '05', verb: 'Visualize', tool: 'React · Recharts', note: 'This dashboard — filters, search, and salary / skill analytics.' },
]

const CROSS_CUTTING = [
  { label: 'Orchestration', tool: 'Airflow', note: 'Runs the pipeline nightly with retries, backoff & dependency ordering.' },
  { label: 'Data quality', tool: 'Great Expectations', note: 'Business-rule checks — fails loudly before serving bad data.' },
  { label: 'Packaging', tool: 'Docker Compose', note: 'One command spins up Postgres + Airflow. Reproducible everywhere.' },
]

const TECH = [
  { logo: 'python', name: 'Python', role: 'Language' },
  { logo: 'playwright', name: 'Playwright', role: 'Scraping' },
  { logo: 'postgresql', name: 'PostgreSQL', role: 'Database · SQL' },
  { logo: 'dbt', name: 'dbt Core', role: 'Transformation' },
  { logo: 'apacheairflow', name: 'Airflow', role: 'Orchestration' },
  { logo: 'django', name: 'Django REST', role: 'API' },
  { logo: 'react', name: 'React', role: 'Frontend' },
  { logo: 'vite', name: 'Vite', role: 'Build tool' },
  { logo: 'tailwindcss', name: 'Tailwind', role: 'Styling' },
  { logo: 'docker', name: 'Docker', role: 'Packaging' },
]

const DBT_LAYERS = [
  { tag: 'staging', mat: 'views', desc: 'One view per source. Pulls fields out of the JSONB blob and renames them to a consistent schema.' },
  { tag: 'intermediate', mat: 'ephemeral', desc: 'Business logic: unify all sources, de-duplicate to one row per real job, parse salaries, extract skills.' },
  { tag: 'marts', mat: 'tables', desc: 'The star schema — dim_companies / locations / skills / date + fct_job_postings / skill_demand.' },
]

const DECISIONS = [
  { d: 'Store raw JSONB, never transform in the scraper', why: 'Decouples collection from processing. Improve the parser → re-run dbt, don\'t re-scrape the web.' },
  { d: 'dbt owns the tables, Django only reads them', why: 'managed=False keeps a single source of truth for the schema — no two tools fighting over migrations.' },
  { d: 'Star schema over one big table', why: 'Fast aggregations, no repeated text, intuitive for analytics and BI tools.' },
  { d: 'LEFT joins in the fact table', why: 'Completeness over convenience — a job missing a salary or city still appears, with a NULL key.' },
  { d: 'Word-boundary regex for skill matching', why: 'Substring matching gives false positives — "java" would match "javascript". Boundaries fix that.' },
  { d: 'Idempotent upserts (ON CONFLICT)', why: 'Re-running any scraper is always safe — it updates rows instead of creating duplicates.' },
]

const LIMITATIONS = [
  'Modest data volume (~2k jobs); some sources are heavily rate-limited (Indeed ~32) without paid proxies.',
  'Facebook is intentionally a stub — it raises ToS / ethics questions and needs manual cookie capture.',
  'Skill-demand is a single snapshot, so "trends over time" needs the pipeline to run for weeks to build history.',
  'Runs locally via Docker Compose — not yet deployed to a cloud host with a real domain and HTTPS.',
]

// --- Page -------------------------------------------------------------------

export default function EngineeringPage() {
  return (
    <div className="flex-1 bg-slate-50">
      <div className="max-w-6xl mx-auto px-6 py-12 md:py-16">

        {/* Identity header */}
        <div className="flex flex-col sm:flex-row sm:items-center gap-5 mb-10">
          <img
            src="/me.jpg"
            alt="Portrait"
            className="h-20 w-20 rounded-2xl object-cover ring-1 ring-slate-200 shadow-sm shrink-0"
          />
          <div className="flex-1">
            <p className="font-bold text-slate-900 text-lg leading-tight">Gabriel Jericho Limbo</p>
            <p className="text-sm text-slate-500">4th-year Computer Engineering student · Data-engineering practice project</p>
          </div>
          <a
            href="https://github.com/gitgab29/PHJobMarket"
            target="_blank"
            rel="noreferrer"
            className="group inline-flex items-center gap-2.5 rounded-md border border-slate-200 bg-white px-4 py-2.5 text-sm font-medium text-slate-700 transition-colors hover:border-slate-300 hover:bg-slate-50 self-start"
          >
            <img src="/logos/github.svg" alt="" className="h-4 w-4" />
            <span>View source</span>
            <span className="mono text-[0.65rem] uppercase tracking-wider text-amber-700 bg-amber-50 rounded px-1.5 py-0.5">
              public soon
            </span>
          </a>
        </div>

        {/* Intro / note to employers */}
        <section className="max-w-3xl">
          <p className="mono text-xs uppercase tracking-[0.2em] text-accent-600 mb-4">
            For hiring teams · the engineering story
          </p>
          <h1 className="text-3xl md:text-[2.6rem] font-extrabold tracking-tight text-slate-900 leading-[1.1]">
            How this was built, and why I built it
          </h1>
          <div className="mt-6 space-y-4 text-slate-600 text-[1.05rem] leading-relaxed">
            <p>
              I'm a 4th-year Computer Engineering student. This dashboard isn't the point —
              it's the <span className="text-slate-900 font-semibold">visible tip of a full data-engineering pipeline</span> I
              built to practice the craft end to end: collecting messy real-world data, modeling it
              cleanly, testing it, orchestrating it, and serving it.
            </p>
            <p>
              I didn't strictly need to build any of this. I built it to learn how the pieces of a
              modern analytics stack actually fit together — and to have something concrete to walk
              you through. Below is the architecture, the numbers, and the decisions behind it,
              technical enough to be real but written to be readable.
            </p>
          </div>
        </section>

        {/* Pipeline diagram */}
        <Section
          eyebrow="The pipeline"
          title="Data flows one direction, through five stages"
          sub="Raw data comes in messy and is never edited in place. Every layer is a new transformation built on the last — so any number on this dashboard traces back through the API → a warehouse table → a dbt model → the original raw JSON."
        >
          <div className="grid gap-3 lg:grid-cols-5">
            {PIPELINE.map((s, i) => (
              <div key={s.n} className="relative">
                <div className="h-full rounded-md border border-slate-200 bg-white p-5 shadow-[0_1px_0_rgba(0,0,0,0.03)]">
                  <div className="flex items-center gap-2 mb-3">
                    <span className="mono text-xs text-accent-600 font-semibold">{s.n}</span>
                    <span className="h-px flex-1 bg-slate-100" />
                  </div>
                  <h3 className="font-bold text-slate-900">{s.verb}</h3>
                  <p className="mono text-[0.7rem] text-accent-600 mt-0.5 mb-2">{s.tool}</p>
                  <p className="text-[0.82rem] text-slate-500 leading-snug">{s.note}</p>
                </div>
                {i < PIPELINE.length - 1 && (
                  <div className="hidden lg:flex absolute top-1/2 -right-[11px] z-10 -translate-y-1/2 items-center justify-center">
                    <span className="text-accent-500 text-lg">→</span>
                  </div>
                )}
              </div>
            ))}
          </div>

          {/* Cross-cutting band */}
          <div className="mt-3 grid gap-3 md:grid-cols-3">
            {CROSS_CUTTING.map((c) => (
              <div key={c.label} className="rounded-md border border-dashed border-slate-300 bg-slate-50 p-4">
                <div className="flex items-baseline justify-between">
                  <span className="mono text-[0.68rem] uppercase tracking-wider text-slate-400">{c.label}</span>
                  <span className="mono text-xs font-semibold text-slate-700">{c.tool}</span>
                </div>
                <p className="text-[0.8rem] text-slate-500 mt-1.5 leading-snug">{c.note}</p>
              </div>
            ))}
          </div>
        </Section>

        {/* Tech stack */}
        <Section
          eyebrow="The toolkit"
          title="The tools I used — and where each one fits"
          sub="A deliberately modern analytics stack. Each logo maps to a stage in the pipeline above."
        >
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-5 gap-3">
            {TECH.map((t) => (
              <div
                key={t.name}
                className="flex flex-col items-center justify-center gap-2.5 rounded-md border border-slate-200 bg-white p-5 text-center transition-colors hover:border-slate-300"
              >
                <img src={`/logos/${t.logo}.svg`} alt={`${t.name} logo`} className="h-9 w-9 object-contain" />
                <div>
                  <p className="text-sm font-semibold text-slate-900 leading-tight">{t.name}</p>
                  <p className="mono text-[0.68rem] uppercase tracking-wider text-slate-400 mt-0.5">{t.role}</p>
                </div>
              </div>
            ))}
          </div>
          <p className="mt-3 text-sm text-slate-400">
            Also in the stack: Great Expectations (data-quality checks) and Recharts (the charts on this page).
          </p>
        </Section>

        {/* By the numbers */}
        <Section eyebrow="By the numbers" title="What the pipeline produces">
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
            <Stat value="6" label="job sources" />
            <Stat value="~2,071" label="job postings" />
            <Stat value="49" label="dbt checks passing" accent />
            <Stat value="13/13" label="parser unit tests" />
            <Stat value="12" label="API endpoints" />
            <Stat value="767" label="parsed salaries" />
          </div>
        </Section>

        {/* Charts */}
        <Section
          eyebrow="The build, measured"
          title="Where the data comes from — and what's tested"
          sub="Record counts are honest: each source has a different realistic ceiling depending on how aggressively it's bot-protected."
        >
          <div className="grid gap-6 lg:grid-cols-5">
            <ChartCard className="lg:col-span-3" title="Raw records collected per source">
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={RECORDS_BY_SOURCE} layout="vertical" margin={{ left: 8, right: 40 }}>
                  <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="#e8edf3" />
                  <XAxis type="number" fontSize={11} stroke="#94a3b8" />
                  <YAxis type="category" dataKey="source" width={86} fontSize={12} stroke="#475569" tickLine={false} axisLine={false} />
                  <Tooltip
                    cursor={{ fill: 'oklch(0.95 0.02 250)' }}
                    formatter={(v) => [`${v} records`, 'Collected']}
                    labelFormatter={(l) => {
                      const row = RECORDS_BY_SOURCE.find((r) => r.source === l)
                      return `${l} — ${row?.technique ?? ''}`
                    }}
                  />
                  <Bar dataKey="records" fill={ACCENT} radius={[0, 5, 5, 0]}>
                    <LabelList dataKey="records" position="right" fontSize={11} fill="#64748b" />
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </ChartCard>

            <ChartCard className="lg:col-span-2" title="dbt build — 49 checks">
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie
                    data={DBT_COMPOSITION}
                    dataKey="value"
                    nameKey="name"
                    cx="50%"
                    cy="50%"
                    innerRadius={62}
                    outerRadius={96}
                    paddingAngle={3}
                    label={({ name, value }) => `${name} ${value}`}
                    fontSize={12}
                  >
                    {DBT_COMPOSITION.map((_, i) => (
                      <Cell key={i} fill={DBT_COLORS[i]} stroke="#fff" strokeWidth={2} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
              <p className="text-center text-xs text-slate-400 -mt-2">
                11 models + 36 tests + 2 seeds · 0 errors
              </p>
            </ChartCard>
          </div>
        </Section>

        {/* dbt layers */}
        <Section
          eyebrow="The transformation"
          title="Three dbt layers turn JSON into a warehouse"
          sub="This is the heart of the data-engineering story — raw JSONB on the left, a clean, queryable star schema on the right."
        >
          <div className="grid gap-3 md:grid-cols-3">
            {DBT_LAYERS.map((l, i) => (
              <div key={l.tag} className="relative rounded-md border border-slate-200 bg-white p-5">
                <div className="flex items-center justify-between mb-3">
                  <span className="mono text-sm font-semibold text-slate-900">{l.tag}</span>
                  <span className="mono text-[0.66rem] uppercase tracking-wider text-slate-400 px-2 py-0.5 rounded bg-slate-100">
                    {l.mat}
                  </span>
                </div>
                <p className="text-[0.86rem] text-slate-500 leading-snug">{l.desc}</p>
                {i < DBT_LAYERS.length - 1 && (
                  <div className="hidden md:flex absolute top-1/2 -right-[11px] z-10 -translate-y-1/2 text-slate-300">→</div>
                )}
              </div>
            ))}
          </div>
        </Section>

        {/* Decisions */}
        <Section
          eyebrow="Engineering decisions"
          title="The choices I can defend"
          sub="Each of these was deliberate. Knowing the why behind them matters more than the code itself."
        >
          <div className="grid gap-3 md:grid-cols-2">
            {DECISIONS.map((x) => (
              <div key={x.d} className="rounded-md border border-slate-200 bg-white p-5">
                <h3 className="font-semibold text-slate-900 text-[0.95rem] leading-snug">{x.d}</h3>
                <p className="text-[0.85rem] text-slate-500 mt-2 leading-relaxed">{x.why}</p>
              </div>
            ))}
          </div>
        </Section>

        {/* Limitations */}
        <Section
          eyebrow="Honest limitations"
          title="What I'd improve next"
          sub="Being upfront about the edges of a project is part of the engineering."
        >
          <ul className="grid gap-2.5 md:grid-cols-2">
            {LIMITATIONS.map((l) => (
              <li key={l} className="flex gap-3 rounded-md bg-white border border-slate-200 p-4 text-[0.86rem] text-slate-600 leading-snug">
                <span className="mono text-accent-500 select-none">›</span>
                <span>{l}</span>
              </li>
            ))}
          </ul>
        </Section>

        <p className="mt-14 text-sm text-slate-400 border-t border-slate-200 pt-6">
          Want the deep version? Happy to walk through the codebase, the dbt DAG, or a live demo —
          scrapers, warehouse, API, and this dashboard all run from one Docker Compose stack.
        </p>
      </div>
    </div>
  )
}

// --- Small presentational helpers ------------------------------------------

function Section({ eyebrow, title, sub, children }) {
  return (
    <section className="mt-16 md:mt-20">
      <p className="mono text-xs uppercase tracking-[0.2em] text-accent-600 mb-2">{eyebrow}</p>
      <h2 className="text-xl md:text-2xl font-bold tracking-tight text-slate-900">{title}</h2>
      {sub && <p className="mt-2 max-w-3xl text-slate-500 leading-relaxed">{sub}</p>}
      <div className="mt-6">{children}</div>
    </section>
  )
}

function Stat({ value, label, accent }) {
  return (
    <div className={`rounded-md border p-4 ${accent ? 'border-accent-500/30 bg-accent-50' : 'border-slate-200 bg-white'}`}>
      <p className="mono text-2xl font-bold text-slate-900 tnum">{value}</p>
      <p className="text-[0.75rem] text-slate-500 mt-1">{label}</p>
    </div>
  )
}

function ChartCard({ title, children, className = '' }) {
  return (
    <div className={`rounded-md border border-slate-200 bg-white p-5 ${className}`}>
      <h3 className="font-semibold text-slate-900 mb-4 text-[0.95rem]">{title}</h3>
      {children}
    </div>
  )
}
