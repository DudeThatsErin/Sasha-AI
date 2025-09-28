'use client'

import { useRouter, useSearchParams } from 'next/navigation'
import { useEffect } from 'react'
import ChatInterface from '../components/ChatInterface'
import { ThemeProvider } from '../components/ThemeProvider'
import { AuthProvider } from '../contexts/AuthContext'
import ProtectedRoute from '../components/ProtectedRoute'
import LoginPage from '../components/auth/LoginPage'
import RegisterPage from '../components/auth/RegisterPage'
import ForgotPasswordPage from '../components/auth/ForgotPasswordPage'

export default function Home() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const page = searchParams.get('page')

  // Handle routing based on page parameter
  const renderPage = () => {
    switch (page) {
      case 'register':
        return <RegisterPage />
      case 'forgot-password':
        return <ForgotPasswordPage />
      case 'login':
        return <LoginPage />
      default:
        return (
          <ProtectedRoute>
            <ChatInterface />
          </ProtectedRoute>
        )
    }
  }

  return (
    <ThemeProvider>
      <AuthProvider>
        {renderPage()}
      </AuthProvider>
    </ThemeProvider>
  )
}
