'use client'

import { Message } from '../types/chat'

interface ChatMessageProps {
  message: Message
  'aria-posinset'?: number
  'aria-setsize'?: number
}

function renderContent(content: string): React.ReactNode {
  const linkRegex = /\[([^\]]+)\]\((https?:\/\/[^\)]+)\)/g
  const parts: React.ReactNode[] = []
  let lastIndex = 0
  let match: RegExpExecArray | null

  while ((match = linkRegex.exec(content)) !== null) {
    if (match.index > lastIndex) {
      parts.push(content.slice(lastIndex, match.index))
    }
    parts.push(
      <a
        key={match.index}
        href={match[2]}
        target="_blank"
        rel="noopener noreferrer"
        className="underline font-medium hover:opacity-80"
        aria-label={`${match[1]} (opens in new tab)`}
      >
        {match[1]}
      </a>
    )
    lastIndex = match.index + match[0].length
  }

  if (lastIndex < content.length) {
    parts.push(content.slice(lastIndex))
  }

  return parts.length > 0 ? parts : content
}

export default function ChatMessage({ 
  message, 
  'aria-posinset': ariaPosinset, 
  'aria-setsize': ariaSetsize 
}: ChatMessageProps) {
  const isUser = message.sender === 'user'
  const senderName = isUser ? 'You' : 'Sasha'
  
  return (
    <div 
      className={`flex gap-3 p-4 ${isUser ? 'flex-row-reverse' : 'flex-row'}`}
      role="article"
      aria-label={`Message from ${senderName}`}
      aria-posinset={ariaPosinset}
      aria-setsize={ariaSetsize}
    >
      {/* Avatar */}
      <div className="flex-shrink-0">
        <div 
          className={`
            w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium
            ${isUser 
              ? 'bg-blue-600 text-white' 
              : 'bg-purple-600 text-white'
            }
          `}
          aria-label={`${senderName} avatar`}
          role="img"
        >
          {isUser ? 'U' : 'S'}
        </div>
      </div>
      
      {/* Message bubble */}
      <div className={`
        max-w-[70%] rounded-lg px-4 py-2
        ${isUser 
          ? 'bg-blue-600 text-white' 
          : 'bg-gray-200 dark:bg-gray-700 text-gray-900 dark:text-white'
        }
      `}>
        <div className="sr-only">{senderName} said:</div>
        <p className="whitespace-pre-wrap" role="text">
          {renderContent(message.content)}
        </p>
        <div 
          className={`
            text-xs mt-1 opacity-70
            ${isUser ? 'text-blue-100' : 'text-gray-500 dark:text-gray-400'}
          `}
          aria-label={`Sent at ${message.timestamp.toLocaleTimeString()}`}
        >
          {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
        </div>
      </div>
    </div>
  )
}
