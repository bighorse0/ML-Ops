import { create } from 'zustand'
import { devtools, persist } from 'zustand/middleware'
import { immer } from 'zustand/middleware/immer'

export interface Feature {
  id: number
  name: string
  description: string
  data_type: string
  feature_type: string
  entity_type: string
  serving_mode: string
  storage_type: string
  tags: string[]
  metadata: Record<string, any>
  status: string
  created_at: string
  updated_at: string
  created_by: number
  organization_id: number
}

export interface FeatureValue {
  id: number
  feature_id: number
  entity_id: string
  value: any
  timestamp: string
  metadata: Record<string, any>
  created_at: string
  updated_at: string
  created_by: number
  organization_id: number
}

export interface FeatureFilters {
  name?: string
  data_type?: string
  feature_type?: string
  entity_type?: string
  serving_mode?: string
  status?: string
  tags?: string[]
}

export interface PaginationParams {
  page: number
  limit: number
}

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  size: number
  pages: number
}

interface FeatureState {
  // State
  features: Feature[]
  featureValues: FeatureValue[]
  selectedFeature: Feature | null
  loading: boolean
  error: string | null
  filters: FeatureFilters
  pagination: PaginationParams
  
  // Actions
  setFeatures: (features: Feature[]) => void
  setFeatureValues: (values: FeatureValue[]) => void
  setSelectedFeature: (feature: Feature | null) => void
  setLoading: (loading: boolean) => void
  setError: (error: string | null) => void
  setFilters: (filters: Partial<FeatureFilters>) => void
  setPagination: (pagination: Partial<PaginationParams>) => void
  
  // CRUD Operations
  addFeature: (feature: Omit<Feature, 'id' | 'created_at' | 'updated_at' | 'created_by' | 'organization_id'>) => Promise<void>
  updateFeature: (id: number, updates: Partial<Feature>) => Promise<void>
  deleteFeature: (id: number) => Promise<void>
  fetchFeatures: (params?: { filters?: FeatureFilters; pagination?: PaginationParams }) => Promise<void>
  fetchFeature: (id: number) => Promise<void>
  fetchFeatureValues: (featureId: number, params?: { entity_id?: string; start_timestamp?: string; end_timestamp?: string }) => Promise<void>
  
  // Utility
  clearError: () => void
  resetFilters: () => void
  resetPagination: () => void
}

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api'

export const useFeatureStore = create<FeatureState>()(
  devtools(
    persist(
      immer((set, get) => ({
        // Initial state
        features: [],
        featureValues: [],
        selectedFeature: null,
        loading: false,
        error: null,
        filters: {},
        pagination: { page: 1, limit: 50 },

        // Basic setters
        setFeatures: (features) => set((state) => { state.features = features }),
        setFeatureValues: (values) => set((state) => { state.featureValues = values }),
        setSelectedFeature: (feature) => set((state) => { state.selectedFeature = feature }),
        setLoading: (loading) => set((state) => { state.loading = loading }),
        setError: (error) => set((state) => { state.error = error }),
        setFilters: (filters) => set((state) => { state.filters = { ...state.filters, ...filters } }),
        setPagination: (pagination) => set((state) => { state.pagination = { ...state.pagination, ...pagination } }),

        // CRUD Operations
        addFeature: async (featureData) => {
          set((state) => { state.loading = true; state.error = null })
          
          try {
            const response = await fetch(`${API_BASE_URL}/features`, {
              method: 'POST',
              headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${localStorage.getItem('token')}`
              },
              body: JSON.stringify(featureData)
            })

            if (!response.ok) {
              throw new Error(`Failed to create feature: ${response.statusText}`)
            }

            const newFeature = await response.json()
            set((state) => {
              state.features.unshift(newFeature)
              state.loading = false
            })
          } catch (error) {
            set((state) => {
              state.error = error instanceof Error ? error.message : 'Failed to create feature'
              state.loading = false
            })
          }
        },

        updateFeature: async (id, updates) => {
          set((state) => { state.loading = true; state.error = null })
          
          try {
            const response = await fetch(`${API_BASE_URL}/features/${id}`, {
              method: 'PUT',
              headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${localStorage.getItem('token')}`
              },
              body: JSON.stringify(updates)
            })

            if (!response.ok) {
              throw new Error(`Failed to update feature: ${response.statusText}`)
            }

            const updatedFeature = await response.json()
            set((state) => {
              const index = state.features.findIndex((f: Feature) => f.id === id)
              if (index !== -1) {
                state.features[index] = updatedFeature
              }
              if (state.selectedFeature?.id === id) {
                state.selectedFeature = updatedFeature
              }
              state.loading = false
            })
          } catch (error) {
            set((state) => {
              state.error = error instanceof Error ? error.message : 'Failed to update feature'
              state.loading = false
            })
          }
        },

        deleteFeature: async (id) => {
          set((state) => { state.loading = true; state.error = null })
          
          try {
            const response = await fetch(`${API_BASE_URL}/features/${id}`, {
              method: 'DELETE',
              headers: {
                'Authorization': `Bearer ${localStorage.getItem('token')}`
              }
            })

            if (!response.ok) {
              throw new Error(`Failed to delete feature: ${response.statusText}`)
            }

            set((state) => {
              state.features = state.features.filter((f: Feature) => f.id !== id)
              if (state.selectedFeature?.id === id) {
                state.selectedFeature = null
              }
              state.loading = false
            })
          } catch (error) {
            set((state) => {
              state.error = error instanceof Error ? error.message : 'Failed to delete feature'
              state.loading = false
            })
          }
        },

        fetchFeatures: async (params = {}) => {
          set((state) => { state.loading = true; state.error = null })
          
          try {
            const { filters = get().filters, pagination = get().pagination } = params
            const queryParams = new URLSearchParams()
            
            // Add pagination params
            queryParams.append('page', pagination.page.toString())
            queryParams.append('limit', pagination.limit.toString())
            
            // Add filter params
            Object.entries(filters).forEach(([key, value]) => {
              if (value !== undefined && value !== null && value !== '') {
                if (Array.isArray(value)) {
                  value.forEach(v => queryParams.append(key, v))
                } else {
                  queryParams.append(key, value.toString())
                }
              }
            })

            const response = await fetch(`${API_BASE_URL}/features?${queryParams}`, {
              headers: {
                'Authorization': `Bearer ${localStorage.getItem('token')}`
              }
            })

            if (!response.ok) {
              throw new Error(`Failed to fetch features: ${response.statusText}`)
            }

            const data: PaginatedResponse<Feature> = await response.json()
            set((state) => {
              state.features = data.items
              state.pagination = { page: data.page, size: data.size }
              state.loading = false
            })
          } catch (error) {
            set((state) => {
              state.error = error instanceof Error ? error.message : 'Failed to fetch features'
              state.loading = false
            })
          }
        },

        fetchFeature: async (id) => {
          set((state) => { state.loading = true; state.error = null })
          
          try {
            const response = await fetch(`${API_BASE_URL}/features/${id}`, {
              headers: {
                'Authorization': `Bearer ${localStorage.getItem('token')}`
              }
            })

            if (!response.ok) {
              throw new Error(`Failed to fetch feature: ${response.statusText}`)
            }

            const feature = await response.json()
            set((state) => {
              state.selectedFeature = feature
              state.loading = false
            })
          } catch (error) {
            set((state) => {
              state.error = error instanceof Error ? error.message : 'Failed to fetch feature'
              state.loading = false
            })
          }
        },

        fetchFeatureValues: async (featureId, params = {}) => {
          set((state) => { state.loading = true; state.error = null })
          
          try {
            const queryParams = new URLSearchParams()
            queryParams.append('feature_id', featureId.toString())
            
            Object.entries(params).forEach(([key, value]) => {
              if (value !== undefined && value !== null && value !== '') {
                queryParams.append(key, value.toString())
              }
            })

            const response = await fetch(`${API_BASE_URL}/feature-values?${queryParams}`, {
              headers: {
                'Authorization': `Bearer ${localStorage.getItem('token')}`
              }
            })

            if (!response.ok) {
              throw new Error(`Failed to fetch feature values: ${response.statusText}`)
            }

            const data: PaginatedResponse<FeatureValue> = await response.json()
            set((state) => {
              state.featureValues = data.items
              state.loading = false
            })
          } catch (error) {
            set((state) => {
              state.error = error instanceof Error ? error.message : 'Failed to fetch feature values'
              state.loading = false
            })
          }
        },

        // Utility functions
        clearError: () => set((state) => { state.error = null }),
        resetFilters: () => set((state) => { state.filters = {} }),
        resetPagination: () => set((state) => { state.pagination = { page: 1, limit: 50 } })
      })),
      {
        name: 'feature-store',
        partialize: (state) => ({
          filters: state.filters,
          pagination: state.pagination
        })
      }
    )
  )
) 