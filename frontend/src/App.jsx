import { useState } from 'react'
import { BrowserRouter as Router, Routes, Route, useLocation } from 'react-router-dom'
import Header from './components/Header'
import JobsPage from './pages/JobsPage'
import DashboardPage from './pages/DashboardPage'
import EngineeringPage from './pages/EngineeringPage'

function AppContent() {
  const location = useLocation()
  const currentPage =
    location.pathname === '/dashboard' ? 'dashboard'
    : location.pathname === '/engineering' ? 'engineering'
    : 'jobs'

  return (
    <>
      <Header currentPage={currentPage} />
      <Routes>
        <Route path="/" element={<JobsPage />} />
        <Route path="/dashboard" element={<DashboardPage />} />
        <Route path="/engineering" element={<EngineeringPage />} />
      </Routes>
    </>
  )
}

export default function App() {
  return (
    <Router>
      <AppContent />
    </Router>
  )
}
