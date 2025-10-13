import { useState, useEffect, useRef, memo } from 'react'
import { motion } from 'framer-motion'
import { HiPaperAirplane, HiUser, HiChip, HiInformationCircle, HiSparkles } from 'react-icons/hi'
import { useChat } from '../hooks'
import { security, formatters } from '../utils'
import { APP_CONFIG } from '../constants'

// Message component with animations
const Message = memo(({ message, index }) => {
  const isUser = message.role === 'user'
  
  return (
    <motion.div 
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3, delay: index * 0.05 }}
      className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}
    >
      <div className={`flex items-start space-x-2 max-w-[85%] ${isUser ? 'flex-row-reverse space-x-reverse' : ''}`}>
        {/* Avatar */}
        <motion.div 
          whileHover={{ scale: 1.1 }}
          className={`flex-shrink-0 w-9 h-9 rounded-xl flex items-center justify-center shadow-md ${
            isUser 
              ? 'bg-gradient-to-br from-primary-600 to-primary-500' 
              : 'bg-gradient-to-br from-gray-200 to-gray-300'
          }`}
        >
          {isUser ? (
            <HiUser className="text-white text-base" />
          ) : (
            <HiSparkles className="text-gray-700 text-base" />
          )}
        </motion.div>
        
        {/* Message bubble */}
        <motion.div 
          whileHover={{ scale: 1.02 }}
          className={`px-4 py-3 rounded-2xl shadow-md transition-all ${
            isUser 
              ? 'bg-gradient-to-br from-primary-600 to-primary-500 text-white rounded-tr-md' 
              : 'bg-white/80 backdrop-blur-sm text-gray-800 rounded-tl-md border border-gray-200'
          }`}
        >
          <p 
            className="whitespace-pre-wrap break-words text-sm leading-relaxed"
            dangerouslySetInnerHTML={{ __html: security.sanitizeHTML(message.content) }}
          />
        </motion.div>
      </div>
    </motion.div>
  )
})

Message.displayName = 'Message'

// Loading indicator with smooth animation
const LoadingIndicator = memo(() => (
  <motion.div 
    initial={{ opacity: 0, y: 10 }}
    animate={{ opacity: 1, y: 0 }}
    className="flex justify-start"
  >
    <div className="flex items-start space-x-2 max-w-[85%]">
      <div className="flex-shrink-0 w-9 h-9 rounded-xl bg-gradient-to-br from-gray-200 to-gray-300 flex items-center justify-center shadow-md">
        <HiSparkles className="text-gray-700 text-base" />
      </div>
      <div className="px-4 py-3 rounded-2xl rounded-tl-md bg-white/80 backdrop-blur-sm border border-gray-200 shadow-md">
        <div className="flex space-x-1">
          <motion.div 
            animate={{ y: [0, -8, 0] }}
            transition={{ duration: 0.6, repeat: Infinity, ease: "easeInOut" }}
            className="w-2 h-2 bg-primary-400 rounded-full"
          />
          <motion.div 
            animate={{ y: [0, -8, 0] }}
            transition={{ duration: 0.6, repeat: Infinity, ease: "easeInOut", delay: 0.1 }}
            className="w-2 h-2 bg-primary-400 rounded-full"
          />
          <motion.div 
            animate={{ y: [0, -8, 0] }}
            transition={{ duration: 0.6, repeat: Infinity, ease: "easeInOut", delay: 0.2 }}
            className="w-2 h-2 bg-primary-400 rounded-full"
          />
        </div>
      </div>
    </div>
  </motion.div>
))

LoadingIndicator.displayName = 'LoadingIndicator'

const ChatInterface = ({ videoId }) => {
  const [input, setInput] = useState('')
  const messagesEndRef = useRef(null)
  
  const {
    session,
    messages,
    sending,
    error,
    createOrGetSession,
    sendMessage: sendChatMessage,
    setError
  } = useChat()

  useEffect(() => {
    if (videoId) {
      createOrGetSession(videoId)
    }
  }, [videoId, createOrGetSession])

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    
    if (!input.trim() || !session || sending) return
    
    // Input validation
    if (input.length > APP_CONFIG.MAX_MESSAGE_LENGTH) {
      setError(`메시지는 ${APP_CONFIG.MAX_MESSAGE_LENGTH}자를 초과할 수 없습니다`)
      return
    }
    
    const userMessage = input.trim()
    setInput('')
    
    try {
      await sendChatMessage(session.id, userMessage)
    } catch (err) {
      console.error('Failed to send message:', err)
    }
  }

  const handleInputChange = (e) => {
    const value = e.target.value
    if (value.length <= APP_CONFIG.MAX_MESSAGE_LENGTH) {
      setInput(value)
      setError('')
    }
  }

  return (
    <div className="flex flex-col h-full bg-gradient-to-b from-gray-50/50 to-white/50">
      {/* Messages */}
      <div className="flex-1 overflow-auto p-4 space-y-4">
        {messages.length === 0 && (
          <motion.div 
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            className="text-center mt-12"
          >
            <div className="inline-flex items-center justify-center w-20 h-20 bg-gradient-to-br from-primary-100 to-accent-100 rounded-2xl mb-4 shadow-lg">
              <HiSparkles className="text-4xl text-primary-600" />
            </div>
            <p className="text-gray-800 font-bold text-lg mb-2">AI와 대화를 시작해보세요!</p>
            <p className="text-sm text-gray-500">
              학습 내용에 대해 질문하거나 토론할 수 있습니다.
            </p>
          </motion.div>
        )}
        
        {messages.map((msg, index) => (
          <Message key={index} message={msg} index={index} />
        ))}
        
        {sending && <LoadingIndicator />}
        
        <div ref={messagesEndRef} />
      </div>
      
      {/* Session Info */}
      {/* 토큰/비용 정보는 학습자에게 표시하지 않음 */}
      
      {/* Error */}
      {error && (
        <motion.div 
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className="alert alert-error mx-4 my-2"
        >
          <HiInformationCircle className="text-lg flex-shrink-0" />
          <span>{error}</span>
        </motion.div>
      )}
      
      {/* Input */}
      <form onSubmit={handleSubmit} className="p-4 bg-white/80 backdrop-blur-sm border-t border-gray-200/50">
        <div className="flex space-x-2">
          <div className="flex-1 relative">
            <input
              type="text"
              className="w-full px-5 py-3 bg-gray-50 border border-gray-200 rounded-2xl focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent transition-all text-sm placeholder-gray-400"
              value={input}
              onChange={handleInputChange}
              placeholder="메시지를 입력하세요..."
              disabled={sending}
              maxLength={APP_CONFIG.MAX_MESSAGE_LENGTH}
            />
            {input.length > APP_CONFIG.MAX_MESSAGE_LENGTH * 0.9 && (
              <div className="absolute right-4 top-1/2 transform -translate-y-1/2 text-xs text-gray-400 font-medium">
                {input.length}/{APP_CONFIG.MAX_MESSAGE_LENGTH}
              </div>
            )}
          </div>
          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            type="submit"
            className={`p-3 rounded-2xl transition-all shadow-md ${
              sending || !input.trim()
                ? 'bg-gray-200 text-gray-400 cursor-not-allowed'
                : 'bg-gradient-to-br from-primary-600 to-primary-500 text-white hover:shadow-lg'
            }`}
            disabled={sending || !input.trim()}
          >
            <HiPaperAirplane className="text-xl transform rotate-90" />
          </motion.button>
        </div>
      </form>
    </div>
  )
}

export default ChatInterface
