import { useState, useEffect, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { sendChatMessage, getChatSessions, getSessionMessages } from '../services/api'
import '../styles/Chatbot.css'

export default function Chatbot() {
  const navigate = useNavigate()
  const messagesEndRef = useRef(null)

  const [messages, setMessages] = useState([])
  const [inputMessage, setInputMessage] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState('')
  const [sessionId, setSessionId] = useState(null)
  const [location, setLocation] = useState('')

  // Auto-scroll to bottom when new messages arrive
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  // Check if user is logged in
  useEffect(() => {
    const token = localStorage.getItem('token')
    if (!token) {
      navigate('/login')
    }
  }, [navigate])

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!inputMessage.trim() || isLoading) return

    const userMessage = inputMessage.trim()
    setInputMessage('')
    setError('')

    // Add user message to UI immediately
    const newUserMessage = {
      role: 'user',
      content: userMessage,
      created_at: new Date().toISOString()
    }
    setMessages(prev => [...prev, newUserMessage])

    setIsLoading(true)

    try {
      // Send message to backend
      const response = await sendChatMessage({
        message: userMessage,
        session_id: sessionId,
        location: location || undefined
      })

      // Update session ID if it's a new session
      if (!sessionId) {
        setSessionId(response.session_id)
      }

      // Add assistant response to messages
      const assistantMessage = {
        role: 'assistant',
        content: response.response,
        recommendations: response.recommendations,
        created_at: new Date().toISOString()
      }
      setMessages(prev => [...prev, assistantMessage])

    } catch (err) {
      setError(err.message || 'Failed to get response. Please try again.')
      // Remove the user message that failed
      setMessages(prev => prev.slice(0, -1))
    } finally {
      setIsLoading(false)
    }
  }

  const handleNewChat = () => {
    setMessages([])
    setSessionId(null)
    setError('')
  }

  const handleLogout = () => {
    localStorage.removeItem('token')
    navigate('/login')
  }

  return (
    <div className="chatbot-container">
      <div className="chatbot-header">
        <div className="header-left">
          <h1>KindaLike Restaurant Finder</h1>
          <p className="subtitle">Ask me for restaurant recommendations!</p>
        </div>
        <div className="header-actions">
          <input
            type="text"
            placeholder="Override location (e.g., Ithaca, NY)"
            value={location}
            onChange={(e) => setLocation(e.target.value)}
            className="location-input"
          />
          <button onClick={handleNewChat} className="new-chat-btn">
            New Chat
          </button>
          <button onClick={handleLogout} className="logout-btn">
            Logout
          </button>
        </div>
      </div>

      <div className="chat-messages">
        {messages.length === 0 && (
          <div className="welcome-message">
            <h2>Welcome to your AI Restaurant Advisor!</h2>
            <p>Tell me what you're looking for and I'll find the perfect restaurant for you.</p>
            <div className="example-queries">
              <p>Try asking:</p>
              <ul>
                <li>"I want Italian food for a romantic date night"</li>
                <li>"Find me a quick lunch spot nearby"</li>
                <li>"Where can I get healthy vegetarian food?"</li>
                <li>"I need a place for a birthday celebration"</li>
              </ul>
            </div>
          </div>
        )}

        {messages.map((msg, index) => (
          <div key={index} className={`message ${msg.role}`}>
            <div className="message-content">
              <div className="message-header">
                <span className="message-role">
                  {msg.role === 'user' ? 'You' : 'AI Assistant'}
                </span>
                <span className="message-time">
                  {new Date(msg.created_at).toLocaleTimeString()}
                </span>
              </div>
              <p className="message-text">{msg.content}</p>

              {msg.recommendations && msg.recommendations.length > 0 && (
                <div className="recommendations">
                  {msg.recommendations.map((restaurant, idx) => (
                    <div key={idx} className="restaurant-card">
                      {restaurant.image_url && (
                        <img
                          src={restaurant.image_url}
                          alt={restaurant.name}
                          className="restaurant-image"
                        />
                      )}
                      <div className="restaurant-info">
                        <div className="restaurant-header">
                          <h3 className="restaurant-name">{restaurant.name}</h3>
                          <div className="restaurant-rating">
                            <span className="rating-stars">{'⭐'.repeat(Math.round(restaurant.rating))}</span>
                            <span className="rating-text">
                              {restaurant.rating} ({restaurant.review_count} reviews)
                            </span>
                          </div>
                        </div>
                        <div className="restaurant-details">
                          <p className="categories">{restaurant.categories.join(', ')}</p>
                          <p className="price-distance">
                            <span className="price">{restaurant.price}</span>
                            <span className="distance">{restaurant.distance} mi away</span>
                          </p>
                          <p className="address">{restaurant.address}</p>
                          {restaurant.phone !== 'N/A' && (
                            <p className="phone">📞 {restaurant.phone}</p>
                          )}
                        </div>
                        <a
                          href={restaurant.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="view-on-yelp"
                        >
                          View on Yelp →
                        </a>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        ))}

        {isLoading && (
          <div className="message assistant">
            <div className="message-content">
              <div className="message-header">
                <span className="message-role">AI Assistant</span>
              </div>
              <div className="loading-indicator">
                <div className="loading-dots">
                  <span></span>
                  <span></span>
                  <span></span>
                </div>
                <p>Finding the perfect restaurants for you...</p>
              </div>
            </div>
          </div>
        )}

        {error && (
          <div className="error-message">
            <p>⚠️ {error}</p>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      <form onSubmit={handleSubmit} className="chat-input-form">
        <input
          type="text"
          value={inputMessage}
          onChange={(e) => setInputMessage(e.target.value)}
          placeholder="What kind of restaurant are you looking for?"
          className="chat-input"
          disabled={isLoading}
        />
        <button
          type="submit"
          className="send-button"
          disabled={isLoading || !inputMessage.trim()}
        >
          {isLoading ? 'Sending...' : 'Send'}
        </button>
      </form>
    </div>
  )
}
