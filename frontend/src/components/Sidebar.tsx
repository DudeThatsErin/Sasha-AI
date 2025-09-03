'use client'

import { useState, useEffect } from 'react'
import { Chat } from '../types/chat'
import { db } from '../lib/database'

interface SidebarProps {
  isOpen: boolean
  onToggle: () => void
  currentChatId: string | null
  onChatSelect: (chatId: string) => void
  onNewChat: () => void
}

export default function Sidebar({ 
  isOpen, 
  onToggle, 
  currentChatId, 
  onChatSelect, 
  onNewChat 
}: SidebarProps) {
  const [chats, setChats] = useState<Chat[]>([])

  useEffect(() => {
    loadChats()
  }, [])

  const loadChats = async () => {
    const chatList = await db.getChats()
    setChats(chatList)
  }

  const handleNewChat = async () => {
    const newChat = await db.createChat('New Chat')
    setChats(prev => [newChat, ...prev])
    onNewChat()
    onChatSelect(newChat.id)
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
        transform transition-transform duration-300 ease-in-out
        ${isOpen ? 'translate-x-0' : '-translate-x-full'}
        w-80 lg:w-64
        lg:relative lg:translate-x-0
      `}>
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-gray-200 dark:border-gray-700">
          <h1 className="text-xl font-semibold text-gray-900 dark:text-white">
            Sasha AI
          </h1>
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
            className="w-full flex items-center gap-3 px-4 py-3 rounded-lg bg-blue-600 hover:bg-blue-700 text-white transition-colors"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
            </svg>
            New Chat
          </button>
        </div>

        {/* Chat List */}
        <div className="flex-1 overflow-y-auto px-4 pb-4">
          <div className="space-y-2">
            {chats.map((chat) => (
              <button
                key={chat.id}
                onClick={() => onChatSelect(chat.id)}
                className={`
                  w-full text-left p-3 rounded-lg transition-colors
                  ${currentChatId === chat.id 
                    ? 'bg-blue-100 dark:bg-blue-900 text-blue-900 dark:text-blue-100' 
                    : 'hover:bg-gray-200 dark:hover:bg-gray-800 text-gray-700 dark:text-gray-300'
                  }
                `}
              >
                <div className="font-medium truncate">{chat.title}</div>
                <div className="text-sm text-gray-500 dark:text-gray-400">
                  {formatDate(chat.updatedAt)}
                </div>
              </button>
            ))}
          </div>
        </div>

        {/* Collapse button for desktop */}
        <div className="hidden lg:block p-4 border-t border-gray-200 dark:border-gray-700">
          <button
            onClick={onToggle}
            className="w-full flex items-center gap-3 px-4 py-2 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-800 text-gray-700 dark:text-gray-300"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 19l-7-7 7-7m8 14l-7-7 7-7" />
            </svg>
            Collapse
          </button>
        </div>
      </div>
    </>
  )
}
