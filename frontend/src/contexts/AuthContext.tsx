'use client'

import React, { createContext, useContext, useState, useEffect } from 'react'

interface User {
  id: number
  username: string
  name: string
  theme_preference: string
  is_admin: boolean
  created_at: string
}

interface AuthContextType {
  user: User | null
  token: string | null
  login: (username: string, password: string) => Promise<boolean>
  logout: () => void
  register: (username: string, name: string, password: string, confirmPassword: string) => Promise<boolean>
  resetPassword: (username: string, newPassword: string, confirmPassword: string) => Promise<boolean>
  updateTheme: (theme: string) => Promise<boolean>
  isAuthenticated: boolean
  isLoading: boolean
  error: string | null
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export const useAuth = () => {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null)
  const [token, setToken] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

  useEffect(() => {
    // Check for stored token on app load
    const storedToken = localStorage.getItem('sasha_auth_token')
    if (storedToken) {
      setToken(storedToken)
      fetchUserInfo(storedToken)
    } else {
      setIsLoading(false)
    }
  }, [])

  const fetchUserInfo = async (authToken: string) => {
    try {
      const response = await fetch(`${API_BASE_URL}/auth/me`, {
        headers: {
          'Authorization': `Bearer ${authToken}`,
          'Content-Type': 'application/json'
        }
      })

      if (response.ok) {
        const userData = await response.json()
        setUser(userData)
      } else {
        // Token is invalid
        localStorage.removeItem('sasha_auth_token')
        setToken(null)
      }
    } catch (error) {
      console.error('Error fetching user info:', error)
      localStorage.removeItem('sasha_auth_token')
      setToken(null)
    } finally {
      setIsLoading(false)
    }
  }

  const login = async (username: string, password: string): Promise<boolean> => {
    setIsLoading(true)
    setError(null)

    try {
      const response = await fetch(`${API_BASE_URL}/auth/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ username, password })
      })

      if (response.ok) {
        const data = await response.json()
        const authToken = data.access_token
        
        setToken(authToken)
        localStorage.setItem('sasha_auth_token', authToken)
        
        await fetchUserInfo(authToken)
        return true
      } else {
        const errorData = await response.json()
        setError(errorData.detail || 'Login failed')
        return false
      }
    } catch (error) {
      setError('Network error. Please try again.')
      return false
    } finally {
      setIsLoading(false)
    }
  }

  const register = async (username: string, name: string, password: string, confirmPassword: string): Promise<boolean> => {
    setIsLoading(true)
    setError(null)

    try {
      const response = await fetch(`${API_BASE_URL}/auth/register`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          username,
          name,
          password,
          confirm_password: confirmPassword
        })
      })

      if (response.ok) {
        // Auto-login after successful registration
        return await login(username, password)
      } else {
        const errorData = await response.json()
        setError(errorData.detail || 'Registration failed')
        return false
      }
    } catch (error) {
      setError('Network error. Please try again.')
      return false
    } finally {
      setIsLoading(false)
    }
  }

  const resetPassword = async (username: string, newPassword: string, confirmPassword: string): Promise<boolean> => {
    setIsLoading(true)
    setError(null)

    try {
      const response = await fetch(`${API_BASE_URL}/auth/reset-password`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          username,
          new_password: newPassword,
          confirm_password: confirmPassword
        })
      })

      if (response.ok) {
        return true
      } else {
        const errorData = await response.json()
        setError(errorData.detail || 'Password reset failed')
        return false
      }
    } catch (error) {
      setError('Network error. Please try again.')
      return false
    } finally {
      setIsLoading(false)
    }
  }

  const updateTheme = async (theme: string): Promise<boolean> => {
    if (!token) return false
    
    try {
      const response = await fetch(`${API_BASE_URL}/auth/update-theme`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ theme })
      })

      if (response.ok) {
        // Update user in state
        if (user) {
          setUser({ ...user, theme_preference: theme })
        }
        return true
      }
      return false
    } catch (error) {
      console.error('Error updating theme:', error)
      return false
    }
  }

  const logout = () => {
    setUser(null)
    setToken(null)
    // Clear all storage
    localStorage.clear()
    sessionStorage.clear()
  }

  const value: AuthContextType = {
    user,
    token,
    login,
    logout,
    register,
    resetPassword,
    updateTheme,
    isAuthenticated: !!user,
    isLoading,
    error
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}
