import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const client = axios.create({
  baseURL: `${API_BASE_URL}/api/v1`,
  headers: {
    'Content-Type': 'application/json',
  },
})

export const jobsAPI = {
  list: (params = {}) => client.get('/jobs/', { params }),
  detail: (id) => client.get(`/jobs/${id}/`),
  companies: (params = {}) => client.get('/companies/', { params }),
  locations: (params = {}) => client.get('/locations/', { params }),
  skills: (params = {}) => client.get('/skills/', { params }),
  topSkills: (limit = 20) => client.get('/skills/top/', { params: { limit } }),
}

export const analyticsAPI = {
  dashboard: () => client.get('/analytics/dashboard_summary/'),
  salaryByLocation: () => client.get('/analytics/salary_by_location/'),
  salaryByExperience: () => client.get('/analytics/salary_by_experience/'),
  jobsBySource: () => client.get('/analytics/jobs_by_source/'),
  remoteVsOnsite: () => client.get('/analytics/remote_vs_onsite/'),
  skillTrends: () => client.get('/analytics/skill_trends/'),
}

export default client
