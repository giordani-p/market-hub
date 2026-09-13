import { useCallback, useEffect, useMemo, useState, type ReactNode } from 'react'
import { fetchCurrentUser, login as loginRequest } from '../../features/auth/api'
import { setUnauthorizedHandler } from '../../lib/api/client'
import { clearToken, getToken, setToken } from '../../lib/auth/storage'
import type { AuthUser } from '../../types/auth'
import { AuthContext, type AuthStatus } from './auth-context'

export function AuthProvider({ children }: { children: ReactNode }) {
  const [status, setStatus] = useState<AuthStatus>('checking')
  const [user, setUser] = useState<AuthUser | null>(null)

  const logout = useCallback(() => {
    clearToken()
    setUser(null)
    setStatus('unauthenticated')
  }, [])

  useEffect(() => {
    setUnauthorizedHandler(logout)
  }, [logout])

  useEffect(() => {
    const token = getToken()
    if (!token) {
      setStatus('unauthenticated')
      return
    }
    fetchCurrentUser()
      .then((currentUser) => {
        setUser(currentUser)
        setStatus('authenticated')
      })
      .catch(() => {
        clearToken()
        setStatus('unauthenticated')
      })
  }, [])

  const login = useCallback(async (email: string, password: string) => {
    const token = await loginRequest({ email, password })
    setToken(token.access_token)
    const currentUser = await fetchCurrentUser()
    setUser(currentUser)
    setStatus('authenticated')
  }, [])

  const value = useMemo(() => ({ status, user, login, logout }), [status, user, login, logout])

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}
