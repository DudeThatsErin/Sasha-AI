export interface Message {
  id: string
  chatId: string
  content: string
  sender: 'user' | 'sasha'
  timestamp: Date
}

export interface Chat {
  id: string
  title: string
  createdAt: Date
  updatedAt: Date
  messages: Message[]
}
