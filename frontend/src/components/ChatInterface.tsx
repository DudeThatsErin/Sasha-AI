'use client'

import { useState, useEffect, useRef } from 'react'
import { Chat, Message } from '../types/chat'
import { db } from '../lib/database'
import { useTheme } from './ThemeProvider'
import Sidebar from './Sidebar'
import ChatMessage from './ChatMessage'
import Toast from './Toast'
import { generateChatTitle } from '../lib/titleGenerator'
import { API_ENDPOINTS } from '../config/api'

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
  const [toast, setToast] = useState<{ message: string; type: 'info' | 'success' | 'warning' | 'error' } | null>(null)

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
    const chats = await db.getChats()
    if (chats.length === 0) {
      const newChat = await db.createChat('New Chat')
      setCurrentChat(newChat)
      setMessages([])
    } else {
      const chat = await db.getChat(chats[0].id)
      if (chat) {
        setCurrentChat(chat)
        setMessages(chat.messages)
      }
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
    }
    setSidebarOpen(false)
  }

  const handleNewChat = async () => {
    const newChat = await db.createChat('New Chat')
    setCurrentChat(newChat)
    setMessages([])
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
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: messageText,
          chat_id: currentChat.id
        })
      })

      if (!response.ok) {
        throw new Error('Failed to get bot response')
      }

      const data = await response.json()
      const aiMessage = await db.addMessage(currentChat.id, data.response, 'sasha')
      setMessages(prev => [...prev, aiMessage])

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

  return (
    <div className="flex h-screen bg-white dark:bg-gray-900" onKeyDown={handleKeyDown}>
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
        <header className="flex items-center justify-between px-4 py-4 border-b border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 h-[73px]">
          <div className="flex items-center gap-3">
            {/* Mobile hamburger menu */}
            <button
              onClick={() => setSidebarOpen(!sidebarOpen)}
              className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 lg:hidden"
              aria-label="Toggle sidebar"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
              </svg>
            </button>
            
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white truncate">
              {currentChat?.title || 'New Chat'}
            </h2>
          </div>
          
          {/* Theme Toggle */}
          <button
            onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}
            className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800"
            aria-label="Toggle theme"
          >
            {theme === 'dark' ? (
              <svg className="w-5 h-5 text-yellow-500" fill="currentColor" viewBox="0 0 24 24">
                <path d="M12 2.25a.75.75 0 01.75.75v2.25a.75.75 0 01-1.5 0V3a.75.75 0 01.75-.75zM7.5 12a4.5 4.5 0 119 0 4.5 4.5 0 01-9 0zM18.894 6.166a.75.75 0 00-1.06-1.06l-1.591 1.59a.75.75 0 101.06 1.061l1.591-1.59zM21.75 12a.75.75 0 01-.75.75h-2.25a.75.75 0 010-1.5H21a.75.75 0 01.75.75zM17.834 18.894a.75.75 0 001.06-1.06l-1.59-1.591a.75.75 0 10-1.061 1.06l1.59 1.591zM12 18a.75.75 0 01.75.75V21a.75.75 0 01-1.5 0v-2.25A.75.75 0 0112 18zM7.758 17.303a.75.75 0 00-1.061-1.06l-1.591 1.59a.75.75 0 001.06 1.061l1.591-1.59zM6 12a.75.75 0 01-.75.75H3a.75.75 0 010-1.5h2.25A.75.75 0 016 12zM6.697 7.757a.75.75 0 001.06-1.06l-1.59-1.591a.75.75 0 00-1.061 1.06l1.59 1.591z" />
              </svg>
            ) : (
              <svg className="w-5 h-5 text-gray-700" fill="currentColor" viewBox="0 0 24 24">
                <path d="M9.528 1.718a.75.75 0 01.162.819A8.97 8.97 0 009 6a9 9 0 009 9 8.97 8.97 0 003.463-.69.75.75 0 01.981.98 10.503 10.503 0 01-9.694 6.46c-5.799 0-10.5-4.701-10.5-10.5 0-4.368 2.667-8.112 6.46-9.694a.75.75 0 01.818.162z" />
              </svg>
            )}
          </button>
        </header>

        {/* Messages Area */}
        <div className="flex-1 overflow-y-auto">
          {messages.length === 0 ? (
            <div className="flex items-center justify-center h-full">
              <div className="text-center">
                <div className="w-16 h-16 bg-purple-600 rounded-full flex items-center justify-center mx-auto mb-4">
                  <span className="text-2xl font-bold text-white">S</span>
                </div>
                <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">
                  Welcome to Sasha AI
                </h3>
                <p className="text-gray-600 dark:text-gray-400">
                  Start a conversation by typing a message below
                </p>
              </div>
            </div>
          ) : (
            <div className="pb-4">
              {messages.map((message) => (
                <ChatMessage key={message.id} message={message} />
              ))}
              {isLoading && (
                <div className="flex gap-3 p-4">
                  <div className="w-8 h-8 rounded-full bg-purple-600 flex items-center justify-center text-sm font-medium text-white">
                    S
                  </div>
                  <div className="bg-gray-200 dark:bg-gray-700 rounded-lg px-4 py-2">
                    <div className="flex space-x-1">
                      <div className="w-2 h-2 bg-gray-500 rounded-full animate-bounce"></div>
                      <div className="w-2 h-2 bg-gray-500 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                      <div className="w-2 h-2 bg-gray-500 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                    </div>
                  </div>
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>
          )}
        </div>

        {/* Input Area */}
        <div className="border-t border-gray-200 dark:border-gray-700 p-4 bg-white dark:bg-gray-900">
          <form onSubmit={handleSendMessage} className="flex gap-3">
            <input
              ref={inputRef}
              type="text"
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              placeholder="Type your message..."
              autoFocus
              className="flex-1 px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
            />
            <button
              type="submit"
              disabled={!inputValue.trim() || isLoading}
              className="px-6 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white rounded-lg transition-colors disabled:cursor-not-allowed"
            >
              Send
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
