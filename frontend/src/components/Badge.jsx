export function SourceBadge({ source }) {
  const colors = {
    philjobnet: 'bg-red-100 text-red-800',
    kalibrr: 'bg-green-100 text-green-800',
    jobstreet: 'bg-purple-100 text-purple-800',
    onlinejobs: 'bg-amber-100 text-amber-800',
    indeed: 'bg-blue-100 text-blue-800',
    facebook: 'bg-blue-900 text-blue-100',
  }

  const sourceDisplay = {
    philjobnet: 'PhilJobNet',
    kalibrr: 'Kalibrr',
    jobstreet: 'JobStreet',
    onlinejobs: 'OnlineJobs',
    indeed: 'Indeed',
    facebook: 'Facebook',
  }

  return (
    <span className={`inline-block px-2 py-1 text-xs font-mono font-medium rounded-sm ${colors[source] || 'bg-slate-100 text-slate-800'}`}>
      {sourceDisplay[source] || source}
    </span>
  )
}

export function EmploymentTypeBadge({ type }) {
  if (!type) return null

  // Normalize messy real-world values ("full time", "full-time+2", "permanent"…)
  // into a small set of color buckets.
  const normalized = type.toLowerCase()
  const bucket =
    normalized.includes('full') ? 'fulltime'
    : normalized.includes('part') ? 'parttime'
    : normalized.includes('permanent') ? 'permanent'
    : normalized.includes('contract') ? 'contract'
    : normalized.includes('freelance') || normalized.includes('gig') ? 'freelance'
    : normalized.includes('intern') || normalized.includes('ojt') ? 'internship'
    : normalized.includes('project') ? 'project'
    : 'other'

  const colors = {
    fulltime: 'bg-blue-50 text-blue-700 border border-blue-200',
    parttime: 'bg-amber-50 text-amber-700 border border-amber-200',
    permanent: 'bg-indigo-50 text-indigo-700 border border-indigo-200',
    contract: 'bg-purple-50 text-purple-700 border border-purple-200',
    freelance: 'bg-green-50 text-green-700 border border-green-200',
    internship: 'bg-cyan-50 text-cyan-700 border border-cyan-200',
    project: 'bg-rose-50 text-rose-700 border border-rose-200',
    other: 'bg-slate-100 text-slate-700 border border-slate-200',
  }

  // Title-case for display, strip trailing "+N" noise from messy source data.
  const label = type
    .replace(/\+\d+$/, '')
    .split(/[\s/-]+/)
    .filter(Boolean)
    .map(w => w.charAt(0).toUpperCase() + w.slice(1))
    .join(' ')

  return (
    <span className={`inline-block px-2 py-1 text-xs font-medium rounded-sm ${colors[bucket]}`}>
      {label}
    </span>
  )
}

export function RemoteBadge() {
  return (
    <span className="inline-block px-2 py-1 text-xs font-medium rounded-sm bg-green-50 text-green-700 border border-green-200">
      Remote
    </span>
  )
}
