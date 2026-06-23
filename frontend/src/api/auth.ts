import api from './client'
import type { User } from '../types'

export interface AuthCredentials {
  username: string
  password: string
}

export async function register(credentials: AuthCredentials): Promise<User> {
  const { data } = await api.post('/auth/register', credentials)
  return data
}

export async function login(credentials: AuthCredentials): Promise<User> {
  const { data } = await api.post('/auth/login', credentials)
  return data
}

export async function logout(): Promise<void> {
  await api.post('/auth/logout')
}

export async function getCurrentUser(): Promise<User> {
  const { data } = await api.get('/auth/me')
  return data
}
