'use client'

import { useState, useEffect } from 'react'
import { Chat } from '../types/chat'
import { db, ArchivedChat } from '../lib/database'

interface SidebarProps {
  isOpen: boolean
  isCollapsed: boolean
  onToggle: () => void
  onCollapse: () => void
  currentChatId: string | null
  onChatSelect: (chatId: string) => void
  onNewChat: () => void
}

export default function Sidebar({ 
  isOpen, 
  isCollapsed,
  onToggle, 
  onCollapse,
  currentChatId, 
  onChatSelect, 
  onNewChat 
}: SidebarProps) {
  const [chats, setChats] = useState<Chat[]>([])
  const [showArchived, setShowArchived] = useState(false)
  const [archivedChats, setArchivedChats] = useState<ArchivedChat[]>([])
  const [archivedCount, setArchivedCount] = useState(0)

  useEffect(() => {
    loadChats()
    loadArchivedChats()
    
    // Clean up expired archives on load
    const cleanedCount = db.cleanupExpiredArchives()
    if (cleanedCount > 0) {
      console.log(`Cleaned up ${cleanedCount} expired archived chats`)
      loadArchivedChats() // Reload after cleanup
    }
  }, [])

  const loadChats = async () => {
    const chatList = await db.getChats()
    setChats(chatList)
  }

  const loadArchivedChats = () => {
    const archived = db.getArchivedChats()
    setArchivedChats(archived)
    setArchivedCount(archived.length)
  }

  const handleNewChat = async () => {
    const newChat = await db.createChat('New Chat')
    setChats(prev => [newChat, ...prev])
    onNewChat()
    onChatSelect(newChat.id)
  }

  const handleArchiveChat = async (chatId: string, e: React.MouseEvent) => {
    e.stopPropagation()
    const success = await db.archiveChat(chatId)
    if (success) {
      loadChats()
      loadArchivedChats()
      // If the archived chat was currently selected, clear selection
      if (currentChatId === chatId) {
        onChatSelect('')
      }
    }
  }

  const handleRestoreChat = async (chatId: string, e: React.MouseEvent) => {
    e.stopPropagation()
    const success = await db.restoreFromArchive(chatId)
    if (success) {
      loadChats()
      loadArchivedChats()
      onChatSelect(chatId)
    }
  }

  const formatDate = (date: Date) => {
    const now = new Date()
    const diff = now.getTime() - date.getTime()
    const days = Math.floor(diff / (1000 * 60 * 60 * 24))
    
    if (days === 0) return 'Today'
    if (days === 1) return 'Yesterday'
    if (days < 7) return `${days} days ago`
    return date.toLocaleDateString()
  }

  const formatTimeRemaining = (archivedAt: Date) => {
    const now = new Date()
    const expiryTime = new Date(archivedAt.getTime() + (24 * 60 * 60 * 1000))
    const remaining = expiryTime.getTime() - now.getTime()
    
    if (remaining <= 0) return 'Expired'
    
    const hours = Math.floor(remaining / (1000 * 60 * 60))
    const minutes = Math.floor((remaining % (1000 * 60 * 60)) / (1000 * 60))
    
    if (hours > 0) return `${hours}h ${minutes}m left`
    return `${minutes}m left`
  }

  return (
    <>
      {/* Mobile overlay */}
      {isOpen && (
        <div 
          className="fixed inset-0 bg-black bg-opacity-50 z-40 lg:hidden"
          onClick={onToggle}
        />
      )}
      
      {/* Sidebar */}
      <div className={`
        fixed top-0 left-0 h-full bg-gray-50 dark:bg-gray-900 border-r border-gray-200 dark:border-gray-700 z-50
        transform transition-all duration-300 ease-in-out
        ${isOpen ? 'translate-x-0' : '-translate-x-full'}
        ${isCollapsed ? 'w-16' : 'w-80 lg:w-64'}
        lg:relative lg:translate-x-0
      `}>
        {/* Header */}
        <div className="flex items-center justify-between px-4 py-4 border-b border-gray-200 dark:border-gray-700 h-[73px]">
          {!isCollapsed && (
            <h1 className="text-xl font-semibold text-gray-900 dark:text-white">
              Sasha AI
            </h1>
          )}
          {isCollapsed && (
            <div className="w-8 h-8 bg-purple-600 rounded-full flex items-center justify-center mx-auto">
              <span className="text-sm font-bold text-white">S</span>
            </div>
          )}
          <button
            onClick={onToggle}
            className="p-2 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-800 lg:hidden"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* New Chat Button */}
        <div className="p-4">
          <button
            onClick={handleNewChat}
            className={`w-full flex items-center ${isCollapsed ? 'justify-center px-2 py-3' : 'gap-3 px-4 py-3'} rounded-lg bg-blue-600 hover:bg-blue-700 text-white transition-colors`}
            title={isCollapsed ? "New Chat" : ""}
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
            </svg>
            {!isCollapsed && <span>New Chat</span>}
          </button>
        </div>

        {/* Active Chats Section */}
        <div className="flex-1 overflow-y-auto">
          {/* Active Chats Header */}
          {!isCollapsed && (
            <div className="px-4 py-2">
              <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wide">
                Active Chats
              </h3>
            </div>
          )}
          
          {/* Active Chat List */}
          <div className="px-4 pb-4">
            <div className="space-y-2">
              {chats.map((chat) => (
                <div key={chat.id} className="group relative">
                  <button
                    onClick={() => onChatSelect(chat.id)}
                    className={`
                      w-full text-left rounded-lg transition-colors
                      ${isCollapsed ? 'p-2 flex justify-center' : 'p-3'}
                      ${currentChatId === chat.id 
                        ? 'bg-blue-100 dark:bg-blue-900 text-blue-900 dark:text-blue-100' 
                        : 'hover:bg-gray-200 dark:hover:bg-gray-800 text-gray-700 dark:text-gray-300'
                      }
                    `}
                    title={isCollapsed ? chat.title : ""}
                  >
                    {isCollapsed ? (
                      <div className="w-6 h-6 bg-gray-400 dark:bg-gray-600 rounded-full flex items-center justify-center">
                        <span className="text-xs text-white">{chat.title.charAt(0).toUpperCase()}</span>
                      </div>
                    ) : (
                      <>
                        <div className="font-medium truncate pr-8">{chat.title}</div>
                        <div className="text-sm text-gray-500 dark:text-gray-400">
                          {formatDate(chat.updatedAt)}
                        </div>
                      </>
                    )}
                  </button>
                  {!isCollapsed && (
                    <button
                      onClick={(e) => handleArchiveChat(chat.id, e)}
                      className="absolute right-2 top-1/2 transform -translate-y-1/2 p-1 rounded opacity-0 group-hover:opacity-100 hover:bg-gray-300 dark:hover:bg-gray-600 transition-opacity"
                      title="Archive chat"
                    >
                      <span className="text-sm">🗑️</span>
                    </button>
                  )}
                </div>
              ))}
            </div>
          </div>

          {/* Archived Chats Dropdown */}
          {!isCollapsed && archivedCount > 0 && (
            <div className="pb-4 border-t border-gray-200 dark:border-gray-700 pt-4">
              <button
                onClick={() => setShowArchived(!showArchived)}
                className="w-full flex items-center justify-between px-3 py-2 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-800 text-gray-700 dark:text-gray-300 transition-colors"
              >
                <span className="text-sm font-medium flex items-center">
                  Archived Chats
                  <span className="ml-2 px-2 py-1 text-xs bg-gray-300 dark:bg-gray-600 rounded-full">
                    {archivedCount}
                  </span>
                </span>
                <svg className={`w-4 h-4 transition-transform ${showArchived ? 'rotate-180' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                </svg>
              </button>
              
              {/* Archived Chat List */}
              {showArchived && (
                <div className="mt-2 space-y-2 pl-4">
                  {archivedChats.map((chat) => (
                    <div key={chat.id} className="group relative">
                      <button
                        onClick={() => onChatSelect(chat.id)}
                        className="w-full text-left p-3 rounded-lg transition-colors hover:bg-gray-200 dark:hover:bg-gray-800 text-gray-700 dark:text-gray-300"
                      >
                        <div className="font-medium truncate pr-8">{chat.title}</div>
                        <div className="text-sm text-gray-500 dark:text-gray-400">
                          Archived {formatDate(chat.archivedAt)} • {formatTimeRemaining(chat.archivedAt)}
                        </div>
                      </button>
                      <button
                        onClick={(e) => handleRestoreChat(chat.id, e)}
                        className="absolute right-2 top-1/2 transform -translate-y-1/2 p-1 rounded opacity-0 group-hover:opacity-100 hover:bg-gray-300 dark:hover:bg-gray-600 transition-opacity"
                        title="Restore chat"
                      >
                        <span className="text-sm">♻️</span>
                      </button>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>

        {/* Collapse/Expand button for desktop */}
        <div className="hidden lg:block p-4 border-t border-gray-200 dark:border-gray-700">
          <button
            onClick={onCollapse}
            className={`w-full flex items-center rounded-lg hover:bg-gray-200 dark:hover:bg-gray-800 text-gray-700 dark:text-gray-300 transition-colors ${isCollapsed ? 'justify-center px-2 py-2' : 'gap-3 px-4 py-2'}`}
            title={isCollapsed ? (isCollapsed ? "Expand" : "Collapse") : ""}
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d={isCollapsed ? "M13 5l7 7-7 7M5 5l7 7-7 7" : "M11 19l-7-7 7-7m8 14l-7-7 7-7"} />
            </svg>
            {!isCollapsed && <span>{isCollapsed ? "Expand" : "Collapse"}</span>}
          </button>
        </div>
      </div>
    </>
  )
}
