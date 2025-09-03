import { Chat, Message } from '@/types/chat'

// Simple in-memory storage for now - can be replaced with SQLite later
class ChatDatabase {
  private chats: Map<string, Chat> = new Map()
  private messages: Map<string, Message[]> = new Map()

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

    return message
  }

  async deleteChat(id: string): Promise<boolean> {
    const deleted = this.chats.delete(id)
    this.messages.delete(id)
    return deleted
  }
}

export const db = new ChatDatabase()
