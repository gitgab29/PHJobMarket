import axios from 'axios'

const client = axios.create({
  baseURL: '/api/v1',
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
  dashboard: () => client.get('/analytics/summary/'),
  salaryByLocation: () => client.get('/analytics/salary-by-location/'),
  salaryByExperience: () => client.get('/analytics/salary-by-experience/'),
  jobsBySource: () => client.get('/analytics/jobs-by-source/'),
  remoteVsOnsite: () => client.get('/analytics/remote-vs-onsite/'),
  skillTrends: () => client.get('/analytics/skill-trends/'),
}

export default client
