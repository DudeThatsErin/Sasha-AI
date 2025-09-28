import { Chat, Message } from '../types/chat'

export interface ArchivedChat extends Chat {
  archivedAt: Date
}

// Persistent storage using localStorage
class ChatDatabase {
  private chats: Map<string, Chat> = new Map()
  private messages: Map<string, Message[]> = new Map()
  private archivedChats: Map<string, ArchivedChat> = new Map()
  
  private readonly STORAGE_KEYS = {
    CHATS: 'sasha_chats',
    MESSAGES: 'sasha_messages',
    ARCHIVED: 'sasha_archived_chats'
  }

  constructor() {
    this.loadFromStorage()
  }

  private loadFromStorage(): void {
    if (typeof window === 'undefined') return

    try {
      // Load chats
      const chatsData = localStorage.getItem(this.STORAGE_KEYS.CHATS)
      if (chatsData) {
        const chatsArray = JSON.parse(chatsData) as Chat[]
        chatsArray.forEach(chat => {
          this.chats.set(chat.id, {
            ...chat,
            createdAt: new Date(chat.createdAt),
            updatedAt: new Date(chat.updatedAt)
          })
        })
      }

      // Load messages
      const messagesData = localStorage.getItem(this.STORAGE_KEYS.MESSAGES)
      if (messagesData) {
        const messagesObj = JSON.parse(messagesData)
        Object.entries(messagesObj).forEach(([chatId, messages]) => {
          this.messages.set(chatId, (messages as Message[]).map(msg => ({
            ...msg,
            timestamp: new Date(msg.timestamp)
          })))
        })
      }

      // Load archived chats
      const archivedData = localStorage.getItem(this.STORAGE_KEYS.ARCHIVED)
      if (archivedData) {
        const archivedArray = JSON.parse(archivedData) as ArchivedChat[]
        archivedArray.forEach(chat => {
          this.archivedChats.set(chat.id, {
            ...chat,
            createdAt: new Date(chat.createdAt),
            updatedAt: new Date(chat.updatedAt),
            archivedAt: new Date(chat.archivedAt)
          })
        })
      }
    } catch (error) {
      console.error('Error loading data from storage:', error)
    }
  }

  private saveToStorage(): void {
    if (typeof window === 'undefined') return

    try {
      // Save chats
      const chatsArray = Array.from(this.chats.values())
      localStorage.setItem(this.STORAGE_KEYS.CHATS, JSON.stringify(chatsArray))

      // Save messages
      const messagesObj: Record<string, Message[]> = {}
      this.messages.forEach((messages, chatId) => {
        messagesObj[chatId] = messages
      })
      localStorage.setItem(this.STORAGE_KEYS.MESSAGES, JSON.stringify(messagesObj))

      // Save archived chats
      const archivedArray = Array.from(this.archivedChats.values())
      localStorage.setItem(this.STORAGE_KEYS.ARCHIVED, JSON.stringify(archivedArray))
    } catch (error) {
      console.error('Error saving data to storage:', error)
    }
  }

  async createChat(title: string): Promise<Chat> {
    const id = Math.random().toString(36).substring(2, 15)
    const chat: Chat = {
      id,
      title,
      createdAt: new Date(),
      updatedAt: new Date(),
      messages: []
    }
    
    this.chats.set(id, chat)
    this.messages.set(id, [])
    this.saveToStorage()
    return chat
  }

  async getChats(): Promise<Chat[]> {
    const chats = Array.from(this.chats.values())
    return chats.sort((a, b) => b.updatedAt.getTime() - a.updatedAt.getTime())
  }

  async getChat(id: string): Promise<Chat | null> {
    const chat = this.chats.get(id)
    if (!chat) return null
    
    const messages = this.messages.get(id) || []
    return { ...chat, messages }
  }

  async addMessage(chatId: string, content: string, sender: 'user' | 'sasha'): Promise<Message> {
    const messageId = Math.random().toString(36).substring(2, 15)
    const message: Message = {
      id: messageId,
      chatId,
      content,
      sender,
      timestamp: new Date()
    }

    const messages = this.messages.get(chatId) || []
    messages.push(message)
    this.messages.set(chatId, messages)

    // Update chat's updatedAt timestamp
    const chat = this.chats.get(chatId)
    if (chat) {
      chat.updatedAt = new Date()
      this.chats.set(chatId, chat)
    }

    this.saveToStorage()
    return message
  }

  async updateChatTitle(chatId: string, title: string): Promise<boolean> {
    const chat = this.chats.get(chatId)
    if (!chat) return false
    
    // Truncate title to 30 characters
    const truncatedTitle = title.length > 30 ? title.substring(0, 30).trim() : title
    
    chat.title = truncatedTitle
    chat.updatedAt = new Date()
    this.chats.set(chatId, chat)
    
    this.saveToStorage()
    return true
  }

  async deleteChat(id: string): Promise<boolean> {
    const deleted = this.chats.delete(id)
    this.messages.delete(id)
    this.saveToStorage()
    return deleted
  }

  async archiveChat(id: string): Promise<boolean> {
    const chat = this.chats.get(id)
    if (!chat) return false
    
    // Get full chat with messages
    const fullChat = await this.getChat(id)
    if (!fullChat) return false
    
    // Archive the chat
    const archivedChat: ArchivedChat = {
      ...fullChat,
      archivedAt: new Date()
    }
    this.archivedChats.set(id, archivedChat)
    
    // Remove from active chats
    this.chats.delete(id)
    this.messages.delete(id)
    
    this.saveToStorage()
    return true
  }

  async restoreFromArchive(id: string): Promise<boolean> {
    const archivedChat = this.archivedChats.get(id)
    if (!archivedChat) return false
    
    // Restore to active chats
    const { archivedAt, ...chat } = archivedChat
    this.chats.set(id, chat)
    this.messages.set(id, chat.messages || [])
    
    // Remove from archive
    this.archivedChats.delete(id)
    
    this.saveToStorage()
    return true
  }

  // Get archived chats
  getArchivedChats(): ArchivedChat[] {
    return Array.from(this.archivedChats.values())
      .sort((a, b) => b.archivedAt.getTime() - a.archivedAt.getTime())
  }

  // Clean up expired archives and return count of deleted items
  cleanupExpiredArchives(): number {
    const now = new Date()
    const cutoffTime = new Date(now.getTime() - (24 * 60 * 60 * 1000)) // 24 hours ago
    
    const expiredIds: string[] = []
    this.archivedChats.forEach((chat, id) => {
      if (chat.archivedAt <= cutoffTime) {
        expiredIds.push(id)
      }
    })
    
    expiredIds.forEach(id => this.archivedChats.delete(id))
    
    if (expiredIds.length > 0) {
      this.saveToStorage()
    }
    
    return expiredIds.length
  }
}

export const db = new ChatDatabase()
