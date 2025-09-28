'use client'

import { useState, useEffect, useRef } from 'react'
import { Chat, Message } from '../types/chat'
import { db } from '../lib/database'
import { useTheme } from './ThemeProvider'
import Sidebar from './Sidebar'
import ChatMessage from './ChatMessage'
import Toast from './Toast'
import { generateChatTitle } from '../lib/titleGenerator'
import { API_ENDPOINTS, getAuthHeaders } from '../config/api'
import { useAuth } from '../contexts/AuthContext'
import UserProfileDropdown from './UserProfileDropdown'

export default function ChatInterface() {
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false)
  const [sidebarOpen, setSidebarOpen] = useState(false) // For mobile overlay
  const [currentChat, setCurrentChat] = useState<Chat | null>(null)
  const [messages, setMessages] = useState<Message[]>([])
  const [inputValue, setInputValue] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)
  const { theme, setTheme } = useTheme()
  const { isAuthenticated, logout, user, updateTheme } = useAuth()
  const [toast, setToast] = useState<{ message: string; type: 'info' | 'success' | 'warning' | 'error' } | null>(null)
  const [isInitializing, setIsInitializing] = useState(true)

  useEffect(() => {
    // Auto-create first chat if none exists
    initializeChat()
    
    // Clean up expired archives and notify user
    const cleanedCount = db.cleanupExpiredArchives()
    if (cleanedCount > 0) {
      setToast({
        message: `${cleanedCount} archived chat${cleanedCount > 1 ? 's' : ''} automatically deleted after 24 hours`,
        type: 'info'
      })
    }
  }, [])

  // Sync theme with user preference
  useEffect(() => {
    if (user && user.theme_preference !== theme) {
      setTheme(user.theme_preference as 'light' | 'dark')
    }
  }, [user, theme, setTheme])

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  useEffect(() => {
    // Set initial sidebar state based on screen size
    const handleResize = () => {
      if (window.innerWidth < 1024) { // Mobile
        setSidebarOpen(false) // Closed by default on mobile
      }
    }

    // Set initial state
    handleResize()
    
    // Listen for window resize
    window.addEventListener('resize', handleResize)
    return () => window.removeEventListener('resize', handleResize)
  }, [])

  const initializeChat = async () => {
    try {
      const chats = await db.getChats()
      
      if (chats.length === 0) {
        const newChat = await db.createChat('New Chat')
        setCurrentChat(newChat)
        setMessages([])
        db.setCurrentChatId(newChat.id)
      } else {
        // Try to restore the last active chat
        const lastChatId = db.getCurrentChatId()
        let chatToLoad = null
        
        if (lastChatId) {
          chatToLoad = await db.getChat(lastChatId)
        }
        
        // If last chat doesn't exist, use the most recent one
        if (!chatToLoad) {
          chatToLoad = await db.getChat(chats[0].id)
        }
        
        if (chatToLoad) {
          setCurrentChat(chatToLoad)
          setMessages(chatToLoad.messages)
          db.setCurrentChatId(chatToLoad.id)
        }
      }
    } catch (error) {
      console.error('Error initializing chat:', error)
      setToast({
        message: 'Error loading chat history. Starting fresh.',
        type: 'warning'
      })
    } finally {
      setIsInitializing(false)
    }
  }

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  const showToast = (message: string, type: 'info' | 'success' | 'warning' | 'error' = 'info') => {
    setToast({ message, type })
  }

  const handleChatSelect = async (chatId: string) => {
    const chat = await db.getChat(chatId)
    if (chat) {
      setCurrentChat(chat)
      setMessages(chat.messages)
      db.setCurrentChatId(chatId) // Remember the selected chat
    }
    setSidebarOpen(false)
  }

  const handleNewChat = async () => {
    const newChat = await db.createChat('New Chat')
    setCurrentChat(newChat)
    setMessages([])
    db.setCurrentChatId(newChat.id) // Remember the new chat
    setSidebarOpen(false)
    // Focus input after creating new chat
    setTimeout(() => inputRef.current?.focus(), 100)
  }

  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!inputValue.trim() || !currentChat || isLoading) return

    const messageText = inputValue.trim()
    const isFirstMessage = messages.length === 0
    setInputValue('')
    setIsLoading(true)

    // Immediately restore focus after clearing input
    setTimeout(() => inputRef.current?.focus(), 0)

    try {
      // Add user message to database and update state
      const userMessage = await db.addMessage(currentChat.id, messageText, 'user')
      setMessages(prev => [...prev, userMessage])

      // Call the bot API
      const response = await fetch(API_ENDPOINTS.CHAT, {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify({
          message: messageText,
          chat_id: currentChat.id
        })
      })

      if (!response.ok) {
        if (response.status === 401) {
          // Authentication failed, logout user
          logout()
          setToast({
            message: 'Your session has expired. Please log in again.',
            type: 'warning'
          })
          return
        }
        throw new Error('Failed to get bot response')
      }

      const data = await response.json()
      const aiMessage = await db.addMessage(currentChat.id, data.response, 'sasha')
      setMessages(prev => [...prev, aiMessage])

      // Announce AI response to screen readers
      announceMessage(data.response, 'sasha')

      // Auto-generate title after first AI response
      if (isFirstMessage && currentChat.title === 'New Chat') {
        const newTitle = generateChatTitle(messageText)
        const success = await db.updateChatTitle(currentChat.id, newTitle)
        if (success) {
          setCurrentChat(prev => prev ? { ...prev, title: newTitle } : null)
        }
      }
    } catch (error) {
      console.error('Error calling bot API:', error)
      // Fallback to a default response if API fails
      const fallbackMessage = await db.addMessage(
        currentChat.id, 
        "Sorry, I'm having trouble connecting right now. Please try again later.", 
        'sasha'
      )
      setMessages(prev => [...prev, fallbackMessage])

      // Still generate title even with fallback response
      if (isFirstMessage && currentChat.title === 'New Chat') {
        const newTitle = generateChatTitle(messageText)
        const success = await db.updateChatTitle(currentChat.id, newTitle)
        if (success) {
          setCurrentChat(prev => prev ? { ...prev, title: newTitle } : null)
        }
      }
    } finally {
      setIsLoading(false)
      // Ensure focus is maintained after loading completes
      setTimeout(() => inputRef.current?.focus(), 50)
    }
  }

  // Handle keyboard navigation
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Escape') {
      setSidebarOpen(false)
    }
  }

  // Announce new messages to screen readers
  const announceMessage = (message: string, sender: string) => {
    const announcement = `${sender === 'user' ? 'You said' : 'Sasha replied'}: ${message}`
    const ariaLive = document.getElementById('aria-live-region')
    if (ariaLive) {
      ariaLive.textContent = announcement
      // Clear after announcement
      setTimeout(() => {
        ariaLive.textContent = ''
      }, 1000)
    }
  }

  return (
    <div className="flex h-screen bg-white dark:bg-gray-900" onKeyDown={handleKeyDown}>
      {/* Skip Link for Keyboard Navigation */}
      <a
        href="#message-input"
        className="sr-only focus:not-sr-only focus:absolute focus:top-4 focus:left-4 focus:z-50 focus:px-4 focus:py-2 focus:bg-blue-600 focus:text-white focus:rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-300"
      >
        Skip to message input
      </a>
      
      {/* Screen Reader Announcements */}
      <div
        id="aria-live-region"
        aria-live="polite"
        aria-atomic="true"
        className="sr-only"
      />
      {/* Sidebar */}
      <Sidebar
        isOpen={sidebarOpen}
        isCollapsed={sidebarCollapsed}
        onToggle={() => setSidebarOpen(!sidebarOpen)}
        onCollapse={() => setSidebarCollapsed(!sidebarCollapsed)}
        currentChatId={currentChat?.id || null}
        onChatSelect={handleChatSelect}
        onNewChat={handleNewChat}
      />

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col">
        {/* Header */}
        <header className="flex items-center justify-between p-4 border-b border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900">
          <div className="flex items-center gap-3">
            <button
              onClick={() => setSidebarOpen(!sidebarOpen)}
              className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 lg:hidden focus:outline-none focus:ring-2 focus:ring-blue-500"
              aria-label="Toggle sidebar"
              aria-expanded={sidebarOpen}
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
              </svg>
            </button>
            
            <h1 className="text-lg font-semibold text-gray-900 dark:text-white truncate">
              {currentChat?.title || 'New Chat'}
            </h1>
          </div>
          
          {/* User Profile and Theme Toggle */}
          <div className="flex items-center gap-2">
            {/* Theme Toggle */}
            <button
              onClick={async () => {
                const newTheme = theme === 'dark' ? 'light' : 'dark'
                setTheme(newTheme)
                if (user) {
                  await updateTheme(newTheme)
                }
              }}
              className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 focus:outline-none focus:ring-2 focus:ring-blue-500"
              aria-label={`Switch to ${theme === 'dark' ? 'light' : 'dark'} mode`}
            >
              {theme === 'dark' ? (
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z" />
                </svg>
              ) : (
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z" />
                </svg>
              )}
            </button>
            
            {/* User Profile Dropdown */}
            <UserProfileDropdown />
          </div>
        </header>

        {/* Messages Area */}
        <main 
          className="flex-1 overflow-y-auto"
          role="main"
          aria-label="Chat conversation"
        >
          {isInitializing ? (
            <div className="flex items-center justify-center h-full">
              <div className="text-center">
                <div className="w-8 h-8 border-4 border-blue-600 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
                <p className="text-gray-600 dark:text-gray-400">
                  Loading your chat history...
                </p>
              </div>
            </div>
          ) : messages.length === 0 ? (
            <div className="flex items-center justify-center h-full">
              <div className="text-center">
                <h2 className="text-xl font-medium text-gray-900 dark:text-white mb-2">
                  Welcome to Sasha AI
                </h2>
                <p className="text-gray-600 dark:text-gray-400">
                  Start a conversation by typing a message below
                </p>
              </div>
            </div>
          ) : (
            <div className="pb-4" role="log" aria-live="polite" aria-label="Chat messages">
              {messages.map((message, index) => (
                <ChatMessage 
                  key={message.id} 
                  message={message}
                  aria-posinset={index + 1}
                  aria-setsize={messages.length}
                />
              ))}
              {isLoading && (
                <div className="flex gap-3 p-4" role="status" aria-label="Sasha is typing">
                  <div className="w-8 h-8 rounded-full bg-purple-600 flex items-center justify-center text-sm font-medium text-white">
                    S
                  </div>
                  <div className="bg-gray-200 dark:bg-gray-700 rounded-lg px-4 py-2">
                    <div className="flex space-x-1">
                      <div className="w-2 h-2 bg-gray-500 rounded-full animate-bounce"></div>
                      <div className="w-2 h-2 bg-gray-500 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                      <div className="w-2 h-2 bg-gray-500 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                    </div>
                    <span className="sr-only">Sasha is typing a response</span>
                  </div>
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>
          )}
        </main>

        {/* Input Area */}
        <div className="border-t border-gray-200 dark:border-gray-700 p-4 bg-white dark:bg-gray-900">
          <form onSubmit={handleSendMessage} className="flex gap-3" role="form" aria-label="Send message">
            <label htmlFor="message-input" className="sr-only">
              Type your message to Sasha AI
            </label>
            <input
              id="message-input"
              ref={inputRef}
              type="text"
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              placeholder="Type your message..."
              autoFocus
              aria-describedby="send-button"
              aria-invalid={false}
              className="flex-1 px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
            />
            <button
              id="send-button"
              type="submit"
              disabled={!inputValue.trim() || isLoading}
              aria-label={isLoading ? "Sending message..." : "Send message"}
              className="px-6 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white rounded-lg transition-colors disabled:cursor-not-allowed focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              {isLoading ? (
                <>
                  <span className="sr-only">Sending...</span>
                  <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24" aria-hidden="true">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                </>
              ) : (
                'Send'
              )}
            </button>
          </form>
        </div>
      </div>

      {/* Toast Notifications */}
      {toast && (
        <Toast
          message={toast.message}
          type={toast.type}
          onClose={() => setToast(null)}
        />
      )}
    </div>
  )
}
