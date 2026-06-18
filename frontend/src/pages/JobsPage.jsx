import { useState, useEffect } from 'react'
import { jobsAPI } from '../api/client'
import { SourceBadge, EmploymentTypeBadge, RemoteBadge } from '../components/Badge'

export default function JobsPage() {
  const [jobs, setJobs] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [selectedJob, setSelectedJob] = useState(null)

  // Filters
  const [filters, setFilters] = useState({
    search: '',
    source: '',
    salary_min: '',
    salary_max: '',
    employment_type: '',
    location: '',
    company_name: '',
    is_remote: false,
  })

  const [sortBy, setSortBy] = useState('-date_posted')
  const [page, setPage] = useState(1)
  const [totalCount, setTotalCount] = useState(0)

  // Master data for dropdowns
  const [companies, setCompanies] = useState([])
  const [locations, setLocations] = useState([])

  useEffect(() => {
    Promise.all([
      jobsAPI.companies(),
      jobsAPI.locations(),
    ]).then(([compRes, locRes]) => {
      setCompanies(compRes.data.results || [])
      setLocations(locRes.data.results || [])
    }).catch(console.error)
  }, [])

  useEffect(() => {
    fetchJobs()
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
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  function handleFilterChange(field, value) {
    setFilters(prev => ({ ...prev, [field]: value }))
    setPage(1)
  }

  function formatSalary(min, max, currency) {
    if (!min && !max) return 'Negotiable'
    const symbol = currency === 'USD' ? '$' : '₱'
    const minStr = min ? `${symbol}${min.toLocaleString()}` : ''
    const maxStr = max ? `${symbol}${max.toLocaleString()}` : ''
    if (minStr && maxStr) return `${minStr} – ${maxStr}`
    return minStr || maxStr
  }

  function formatDate(dateStr) {
    if (!dateStr) return 'Date not available'
    const date = new Date(dateStr)
    if (isNaN(date.getTime())) return 'Date not available'
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    })
  }

  const pageSize = 25
  const totalPages = Math.ceil(totalCount / pageSize)

  return (
    <div className="flex-1 bg-slate-50">
      <div className="max-w-7xl mx-auto px-6 py-8">
        {/* Search and Filters */}
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6 mb-8">
          {/* Search */}
          <div className="lg:col-span-4">
            <input
              type="text"
              placeholder="Search jobs by title, company, or location..."
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
              value={filters.salary_min}
              onChange={(e) => handleFilterChange('salary_min', e.target.value)}
              className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-700 mb-2">Salary Max</label>
            <input
              type="number"
              placeholder="Max (PHP)"
              value={filters.salary_max}
              onChange={(e) => handleFilterChange('salary_max', e.target.value)}
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
              <option value="fulltime">Full-Time</option>
              <option value="part-time">Part-Time</option>
              <option value="contract">Contract</option>
              <option value="freelance">Freelance</option>
              <option value="temporary">Temporary</option>
            </select>
          </div>

          {/* Location */}
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-2">Location</label>
            <select
              value={filters.location}
              onChange={(e) => handleFilterChange('location', e.target.value)}
              className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">All</option>
              {locations.map(loc => (
                <option key={loc.city} value={loc.city}>{loc.city}, {loc.province}</option>
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
                <option key={comp.name} value={comp.name}>{comp.name}</option>
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
              {filters.is_remote ? '✓ Remote' : 'All'}
            </button>
          </div>

          {/* Sort */}
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-2">Sort By</label>
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value)}
              className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="-date_posted">Newest</option>
              <option value="-salary_max">Highest Salary</option>
              <option value="company_name">Company A-Z</option>
            </select>
          </div>
        </div>

        {/* Results Count and Sort */}
        <div className="flex justify-between items-center mb-6">
          <div className="text-sm text-slate-600">
            Showing {loading ? '...' : jobs.length} of {totalCount.toLocaleString()} jobs
          </div>
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
                key={job.id}
                className="bg-white border border-slate-200 rounded-lg p-6 hover:shadow-md transition cursor-pointer"
                onClick={() => setSelectedJob(job)}
              >
                <div className="flex justify-between items-start mb-2">
                  <div>
                    <h3 className="font-semibold text-lg text-slate-900">{job.title}</h3>
                    <p className="text-sm text-slate-600">{job.company_name}</p>
                  </div>
                  <SourceBadge source={job.source} />
                </div>

                <div className="flex flex-wrap gap-2 mb-4">
                  <span className="text-sm text-slate-600">{job.location}</span>
                  {job.is_remote && <RemoteBadge />}
                  <EmploymentTypeBadge type={job.employment_type} />
                </div>

                <div className="flex justify-between items-center text-sm">
                  <span className="font-mono text-slate-900">
                    {formatSalary(job.salary_min, job.salary_max, job.salary_currency)}
                  </span>
                  <span className="text-slate-500">
                    {new Date(job.date_posted).toLocaleDateString()}
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
              className="px-3 py-2 border border-slate-200 rounded-lg text-sm font-medium disabled:opacity-50"
            >
              Previous
            </button>
            <div className="flex items-center gap-1">
              {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
                const p = page <= 3 ? i + 1 : page + i - 2
                return p <= totalPages ? (
                  <button
                    key={p}
                    onClick={() => setPage(p)}
                    className={`px-3 py-2 rounded-lg text-sm font-medium ${
                      p === page ? 'bg-blue-600 text-white' : 'border border-slate-200'
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
              className="px-3 py-2 border border-slate-200 rounded-lg text-sm font-medium disabled:opacity-50"
            >
              Next
            </button>
          </div>
        )}
      </div>

      {/* Job Detail Modal/Drawer */}
      {selectedJob && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex justify-end">
          <div className="bg-white w-full max-w-md max-h-screen overflow-y-auto">
            <div className="p-6">
              <button
                onClick={() => setSelectedJob(null)}
                className="float-right text-slate-500 hover:text-slate-900"
              >
                ✕
              </button>
              <h2 className="text-2xl font-bold text-slate-900 mb-2">{selectedJob.title}</h2>
              <p className="text-slate-600 mb-4">{selectedJob.company_name}</p>

              <div className="space-y-4">
                <div>
                  <h3 className="text-sm font-medium text-slate-700 mb-1">Location</h3>
                  <p className="text-slate-900">{selectedJob.location}</p>
                </div>

                <div>
                  <h3 className="text-sm font-medium text-slate-700 mb-1">Salary</h3>
                  <p className="font-mono text-slate-900">
                    {formatSalary(selectedJob.salary_min, selectedJob.salary_max, selectedJob.salary_currency)}
                  </p>
                </div>

                <div>
                  <h3 className="text-sm font-medium text-slate-700 mb-2">Details</h3>
                  <div className="flex flex-wrap gap-2">
                    <EmploymentTypeBadge type={selectedJob.employment_type} />
                    <SourceBadge source={selectedJob.source} />
                    {selectedJob.is_remote && <RemoteBadge />}
                  </div>
                </div>

                <div>
                  <h3 className="text-sm font-medium text-slate-700 mb-1">Posted</h3>
                  <p className="text-slate-600">
                    {formatDate(selectedJob.date_posted)}
                  </p>
                </div>

                <a
                  href={selectedJob.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="block w-full bg-blue-600 text-white text-center font-medium py-2 rounded-lg hover:bg-blue-700 mt-6"
                >
                  View Full Posting
                </a>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
