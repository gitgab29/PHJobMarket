import { useState, useEffect } from 'react'
import { BarChart, Bar, PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'
import { analyticsAPI, jobsAPI } from '../api/client'

const peso = (v) => `₱${Math.round(Number(v) || 0).toLocaleString()}`

const SOURCE_LABELS = {
  philjobnet: 'PhilJobNet',
  kalibrr: 'Kalibrr',
  jobstreet: 'JobStreet',
  onlinejobs: 'OnlineJobs',
  indeed: 'Indeed',
  facebook: 'Facebook',
}

export default function DashboardPage() {
  const [summary, setSummary] = useState(null)
  const [salaryByLocation, setSalaryByLocation] = useState([])
  const [salaryBySource, setSalaryBySource] = useState([])
  const [jobsBySource, setJobsBySource] = useState([])
  const [remoteVsOnsite, setRemoteVsOnsite] = useState(null)
  const [topSkills, setTopSkills] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    Promise.all([
      analyticsAPI.dashboard(),
      analyticsAPI.salaryByLocation(),
      analyticsAPI.salaryBySource(),
      analyticsAPI.jobsBySource(),
      analyticsAPI.remoteVsOnsite(),
      jobsAPI.topSkills(10),
    ]).then(([sumRes, salLocRes, salSrcRes, jobsSourceRes, remoteRes, skillRes]) => {
      setSummary(sumRes.data)
      setSalaryByLocation((salLocRes.data || []).slice(0, 12))
      setSalaryBySource((salSrcRes.data || []).map(d => ({ ...d, label: SOURCE_LABELS[d.source] || d.source })))
      setJobsBySource((jobsSourceRes.data || []).map(d => ({ ...d, label: SOURCE_LABELS[d.source] || d.source })))
      setRemoteVsOnsite(remoteRes.data)
      setTopSkills(skillRes.data || [])
      setLoading(false)
    }).catch(err => {
      console.error(err)
      setError(err.response?.data?.detail || err.message)
      setLoading(false)
    })
  }, [])

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="text-slate-600">Loading dashboard...</div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="text-red-600">Error loading dashboard: {error}</div>
      </div>
    )
  }

  const COLORS = ['#3b82f6', '#8b5cf6', '#ec4899', '#f59e0b', '#10b981', '#06b6d4']

  return (
    <div className="flex-1 bg-slate-50">
      <div className="max-w-7xl mx-auto px-6 py-8">
        {/* Summary Cards */}
        {summary && (
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4 mb-8">
            <SummaryCard label="Total Jobs" value={(summary.total_jobs ?? 0).toLocaleString()} color="blue" />
            <SummaryCard label="With Salary" value={(summary.jobs_with_salary ?? 0).toLocaleString()} color="purple" />
            <SummaryCard label="Remote Jobs" value={(summary.remote_jobs ?? 0).toLocaleString()} color="pink" />
            <SummaryCard label="Avg Min Salary" value={peso(summary.avg_salary_min_php)} color="amber" />
            <SummaryCard label="Avg Max Salary" value={peso(summary.avg_salary_max_php)} color="green" />
          </div>
        )}

        {/* Charts Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Salary by Location */}
          <ChartCard title="Average Salary by Location (PHP / month)" empty={salaryByLocation.length === 0}>
            <BarChart data={salaryByLocation} margin={{ bottom: 40 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
              <XAxis dataKey="city" fontSize={11} angle={-35} textAnchor="end" interval={0} height={60} />
              <YAxis fontSize={12} tickFormatter={(v) => `${Math.round(v / 1000)}k`} />
              <Tooltip formatter={(value) => peso(value)} />
              <Legend />
              <Bar dataKey="avg_salary_min" name="Avg Min" fill="#93c5fd" radius={[6, 6, 0, 0]} />
              <Bar dataKey="avg_salary_max" name="Avg Max" fill="#3b82f6" radius={[6, 6, 0, 0]} />
            </BarChart>
          </ChartCard>

          {/* Jobs by Source */}
          <ChartCard title="Jobs by Source" empty={jobsBySource.length === 0}>
            <PieChart>
              <Pie
                data={jobsBySource}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ label, value }) => `${label} (${value})`}
                outerRadius={100}
                dataKey="count"
                nameKey="label"
              >
                {jobsBySource.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ChartCard>

          {/* Average Salary by Source */}
          <ChartCard title="Average Salary by Source (PHP / month)" empty={salaryBySource.length === 0}>
            <BarChart data={salaryBySource}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
              <XAxis dataKey="label" fontSize={12} />
              <YAxis fontSize={12} tickFormatter={(v) => `${Math.round(v / 1000)}k`} />
              <Tooltip formatter={(value) => peso(value)} />
              <Legend />
              <Bar dataKey="avg_salary_min" name="Avg Min" fill="#c4b5fd" radius={[6, 6, 0, 0]} />
              <Bar dataKey="avg_salary_max" name="Avg Max" fill="#8b5cf6" radius={[6, 6, 0, 0]} />
            </BarChart>
          </ChartCard>

          {/* Remote vs Onsite */}
          {remoteVsOnsite && (
            <ChartCard title={`Remote vs Onsite (${remoteVsOnsite.remote_percentage ?? 0}% remote)`} empty={!remoteVsOnsite.total}>
              <PieChart>
                <Pie
                  data={[
                    { name: 'Remote', value: remoteVsOnsite.remote },
                    { name: 'Onsite', value: remoteVsOnsite.onsite },
                  ]}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={100}
                  paddingAngle={5}
                  dataKey="value"
                  label={({ name, value }) => `${name} (${value})`}
                >
                  <Cell fill="#10b981" />
                  <Cell fill="#3b82f6" />
                </Pie>
                <Tooltip />
                <Legend />
              </PieChart>
            </ChartCard>
          )}

          {/* Top Skills */}
          <ChartCard title="Top Skills by Demand" empty={topSkills.length === 0}>
            <BarChart data={topSkills} margin={{ bottom: 40 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
              <XAxis dataKey="skill_name" fontSize={11} angle={-35} textAnchor="end" interval={0} height={60} />
              <YAxis fontSize={12} />
              <Tooltip />
              <Bar dataKey="posting_count" name="Postings" fill="#ec4899" radius={[6, 6, 0, 0]} />
            </BarChart>
          </ChartCard>
        </div>
      </div>
    </div>
  )
}

function ChartCard({ title, empty, children }) {
  return (
    <div className="bg-white rounded-lg border border-slate-200 p-6">
      <h3 className="text-lg font-semibold text-slate-900 mb-4">{title}</h3>
      {empty ? (
        <div className="h-[300px] flex items-center justify-center text-slate-400 text-sm">
          No data available
        </div>
      ) : (
        <ResponsiveContainer width="100%" height={300}>
          {children}
        </ResponsiveContainer>
      )}
    </div>
  )
}

function SummaryCard({ label, value, color }) {
  const bgColors = {
    blue: 'bg-blue-50',
    purple: 'bg-purple-50',
    pink: 'bg-pink-50',
    amber: 'bg-amber-50',
    green: 'bg-green-50',
  }

  const textColors = {
    blue: 'text-blue-900',
    purple: 'text-purple-900',
    pink: 'text-pink-900',
    amber: 'text-amber-900',
    green: 'text-green-900',
  }

  return (
    <div className={`${bgColors[color]} rounded-lg p-6 border border-slate-200`}>
      <p className="text-xs font-medium text-slate-600 mb-2">{label}</p>
      <p className={`text-xl font-bold ${textColors[color]} truncate`}>{value}</p>
    </div>
  )
}
