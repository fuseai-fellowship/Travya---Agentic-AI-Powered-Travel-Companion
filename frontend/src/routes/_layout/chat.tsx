import { useState, useEffect, useRef } from 'react';
import { createFileRoute } from '@tanstack/react-router';
import { FiSend, FiUser, FiMessageCircle, FiPlus, FiRefreshCw, FiTrash2 } from 'react-icons/fi';
import { useTravel } from '@/contexts/TravelContext';

export const Route = createFileRoute('/_layout/chat')({
  component: ChatPage,
});

interface Message {
  id: string;
  content: string;
  sender: 'user' | 'ai';
  timestamp: Date;
  conversationId?: number;
}

function ChatPage() {
  const { chatWithAI, conversations, currentConversation, setCurrentConversation, fetchConversationMessages, deleteConversation } = useTravel();
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isLoadingMessages, setIsLoadingMessages] = useState(false);
  const [conversationToDelete, setConversationToDelete] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    const loadConversationMessages = async () => {
      if (currentConversation) {
        console.log('Loading messages for conversation:', currentConversation.id);
        setIsLoadingMessages(true);
        try {
          const conversationMessages = await fetchConversationMessages(currentConversation.id);
          console.log('Fetched messages:', conversationMessages);
          
          if (conversationMessages.length > 0) {
            // Convert backend messages to frontend format
            const formattedMessages: Message[] = conversationMessages.map(msg => ({
              id: msg.id.toString(),
              content: msg.message,
              sender: msg.sender,
              timestamp: new Date(msg.created_at),
              conversationId: parseInt(msg.conversation_id)
            }));
            console.log('Raw messages from backend:', conversationMessages);
            console.log('Formatted messages:', formattedMessages);
            setMessages(formattedMessages);
          } else {
            // No messages yet, show welcome message
            console.log('No messages found, showing welcome message');
            setMessages([
              {
                id: '1',
                content: `Hello! I'm your AI travel assistant. How can I help you plan your next adventure?`,
                sender: 'ai',
                timestamp: new Date(),
              }
            ]);
          }
        } catch (error) {
          console.error('Error loading conversation messages:', error);
          // Fallback to welcome message
          setMessages([
            {
              id: '1',
              content: `Hello! I'm your AI travel assistant. How can I help you plan your next adventure?`,
              sender: 'ai',
              timestamp: new Date(),
            }
          ]);
        } finally {
          setIsLoadingMessages(false);
        }
      } else {
        console.log('No current conversation, clearing messages');
        setMessages([]);
      }
    };

    // Always load messages when conversation changes
    if (currentConversation) {
      loadConversationMessages();
    } else {
      setMessages([]);
    }
  }, [currentConversation?.id]); // Only depend on conversation ID

  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputMessage.trim() || isLoading) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      content: inputMessage,
      sender: 'user',
      timestamp: new Date(),
    };

    // Add user message immediately to UI
    setMessages(prev => [...prev, userMessage]);
    setInputMessage('');
    setIsLoading(true);

    try {
      // Send message to backend - it will create conversation if needed
      console.log('Sending message to backend:', inputMessage, 'Current conversation:', currentConversation?.id);
      const response = await chatWithAI(inputMessage, currentConversation?.id);
      console.log('Backend response:', response);
      
      // Update current conversation with the one returned by backend
      if (response.conversation_id && response.conversation_id !== currentConversation?.id) {
        console.log('Creating new conversation with ID:', response.conversation_id);
        const newConversation = {
          id: response.conversation_id,
          title: inputMessage.length > 50 ? inputMessage.substring(0, 50) + '...' : inputMessage,
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
          last_message: response.message?.substring(0, 100) || inputMessage.substring(0, 100)
        };
        setCurrentConversation(newConversation);
      }
      
      const aiMessage: Message = {
        id: (Date.now() + 1).toString(),
        content: response.message || 'I received your message but couldn\'t generate a response.',
        sender: 'ai',
        timestamp: new Date(),
        conversationId: response.conversation_id ? parseInt(response.conversation_id) : undefined,
      };

      setMessages(prev => [...prev, aiMessage]);
    } catch (error) {
      console.error('Failed to send message:', error);
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        content: 'Sorry, I encountered an error. Please try again.',
        sender: 'ai',
        timestamp: new Date(),
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const startNewConversation = () => {
    try {
      console.log('Starting new conversation...');
      // Clear current conversation and messages first
      setCurrentConversation(null);
      setMessages([]);
      
      // The conversation will be created by the backend when the first message is sent
      // We just need to clear the current state
      console.log('New conversation state cleared');
    } catch (error) {
      console.error('Error starting new conversation:', error);
    }
  };

  const quickQuestions = [
    "What's the best time to visit Japan?",
    "Suggest a 5-day itinerary for Paris",
    "What are the must-see attractions in Rome?",
    "How can I save money on flights?",
    "What should I pack for a beach vacation?",
    "Recommend budget-friendly hotels in Bangkok",
  ];

  const handleQuickQuestion = (question: string) => {
    setInputMessage(question);
    inputRef.current?.focus();
  };

  const formatTime = (timestamp: Date) => {
    return timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  const handleDeleteConversation = async (conversationId: string) => {
    try {
      console.log('Deleting conversation:', conversationId);
      await deleteConversation(conversationId);
      
      // If we're deleting the current conversation, clear it
      if (currentConversation?.id === conversationId) {
        setCurrentConversation(null);
        setMessages([]);
      }
      
      setConversationToDelete(null);
      console.log('Conversation deleted successfully');
    } catch (error) {
      console.error('Error deleting conversation:', error);
    }
  };

  return (
    <div className="grok-chat-page">
      {/* Sidebar */}
      <div className="chat-sidebar">
        <div className="sidebar-header">
          <button onClick={startNewConversation} className="new-chat-btn">
            <FiPlus className="icon" />
            New Chat
          </button>
        </div>
        
        <div className="conversations-list">
          {Array.isArray(conversations) && conversations.length > 0 ? (
            conversations.map((conversation) => (
              <div 
                key={conversation.id} 
                className={`conversation-item ${currentConversation?.id === conversation.id ? 'active' : ''}`}
                onClick={() => {
                  console.log('Switching to conversation:', conversation);
                  setCurrentConversation(conversation);
                }}
              >
                <div className="conversation-content">
                  <div className="conversation-title">
                    {conversation.title || 'Travel Chat'}
                  </div>
                  <div className="conversation-preview">
                    {conversation.last_message || 'No messages yet'}
                  </div>
                </div>
                <div className="conversation-actions">
                  <div className="conversation-time">
                    {conversation.updated_at && formatTime(new Date(conversation.updated_at))}
                  </div>
                  <button
                    className="delete-conversation-btn"
                    onClick={(e) => {
                      e.stopPropagation();
                      setConversationToDelete(conversation.id);
                    }}
                    title="Delete conversation"
                  >
                    <FiTrash2 />
                  </button>
                </div>
              </div>
            ))
          ) : (
            <div className="no-conversations">
              <p>No conversations yet</p>
            </div>
          )}
        </div>
      </div>

      {/* Main Chat Area */}
      <div className="chat-main">
        {currentConversation ? (
          <>
            {/* Chat Header */}
            <div className="chat-header">
            <div className="chat-title">
              <FiMessageCircle className="icon" />
              <span>AI Travel Assistant</span>
            </div>
              <div className="chat-actions">
                <button onClick={startNewConversation} className="action-btn" title="New Chat">
                  <FiRefreshCw className="icon" />
                </button>
              </div>
            </div>

            {/* Messages */}
            <div className="messages-container">
              {isLoadingMessages ? (
                <div className="loading-messages">
                  <div className="loading-spinner">
                    <span></span>
                    <span></span>
                    <span></span>
                  </div>
                  <p>Loading conversation...</p>
                </div>
              ) : messages.length === 0 ? (
                <div className="welcome-message">
                  <FiMessageCircle className="welcome-icon" />
                  <h3>Welcome to AI Travel Assistant!</h3>
                  <p>I'm here to help you plan your perfect trip. Ask me anything!</p>
                    
                    <div className="quick-questions">
                      <h4>Quick Questions:</h4>
                      <div className="quick-questions-grid">
                        {quickQuestions.map((question, index) => (
                          <button
                            key={index}
                            className="quick-question-chip"
                            onClick={() => handleQuickQuestion(question)}
                          >
                            {question}
                          </button>
                        ))}
                      </div>
                    </div>
                  </div>
                ) : (
                  messages.map((message) => (
                    <div key={message.id} className={`message ${message.sender === 'user' ? 'user-message' : 'ai-message'}`}>
                      {message.sender === 'user' ? (
                        // User message on the right
                        <>
                          <div className="message-content">
                            <div className="message-text">{message.content}</div>
                            <div className="message-time">{formatTime(message.timestamp)}</div>
                          </div>
                          <div className="message-avatar">
                            <FiUser />
                          </div>
                        </>
                      ) : (
                        // AI message on the left
                        <>
                          <div className="message-avatar">
                            <FiMessageCircle />
                          </div>
                          <div className="message-content">
                            <div className="message-text">{message.content}</div>
                            <div className="message-time">{formatTime(message.timestamp)}</div>
                          </div>
                        </>
                      )}
                    </div>
                  ))
                )}
              
              {isLoading && (
                <div className="message ai-message typing">
                  <div className="message-avatar">
                    <FiMessageCircle />
                  </div>
                  <div className="message-content">
                    <div className="typing-indicator">
                      <span></span>
                      <span></span>
                      <span></span>
                    </div>
                  </div>
                </div>
              )}
              
              <div ref={messagesEndRef} />
            </div>

            {/* Input Area */}
            <div className="chat-input-area">
              <form onSubmit={handleSendMessage} className="chat-form">
                <div className="input-container">
                  <input
                    ref={inputRef}
                    type="text"
                    value={inputMessage}
                    onChange={(e) => setInputMessage(e.target.value)}
                    placeholder="Ask about your travel plans..."
                    className="chat-input"
                    disabled={isLoading}
                    autoFocus
                  />
                  <button 
                    type="submit" 
                    className="send-button"
                    disabled={isLoading || !inputMessage.trim()}
                  >
                    <FiSend />
                  </button>
                </div>
              </form>
            </div>
          </>
        ) : (
          <>
            {/* Welcome Header */}
            <div className="chat-header">
              <div className="chat-title">
                <FiMessageCircle className="icon" />
                <span>AI Travel Assistant</span>
              </div>
              <div className="chat-actions">
                <button onClick={startNewConversation} className="action-btn" title="New Chat">
                  <FiRefreshCw className="icon" />
                </button>
              </div>
            </div>

            {/* Welcome Messages */}
            <div className="messages-container">
              <div className="welcome-message">
                <FiMessageCircle className="welcome-icon" />
                <h3>Welcome to AI Travel Assistant!</h3>
                <p>I'm here to help you plan your perfect trip. Ask me anything!</p>
                  
                <div className="quick-questions">
                  <h4>Quick Questions:</h4>
                  <div className="quick-questions-grid">
                    {quickQuestions.map((question, index) => (
                      <button
                        key={index}
                        className="quick-question-chip"
                        onClick={() => handleQuickQuestion(question)}
                      >
                        {question}
                      </button>
                    ))}
                  </div>
                </div>
              </div>
            </div>

            {/* Input Area */}
            <div className="chat-input-area">
              <form onSubmit={handleSendMessage} className="chat-form">
                <div className="input-container">
                  <input
                    ref={inputRef}
                    type="text"
                    value={inputMessage}
                    onChange={(e) => setInputMessage(e.target.value)}
                    placeholder="Ask about your travel plans..."
                    className="chat-input"
                    disabled={isLoading}
                    autoFocus
                  />
                  <button 
                    type="submit" 
                    className="send-button"
                    disabled={isLoading || !inputMessage.trim()}
                  >
                    <FiSend />
                  </button>
                </div>
              </form>
            </div>
          </>
        )}
      </div>

      {/* Delete Confirmation Dialog */}
      {conversationToDelete && (
        <div className="delete-confirmation-overlay">
          <div className="delete-confirmation-dialog">
            <h3>Delete Conversation</h3>
            <p>Are you sure you want to delete this conversation? This action cannot be undone.</p>
            <div className="confirmation-buttons">
              <button
                className="cancel-btn"
                onClick={() => setConversationToDelete(null)}
              >
                Cancel
              </button>
              <button
                className="delete-btn"
                onClick={() => handleDeleteConversation(conversationToDelete)}
              >
                Delete
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}