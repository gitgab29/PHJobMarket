import { Link } from 'react-router-dom'

export default function Header({ currentPage, onPageChange }) {
  return (
    <header className="bg-white border-b border-slate-200">
      <div className="max-w-7xl mx-auto px-6 py-4">
        <div className="flex items-center justify-between">
          <Link to="/" className="flex items-center gap-2">
            <div className="text-xl font-bold tracking-tight">
              <div className="text-slate-900">PH Job Market</div>
              <div className="text-xs text-slate-500 tracking-widest">TRACKER</div>
            </div>
          </Link>
          <nav className="flex gap-8">
            <Link
              to="/"
              className={`text-sm font-medium transition-colors ${
                currentPage === 'jobs'
                  ? 'text-blue-600 border-b-2 border-blue-600'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              Jobs
            </Link>
            <Link
              to="/dashboard"
              className={`text-sm font-medium transition-colors ${
                currentPage === 'dashboard'
                  ? 'text-blue-600 border-b-2 border-blue-600'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              Dashboard
            </Link>
          </nav>
        </div>
      </div>
    </header>
  )
}
