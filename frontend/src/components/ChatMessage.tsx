'use client'

import ReactMarkdown from 'react-markdown'
import { Message } from '../types/chat'

interface ChatMessageProps {
  message: Message
  'aria-posinset'?: number
  'aria-setsize'?: number
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
        <div role="text" className="text-sm leading-relaxed">
          <ReactMarkdown
            components={{
              a: ({ href, children }) => (
                <a
                  href={href}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="underline font-medium hover:opacity-80"
                >
                  {children}
                </a>
              ),
              p: ({ children }) => <p className="mb-2 last:mb-0">{children}</p>,
              ol: ({ children }) => <ol className="list-decimal pl-5 mb-2 space-y-1">{children}</ol>,
              ul: ({ children }) => <ul className="list-disc pl-5 mb-2 space-y-1">{children}</ul>,
              li: ({ children }) => <li>{children}</li>,
              strong: ({ children }) => <strong className="font-semibold">{children}</strong>,
              em: ({ children }) => <em className="italic">{children}</em>,
              code: ({ children }) => <code className="bg-black/10 dark:bg-white/10 rounded px-1 py-0.5 text-xs font-mono">{children}</code>,
            }}
          >
            {message.content}
          </ReactMarkdown>
        </div>
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
