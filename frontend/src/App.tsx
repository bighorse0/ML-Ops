import { Routes, Route } from 'react-router-dom'
import { Suspense, lazy } from 'react'
import Layout from './components/Layout'
import LoadingSpinner from './components/ui/LoadingSpinner'

// Lazy load pages for better performance
const Dashboard = lazy(() => import('./pages/Dashboard'))
const Features = lazy(() => import('./pages/Features'))
const FeatureDetail = lazy(() => import('./pages/FeatureDetail'))
const Monitoring = lazy(() => import('./pages/Monitoring'))
const Lineage = lazy(() => import('./pages/Lineage'))
const Settings = lazy(() => import('./pages/Settings'))
const Login = lazy(() => import('./pages/Login'))
const NotFound = lazy(() => import('./pages/NotFound'))

function App() {
  return (
    <div className="min-h-screen bg-background">
      <Suspense fallback={<LoadingSpinner />}>
        <Routes>
          {/* Public routes */}
          <Route path="/login" element={<Login />} />
          
          {/* Protected routes */}
          <Route path="/" element={<Layout />}>
            <Route index element={<Dashboard />} />
            <Route path="features" element={<Features />} />
            <Route path="features/:id" element={<FeatureDetail />} />
            <Route path="monitoring" element={<Monitoring />} />
            <Route path="lineage" element={<Lineage />} />
            <Route path="settings" element={<Settings />} />
          </Route>
          
          {/* 404 route */}
          <Route path="*" element={<NotFound />} />
        </Routes>
      </Suspense>
    </div>
  )
}

export default App 