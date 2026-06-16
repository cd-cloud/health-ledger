import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json',
  },
})

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (axios.isAxiosError(error) && error.response?.data?.detail) {
      return Promise.reject(new Error(error.response.data.detail))
    }
    return Promise.reject(error)
  }
)

export default api
