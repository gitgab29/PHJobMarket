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
  const colors = {
    fulltime: 'bg-blue-50 text-blue-700 border border-blue-200',
    'part-time': 'bg-amber-50 text-amber-700 border border-amber-200',
    contract: 'bg-purple-50 text-purple-700 border border-purple-200',
    freelance: 'bg-green-50 text-green-700 border border-green-200',
    temporary: 'bg-red-50 text-red-700 border border-red-200',
  }

  const displayText = {
    fulltime: 'Full-Time',
    'part-time': 'Part-Time',
    contract: 'Contract',
    freelance: 'Freelance',
    temporary: 'Temporary',
  }

  return (
    <span className={`inline-block px-2 py-1 text-xs font-medium rounded-sm ${colors[type] || 'bg-slate-100 text-slate-800'}`}>
      {displayText[type] || type}
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
