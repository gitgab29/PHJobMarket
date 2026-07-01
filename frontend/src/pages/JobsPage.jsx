import { useState, useEffect } from 'react'
import { jobsAPI } from '../api/client'
import { SourceBadge, EmploymentTypeBadge, RemoteBadge } from '../components/Badge'

// date_posted_key is stored as a YYYYMMDD integer in the warehouse.
function formatDateKey(key, opts = { year: 'numeric', month: 'long', day: 'numeric' }) {
  if (!key) return 'Date not available'
  const s = String(key)
  if (s.length !== 8) return 'Date not available'
  const date = new Date(`${s.slice(0, 4)}-${s.slice(4, 6)}-${s.slice(6, 8)}T00:00:00`)
  if (isNaN(date.getTime())) return 'Date not available'
  return date.toLocaleDateString('en-US', opts)
}

function formatSalary(min, max, currency) {
  const minN = min != null && min !== '' ? Number(min) : null
  const maxN = max != null && max !== '' ? Number(max) : null
  if (!minN && !maxN) return 'Negotiable'
  const symbol = currency === 'USD' ? '$' : '₱'
  const fmt = (n) => `${symbol}${n.toLocaleString()}`
  if (minN && maxN) return `${fmt(minN)} – ${fmt(maxN)}`
  return fmt(minN || maxN)
}

export default function JobsPage() {
  const [jobs, setJobs] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [selectedJob, setSelectedJob] = useState(null)

  // Filters — keys match the Django API query params exactly.
  const [filters, setFilters] = useState({
    search: '',
    source: '',
    salary_min_gte: '',
    salary_max_lte: '',
    employment_type: '',
    city: '',
    company_name: '',
    is_remote: false,
  })

  const [sortBy, setSortBy] = useState('-date_posted_key')
  const [page, setPage] = useState(1)
  const [totalCount, setTotalCount] = useState(0)

  // Master data for dropdowns
  const [companies, setCompanies] = useState([])
  const [locations, setLocations] = useState([])

  useEffect(() => {
    Promise.all([
      jobsAPI.companies({ page_size: 2000, ordering: 'company_name' }),
      jobsAPI.locations({ page_size: 2000 }),
    ]).then(([compRes, locRes]) => {
      setCompanies(compRes.data.results || [])
      setLocations(locRes.data.results || [])
    }).catch(console.error)
  }, [])

  useEffect(() => {
    fetchJobs()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [filters, sortBy, page])

  async function fetchJobs() {
    try {
      setLoading(true)
      const params = {
        page,
        ordering: sortBy,
        ...Object.fromEntries(
          Object.entries(filters).filter(([_, v]) => v !== '' && v !== false)
        ),
      }
      const response = await jobsAPI.list(params)
      setJobs(response.data.results || [])
      setTotalCount(response.data.count || 0)
      setError(null)
    } catch (err) {
      setError(err.response?.data?.detail || err.message)
    } finally {
      setLoading(false)
    }
  }

  function handleFilterChange(field, value) {
    setFilters(prev => ({ ...prev, [field]: value }))
    setPage(1)
  }

  function resetFilters() {
    setFilters({
      search: '',
      source: '',
      salary_min_gte: '',
      salary_max_lte: '',
      employment_type: '',
      city: '',
      company_name: '',
      is_remote: false,
    })
    setPage(1)
  }

  const pageSize = 25
  const totalPages = Math.ceil(totalCount / pageSize)
  const hasActiveFilters = Object.values(filters).some(v => v !== '' && v !== false)

  // Unique, sorted city list for the dropdown.
  const cityOptions = Array.from(
    new Map(
      locations
        .filter(l => l.city)
        .map(l => [l.city, l])
    ).values()
  ).sort((a, b) => a.city.localeCompare(b.city))

  return (
    <div className="flex-1 bg-slate-50">
      <div className="max-w-7xl mx-auto px-6 py-8">
        {/* Search and Filters */}
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6 mb-8">
          {/* Search */}
          <div className="lg:col-span-4">
            <input
              type="text"
              placeholder="Search jobs by title, company, or description..."
              value={filters.search}
              onChange={(e) => handleFilterChange('search', e.target.value)}
              className="w-full px-4 py-3 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          {/* Salary Range */}
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-2">Salary Min</label>
            <input
              type="number"
              placeholder="Min (PHP)"
              value={filters.salary_min_gte}
              onChange={(e) => handleFilterChange('salary_min_gte', e.target.value)}
              className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-700 mb-2">Salary Max</label>
            <input
              type="number"
              placeholder="Max (PHP)"
              value={filters.salary_max_lte}
              onChange={(e) => handleFilterChange('salary_max_lte', e.target.value)}
              className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          {/* Employment Type */}
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-2">Employment Type</label>
            <select
              value={filters.employment_type}
              onChange={(e) => handleFilterChange('employment_type', e.target.value)}
              className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">Any</option>
              <option value="full time">Full Time</option>
              <option value="permanent">Permanent</option>
              <option value="contractual">Contractual</option>
              <option value="part time">Part Time</option>
              <option value="project-based">Project-Based</option>
              <option value="internship">Internship / OJT</option>
              <option value="freelance">Freelance</option>
              <option value="gig">Gig</option>
            </select>
          </div>

          {/* Location */}
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-2">Location</label>
            <select
              value={filters.city}
              onChange={(e) => handleFilterChange('city', e.target.value)}
              className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">All</option>
              {cityOptions.map(loc => (
                <option key={loc.location_key} value={loc.city}>
                  {loc.city}{loc.province ? `, ${loc.province}` : ''}
                </option>
              ))}
            </select>
          </div>

          {/* Company */}
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-2">Company</label>
            <select
              value={filters.company_name}
              onChange={(e) => handleFilterChange('company_name', e.target.value)}
              className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">All</option>
              {companies.map(comp => (
                <option key={comp.company_key} value={comp.company_name}>{comp.company_name}</option>
              ))}
            </select>
          </div>

          {/* Source */}
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-2">Source</label>
            <select
              value={filters.source}
              onChange={(e) => handleFilterChange('source', e.target.value)}
              className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">All</option>
              <option value="philjobnet">PhilJobNet</option>
              <option value="kalibrr">Kalibrr</option>
              <option value="jobstreet">JobStreet</option>
              <option value="onlinejobs">OnlineJobs</option>
              <option value="indeed">Indeed</option>
              <option value="facebook">Facebook</option>
            </select>
          </div>

          {/* Remote */}
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-2">Remote</label>
            <button
              onClick={() => handleFilterChange('is_remote', !filters.is_remote)}
              className={`w-full px-3 py-2 rounded-lg text-sm font-medium transition ${
                filters.is_remote
                  ? 'bg-green-100 text-green-800 border border-green-300'
                  : 'bg-white border border-slate-200 text-slate-700 hover:bg-slate-50'
              }`}
            >
              {filters.is_remote ? '✓ Remote only' : 'All'}
            </button>
          </div>

          {/* Sort */}
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-2">Sort By</label>
            <select
              value={sortBy}
              onChange={(e) => { setSortBy(e.target.value); setPage(1) }}
              className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="-date_posted_key">Newest</option>
              <option value="date_posted_key">Oldest</option>
              <option value="-salary_max">Highest Salary</option>
              <option value="salary_min">Lowest Salary</option>
              <option value="company__company_name">Company A–Z</option>
            </select>
          </div>
        </div>

        {/* Results Count and Reset */}
        <div className="flex justify-between items-center mb-6">
          <div className="text-sm text-slate-600">
            Showing {loading ? '...' : jobs.length} of {totalCount.toLocaleString()} jobs
          </div>
          {hasActiveFilters && (
            <button
              onClick={resetFilters}
              className="text-sm font-medium text-blue-600 hover:text-blue-800"
            >
              Clear filters
            </button>
          )}
        </div>

        {/* Jobs List */}
        <div className="space-y-4">
          {loading ? (
            <div className="text-center py-12 text-slate-500">Loading jobs...</div>
          ) : error ? (
            <div className="text-center py-12 text-red-600">Error: {error}</div>
          ) : jobs.length === 0 ? (
            <div className="text-center py-12 text-slate-500">No jobs found</div>
          ) : (
            jobs.map(job => (
              <div
                key={job.job_key}
                className="bg-white border border-slate-200 rounded-lg p-6 hover:shadow-md transition cursor-pointer"
                onClick={() => setSelectedJob(job)}
              >
                <div className="flex justify-between items-start mb-2">
                  <div>
                    <h3 className="font-semibold text-lg text-slate-900">{job.title}</h3>
                    <p className="text-sm text-slate-600">{job.company_name || 'Company not listed'}</p>
                  </div>
                  <SourceBadge source={job.source} />
                </div>

                <div className="flex flex-wrap gap-2 mb-4 items-center">
                  <span className="text-sm text-slate-600">
                    {job.city || job.region || 'Location not specified'}
                  </span>
                  {job.is_remote && <RemoteBadge />}
                  {job.employment_type && <EmploymentTypeBadge type={job.employment_type} />}
                </div>

                <div className="flex justify-between items-center text-sm">
                  <span className="font-mono text-slate-900">
                    {formatSalary(job.salary_min, job.salary_max, job.salary_currency)}
                  </span>
                  <span className="text-slate-500">
                    {formatDateKey(job.date_posted_key, { year: 'numeric', month: 'short', day: 'numeric' })}
                  </span>
                </div>
              </div>
            ))
          )}
        </div>

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="flex justify-center gap-2 mt-8">
            <button
              onClick={() => setPage(Math.max(1, page - 1))}
              disabled={page === 1}
              className="px-3 py-2 border border-slate-200 rounded-lg text-sm font-medium disabled:opacity-50 bg-white"
            >
              Previous
            </button>
            <div className="flex items-center gap-1">
              {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
                const p = page <= 3 ? i + 1 : Math.min(totalPages - 4, page - 2) + i
                return p >= 1 && p <= totalPages ? (
                  <button
                    key={p}
                    onClick={() => setPage(p)}
                    className={`px-3 py-2 rounded-lg text-sm font-medium ${
                      p === page ? 'bg-blue-600 text-white' : 'border border-slate-200 bg-white'
                    }`}
                  >
                    {p}
                  </button>
                ) : null
              })}
            </div>
            <button
              onClick={() => setPage(Math.min(totalPages, page + 1))}
              disabled={page === totalPages}
              className="px-3 py-2 border border-slate-200 rounded-lg text-sm font-medium disabled:opacity-50 bg-white"
            >
              Next
            </button>
          </div>
        )}
      </div>

      {/* Job Detail Drawer */}
      {selectedJob && (
        <div
          className="fixed inset-0 bg-black bg-opacity-50 flex justify-end z-50"
          onClick={() => setSelectedJob(null)}
        >
          <div
            className="bg-white w-full max-w-md max-h-screen overflow-y-auto"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="p-6">
              <button
                onClick={() => setSelectedJob(null)}
                className="float-right text-slate-500 hover:text-slate-900"
              >
                ✕
              </button>
              <h2 className="text-2xl font-bold text-slate-900 mb-2">{selectedJob.title}</h2>
              <p className="text-slate-600 mb-4">{selectedJob.company_name || 'Company not listed'}</p>

              <div className="space-y-4">
                <div>
                  <h3 className="text-sm font-medium text-slate-700 mb-1">Location</h3>
                  <p className="text-slate-900">
                    {[selectedJob.city, selectedJob.region].filter(Boolean).join(', ') || 'Not specified'}
                  </p>
                </div>

                <div>
                  <h3 className="text-sm font-medium text-slate-700 mb-1">Salary</h3>
                  <p className="font-mono text-slate-900">
                    {formatSalary(selectedJob.salary_min, selectedJob.salary_max, selectedJob.salary_currency)}
                    {selectedJob.salary_period ? ` / ${selectedJob.salary_period}` : ''}
                  </p>
                </div>

                <div>
                  <h3 className="text-sm font-medium text-slate-700 mb-2">Details</h3>
                  <div className="flex flex-wrap gap-2">
                    {selectedJob.employment_type && <EmploymentTypeBadge type={selectedJob.employment_type} />}
                    <SourceBadge source={selectedJob.source} />
                    {selectedJob.is_remote && <RemoteBadge />}
                  </div>
                </div>

                <div>
                  <h3 className="text-sm font-medium text-slate-700 mb-1">Posted</h3>
                  <p className="text-slate-600">{formatDateKey(selectedJob.date_posted_key)}</p>
                </div>

                {selectedJob.url && (
                  <a
                    href={selectedJob.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="block w-full bg-blue-600 text-white text-center font-medium py-2 rounded-lg hover:bg-blue-700 mt-6"
                  >
                    View Full Posting
                  </a>
                )}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
