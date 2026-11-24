import axios from 'axios'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || '/api',
})

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

api.interceptors.response.use(
  response => response,
  async error => {
    const original = error.config
    if (error.response?.status === 401 && original && !original._retry) {
      original._retry = true
      const refresh = localStorage.getItem('refresh')
      if (refresh) {
        try {
          const response = await axios.post(
            `${import.meta.env.VITE_API_URL || '/api'}/auth/refresh/`,
            { refresh },
          )
          localStorage.setItem('access', response.data.access)
          original.headers.Authorization = `Bearer ${response.data.access}`
          return api(original)
        } catch {
          localStorage.clear()
          window.location.assign('/login')
        }
      }
    }
    return Promise.reject(error)
  },
)

export default api
