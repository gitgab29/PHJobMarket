import { useState, useEffect } from 'react'
import { BarChart, Bar, PieChart, Pie, Cell, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'
import { analyticsAPI } from '../api/client'

export default function DashboardPage() {
  const [summary, setSummary] = useState(null)
  const [salaryByLocation, setSalaryByLocation] = useState([])
  const [salaryByExperience, setSalaryByExperience] = useState([])
  const [jobsBySource, setJobsBySource] = useState([])
  const [remoteVsOnsite, setRemoteVsOnsite] = useState(null)
  const [skillTrends, setSkillTrends] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([
      analyticsAPI.dashboard(),
      analyticsAPI.salaryByLocation(),
      analyticsAPI.salaryByExperience(),
      analyticsAPI.jobsBySource(),
      analyticsAPI.remoteVsOnsite(),
      analyticsAPI.skillTrends(),
    ]).then(([
      sumRes,
      salLocRes,
      salExpRes,
      jobsSourceRes,
      remoteRes,
      skillRes,
    ]) => {
      setSummary(sumRes.data)
      setSalaryByLocation(salLocRes.data)
      setSalaryByExperience(salExpRes.data)
      setJobsBySource(jobsSourceRes.data)
      setRemoteVsOnsite(remoteRes.data)
      setSkillTrends(skillRes.data.slice(0, 10)) // Top 10 skills
      setLoading(false)
    }).catch(err => {
      console.error(err)
      setLoading(false)
    })
  }, [])

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-slate-600">Loading dashboard...</div>
      </div>
    )
  }

  const COLORS = ['#3b82f6', '#8b5cf6', '#ec4899', '#f59e0b', '#10b981', '#06b6d4']

  return (
    <div className="flex-1 bg-slate-50">
      <div className="max-w-7xl mx-auto px-6 py-8">
        {/* Summary Cards */}
        {summary && (
          <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-5 gap-4 mb-8">
            <SummaryCard
              label="Total Jobs"
              value={summary.total_jobs_count?.toLocaleString() || '0'}
              color="blue"
            />
            <SummaryCard
              label="Avg Salary"
              value={`₱${Math.round(summary.average_salary || 0).toLocaleString()}`}
              color="purple"
            />
            <SummaryCard
              label="Max Salary"
              value={`₱${Math.round(summary.max_salary || 0).toLocaleString()}`}
              color="pink"
            />
            <SummaryCard
              label="Top Location"
              value={summary.top_location || 'N/A'}
              color="amber"
            />
            <SummaryCard
              label="Top Company"
              value={summary.top_company || 'N/A'}
              color="green"
            />
          </div>
        )}

        {/* Charts Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Salary by Location */}
          <div className="bg-white rounded-lg border border-slate-200 p-6">
            <h3 className="text-lg font-semibold text-slate-900 mb-4">Salary by Location</h3>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={salaryByLocation}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                <XAxis dataKey="city" fontSize={12} />
                <YAxis fontSize={12} />
                <Tooltip formatter={(value) => `₱${Math.round(value).toLocaleString()}`} />
                <Bar dataKey="avg_salary" fill="#3b82f6" radius={[8, 8, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>

          {/* Jobs by Source */}
          <div className="bg-white rounded-lg border border-slate-200 p-6">
            <h3 className="text-lg font-semibold text-slate-900 mb-4">Jobs by Source</h3>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={jobsBySource}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ name, value }) => `${name} (${value})`}
                  outerRadius={100}
                  fill="#8884d8"
                  dataKey="count"
                  nameKey="source"
                >
                  {jobsBySource.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </div>

          {/* Salary by Experience */}
          <div className="bg-white rounded-lg border border-slate-200 p-6">
            <h3 className="text-lg font-semibold text-slate-900 mb-4">Salary by Experience</h3>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={salaryByExperience}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                <XAxis dataKey="level" fontSize={12} />
                <YAxis fontSize={12} />
                <Tooltip formatter={(value) => `₱${Math.round(value).toLocaleString()}`} />
                <Bar dataKey="avg_salary" fill="#8b5cf6" radius={[8, 8, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>

          {/* Remote vs Onsite */}
          {remoteVsOnsite && (
            <div className="bg-white rounded-lg border border-slate-200 p-6">
              <h3 className="text-lg font-semibold text-slate-900 mb-4">Remote vs Onsite</h3>
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie
                    data={[
                      { name: 'Remote', value: remoteVsOnsite.remote_count },
                      { name: 'Onsite', value: remoteVsOnsite.onsite_count },
                    ]}
                    cx="50%"
                    cy="50%"
                    innerRadius={60}
                    outerRadius={100}
                    paddingAngle={5}
                    dataKey="value"
                  >
                    <Cell fill="#10b981" />
                    <Cell fill="#3b82f6" />
                  </Pie>
                  <Tooltip />
                  <Legend />
                </PieChart>
              </ResponsiveContainer>
            </div>
          )}

          {/* Top Skills */}
          <div className="bg-white rounded-lg border border-slate-200 p-6">
            <h3 className="text-lg font-semibold text-slate-900 mb-4">Top Skills</h3>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={skillTrends}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                <XAxis dataKey="skill" fontSize={11} />
                <YAxis fontSize={12} />
                <Tooltip />
                <Bar dataKey="demand_count" fill="#ec4899" radius={[8, 8, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
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
