/**
 * Generate a concise chat title from the user's first message
 * @param userMessage The user's first message
 * @returns A title of 30 characters or less
 */
export function generateChatTitle(userMessage: string): string {
  // Remove extra whitespace and newlines
  const cleanMessage = userMessage.trim().replace(/\s+/g, ' ')
  
  // If message is short enough, use it as-is
  if (cleanMessage.length <= 30) {
    return cleanMessage
  }
  
  // Try to find a good breaking point (sentence end, question mark, etc.)
  const breakPoints = ['.', '?', '!', ',', ';']
  
  for (const breakPoint of breakPoints) {
    const index = cleanMessage.indexOf(breakPoint)
    if (index > 10 && index <= 28) { // Leave room for potential ellipsis
      return cleanMessage.substring(0, index + 1).trim()
    }
  }
  
  // Try to break at a word boundary
  const words = cleanMessage.split(' ')
  let title = ''
  
  for (const word of words) {
    if ((title + ' ' + word).length > 27) { // Leave room for "..."
      break
    }
    title = title ? title + ' ' + word : word
  }
  
  // If we have a reasonable title, use it
  if (title.length > 10) {
    return title + '...'
  }
  
  // Fallback: just truncate at 27 chars and add ellipsis
  return cleanMessage.substring(0, 27).trim() + '...'
}

/**
 * Alternative: Generate title using AI response context
 * This could be enhanced to use the AI's response to create more contextual titles
 */
export function generateContextualTitle(userMessage: string, aiResponse: string): string {
  // For now, just use the user message, but this could be enhanced
  // to analyze both messages and create a more descriptive title
  return generateChatTitle(userMessage)
}
