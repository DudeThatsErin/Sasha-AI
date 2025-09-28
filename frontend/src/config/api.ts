// API Configuration for different environments

const getApiBaseUrl = (): string => {
  // Check if we're in development (localhost)
  if (typeof window !== 'undefined' && window.location.hostname === 'localhost') {
    return 'http://localhost:8000'
  }
  
  // For production deployment with Cloudflare Tunnel
  return process.env.NEXT_PUBLIC_API_URL || 'https://api.erinskidds.com'
}

export const API_BASE_URL = getApiBaseUrl()

export const API_ENDPOINTS = {
  CHAT: `${API_BASE_URL}/chat`,
  HEALTH: `${API_BASE_URL}/health`,
  STATUS: `${API_BASE_URL}/model/status`
}

// Helper function to get auth headers
export const getAuthHeaders = (): Record<string, string> => {
  const token = typeof window !== 'undefined' ? localStorage.getItem('sasha_auth_token') : null
  return {
    'Content-Type': 'application/json',
    ...(token && { 'Authorization': `Bearer ${token}` })
  }
}
