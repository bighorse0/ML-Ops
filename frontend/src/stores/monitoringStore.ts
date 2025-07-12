import { create } from 'zustand'
import { devtools, persist } from 'zustand/middleware'
import { immer } from 'zustand/middleware/immer'

export interface DataQualityMetric {
  id: number
  feature_id: number
  metric_type: string
  value: number
  threshold: number
  status: string
  metadata: Record<string, any>
  timestamp: string
  created_at: string
  updated_at: string
  created_by: number
  organization_id: number
}

export interface PerformanceMetric {
  id: number
  service_name: string
  metric_name: string
  value: number
  unit: string
  labels: Record<string, string>
  timestamp: string
  created_at: string
  updated_at: string
  created_by: number
  organization_id: number
}

export interface Alert {
  id: number
  title: string
  description: string
  severity: string
  source: string
  metadata: Record<string, any>
  status: string
  created_at: string
  updated_at: string
  created_by: number
  organization_id: number
}

export interface AlertRule {
  id: number
  name: string
  description: string
  condition: Record<string, any>
  severity: string
  is_active: boolean
  created_at: string
  updated_at: string
  created_by: number
  organization_id: number
}

export interface MonitoringDashboard {
  recent_quality_metrics: DataQualityMetric[]
  recent_performance_metrics: PerformanceMetric[]
  active_alerts: Alert[]
  summary: Record<string, any>
}

export interface TimeSeriesData {
  timestamp: string
  value: number
  labels?: Record<string, string>
}

interface MonitoringState {
  // State
  dataQualityMetrics: DataQualityMetric[]
  performanceMetrics: PerformanceMetric[]
  alerts: Alert[]
  alertRules: AlertRule[]
  dashboard: MonitoringDashboard | null
  timeSeriesData: TimeSeriesData[]
  loading: boolean
  error: string | null
  
  // Actions
  setDataQualityMetrics: (metrics: DataQualityMetric[]) => void
  setPerformanceMetrics: (metrics: PerformanceMetric[]) => void
  setAlerts: (alerts: Alert[]) => void
  setAlertRules: (rules: AlertRule[]) => void
  setDashboard: (dashboard: MonitoringDashboard) => void
  setTimeSeriesData: (data: TimeSeriesData[]) => void
  setLoading: (loading: boolean) => void
  setError: (error: string | null) => void
  
  // API Operations
  fetchDataQualityMetrics: (params?: { feature_id?: number; metric_type?: string; start_timestamp?: string; end_timestamp?: string }) => Promise<void>
  fetchPerformanceMetrics: (params?: { service_name?: string; metric_name?: string; start_timestamp?: string; end_timestamp?: string }) => Promise<void>
  fetchAlerts: (params?: { severity?: string; status?: string; source?: string }) => Promise<void>
  fetchAlertRules: () => Promise<void>
  fetchDashboard: () => Promise<void>
  fetchTimeSeriesData: (metricName: string, startTimestamp: string, endTimestamp: string, interval?: string) => Promise<void>
  
  // CRUD Operations
  createAlert: (alert: Omit<Alert, 'id' | 'created_at' | 'updated_at' | 'created_by' | 'organization_id'>) => Promise<void>
  updateAlertStatus: (id: number, status: string) => Promise<void>
  createAlertRule: (rule: Omit<AlertRule, 'id' | 'created_at' | 'updated_at' | 'created_by' | 'organization_id'>) => Promise<void>
  
  // Utility
  clearError: () => void
}

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api'

export const useMonitoringStore = create<MonitoringState>()(
  devtools(
    persist(
      immer((set) => ({
        // Initial state
        dataQualityMetrics: [],
        performanceMetrics: [],
        alerts: [],
        alertRules: [],
        dashboard: null,
        timeSeriesData: [],
        loading: false,
        error: null,

        // Basic setters
        setDataQualityMetrics: (metrics) => set((state) => { state.dataQualityMetrics = metrics }),
        setPerformanceMetrics: (metrics) => set((state) => { state.performanceMetrics = metrics }),
        setAlerts: (alerts) => set((state) => { state.alerts = alerts }),
        setAlertRules: (rules) => set((state) => { state.alertRules = rules }),
        setDashboard: (dashboard) => set((state) => { state.dashboard = dashboard }),
        setTimeSeriesData: (data) => set((state) => { state.timeSeriesData = data }),
        setLoading: (loading) => set((state) => { state.loading = loading }),
        setError: (error) => set((state) => { state.error = error }),

        // API Operations
        fetchDataQualityMetrics: async (params = {}) => {
          set((state) => { state.loading = true; state.error = null })
          
          try {
            const queryParams = new URLSearchParams()
            Object.entries(params).forEach(([key, value]) => {
              if (value !== undefined && value !== null && value !== '') {
                queryParams.append(key, value.toString())
              }
            })

            const response = await fetch(`${API_BASE_URL}/monitoring/data-quality?${queryParams}`, {
              headers: {
                'Authorization': `Bearer ${localStorage.getItem('token')}`
              }
            })

            if (!response.ok) {
              throw new Error(`Failed to fetch data quality metrics: ${response.statusText}`)
            }

            const data = await response.json()
            set((state) => {
              state.dataQualityMetrics = data.items || data
              state.loading = false
            })
          } catch (error) {
            set((state) => {
              state.error = error instanceof Error ? error.message : 'Failed to fetch data quality metrics'
              state.loading = false
            })
          }
        },

        fetchPerformanceMetrics: async (params = {}) => {
          set((state) => { state.loading = true; state.error = null })
          
          try {
            const queryParams = new URLSearchParams()
            Object.entries(params).forEach(([key, value]) => {
              if (value !== undefined && value !== null && value !== '') {
                queryParams.append(key, value.toString())
              }
            })

            const response = await fetch(`${API_BASE_URL}/monitoring/performance?${queryParams}`, {
              headers: {
                'Authorization': `Bearer ${localStorage.getItem('token')}`
              }
            })

            if (!response.ok) {
              throw new Error(`Failed to fetch performance metrics: ${response.statusText}`)
            }

            const data = await response.json()
            set((state) => {
              state.performanceMetrics = data.items || data
              state.loading = false
            })
          } catch (error) {
            set((state) => {
              state.error = error instanceof Error ? error.message : 'Failed to fetch performance metrics'
              state.loading = false
            })
          }
        },

        fetchAlerts: async (params = {}) => {
          set((state) => { state.loading = true; state.error = null })
          
          try {
            const queryParams = new URLSearchParams()
            Object.entries(params).forEach(([key, value]) => {
              if (value !== undefined && value !== null && value !== '') {
                queryParams.append(key, value.toString())
              }
            })

            const response = await fetch(`${API_BASE_URL}/monitoring/alerts?${queryParams}`, {
              headers: {
                'Authorization': `Bearer ${localStorage.getItem('token')}`
              }
            })

            if (!response.ok) {
              throw new Error(`Failed to fetch alerts: ${response.statusText}`)
            }

            const data = await response.json()
            set((state) => {
              state.alerts = data.items || data
              state.loading = false
            })
          } catch (error) {
            set((state) => {
              state.error = error instanceof Error ? error.message : 'Failed to fetch alerts'
              state.loading = false
            })
          }
        },

        fetchAlertRules: async () => {
          set((state) => { state.loading = true; state.error = null })
          
          try {
            const response = await fetch(`${API_BASE_URL}/monitoring/alert-rules`, {
              headers: {
                'Authorization': `Bearer ${localStorage.getItem('token')}`
              }
            })

            if (!response.ok) {
              throw new Error(`Failed to fetch alert rules: ${response.statusText}`)
            }

            const rules = await response.json()
            set((state) => {
              state.alertRules = rules
              state.loading = false
            })
          } catch (error) {
            set((state) => {
              state.error = error instanceof Error ? error.message : 'Failed to fetch alert rules'
              state.loading = false
            })
          }
        },

        fetchDashboard: async () => {
          set((state) => { state.loading = true; state.error = null })
          
          try {
            const response = await fetch(`${API_BASE_URL}/monitoring/dashboard`, {
              headers: {
                'Authorization': `Bearer ${localStorage.getItem('token')}`
              }
            })

            if (!response.ok) {
              throw new Error(`Failed to fetch dashboard: ${response.statusText}`)
            }

            const dashboard = await response.json()
            set((state) => {
              state.dashboard = dashboard
              state.loading = false
            })
          } catch (error) {
            set((state) => {
              state.error = error instanceof Error ? error.message : 'Failed to fetch dashboard'
              state.loading = false
            })
          }
        },

        fetchTimeSeriesData: async (metricName, startTimestamp, endTimestamp, interval = '1h') => {
          set((state) => { state.loading = true; state.error = null })
          
          try {
            const queryParams = new URLSearchParams({
              start_timestamp: startTimestamp,
              end_timestamp: endTimestamp,
              interval
            })

            const response = await fetch(`${API_BASE_URL}/monitoring/metrics/${metricName}?${queryParams}`, {
              headers: {
                'Authorization': `Bearer ${localStorage.getItem('token')}`
              }
            })

            if (!response.ok) {
              throw new Error(`Failed to fetch time series data: ${response.statusText}`)
            }

            const data = await response.json()
            set((state) => {
              state.timeSeriesData = data.data || []
              state.loading = false
            })
          } catch (error) {
            set((state) => {
              state.error = error instanceof Error ? error.message : 'Failed to fetch time series data'
              state.loading = false
            })
          }
        },

        // CRUD Operations
        createAlert: async (alertData) => {
          set((state) => { state.loading = true; state.error = null })
          
          try {
            const response = await fetch(`${API_BASE_URL}/monitoring/alerts`, {
              method: 'POST',
              headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${localStorage.getItem('token')}`
              },
              body: JSON.stringify(alertData)
            })

            if (!response.ok) {
              throw new Error(`Failed to create alert: ${response.statusText}`)
            }

            const newAlert = await response.json()
            set((state) => {
              state.alerts.unshift(newAlert)
              state.loading = false
            })
          } catch (error) {
            set((state) => {
              state.error = error instanceof Error ? error.message : 'Failed to create alert'
              state.loading = false
            })
          }
        },

        updateAlertStatus: async (id, status) => {
          set((state) => { state.loading = true; state.error = null })
          try {
            const response = await fetch(`${API_BASE_URL}/monitoring/alerts/${id}/status`, {
              method: 'PUT',
              headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${localStorage.getItem('token')}`
              },
              body: JSON.stringify({ status })
            })
            if (!response.ok) {
              throw new Error(`Failed to update alert status: ${response.statusText}`)
            }
            set((state) => {
              const index = state.alerts.findIndex((a: Alert) => a.id === id)
              if (index !== -1) {
                state.alerts[index].status = status
              }
              state.loading = false
            })
          } catch (error) {
            set((state) => {
              state.error = error instanceof Error ? error.message : 'Failed to update alert status'
              state.loading = false
            })
          }
        },

        createAlertRule: async (ruleData) => {
          set((state) => { state.loading = true; state.error = null })
          
          try {
            const response = await fetch(`${API_BASE_URL}/monitoring/alert-rules`, {
              method: 'POST',
              headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${localStorage.getItem('token')}`
              },
              body: JSON.stringify(ruleData)
            })

            if (!response.ok) {
              throw new Error(`Failed to create alert rule: ${response.statusText}`)
            }

            const newRule = await response.json()
            set((state) => {
              state.alertRules.unshift(newRule)
              state.loading = false
            })
          } catch (error) {
            set((state) => {
              state.error = error instanceof Error ? error.message : 'Failed to create alert rule'
              state.loading = false
            })
          }
        },

        // Utility functions
        clearError: () => set((state) => { state.error = null })
      })),
      {
        name: 'monitoring-store',
        partialize: () => ({})
      }
    )
  )
) 