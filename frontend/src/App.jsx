import { useState } from 'react'
import { BrowserRouter as Router, Routes, Route, useLocation } from 'react-router-dom'
import Header from './components/Header'
import JobsPage from './pages/JobsPage'
import DashboardPage from './pages/DashboardPage'

function AppContent() {
  const location = useLocation()
  const currentPage = location.pathname === '/dashboard' ? 'dashboard' : 'jobs'

  return (
    <>
      <Header currentPage={currentPage} />
      <Routes>
        <Route path="/" element={<JobsPage />} />
        <Route path="/dashboard" element={<DashboardPage />} />
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
