import { useState, useEffect, useRef } from 'react';
import { createFileRoute } from '@tanstack/react-router';
import { FiSend, FiUser, FiMessageCircle, FiPlus, FiRefreshCw, FiTrash2 } from 'react-icons/fi';
import { useTravel } from '@/contexts/TravelContext';
import { useSidebar } from '@/contexts/SidebarContext';

export const Route = createFileRoute('/_layout/chat')({
  component: ChatPage,
});

interface Message {
  id: string;
  content: string;
  role: 'user' | 'assistant';
  timestamp: Date;
  conversationId?: number;
  messageType?: 'text' | 'image' | 'file' | 'location';
  attachments?: string[];
  images?: Array<{
    id: string;
    url: string;
    thumbnail_url: string;
    title: string;
    description?: string;
    place_name: string;
    place_type: string;
    photographer_name?: string;
    photographer_url?: string;
    source: string;
    width?: number;
    height?: number;
    relevance_score: number;
  }>;
  message_metadata?: any; // Renamed from metadata
}

function ChatPage() {
  const { chatWithAI, conversations, currentConversation, setCurrentConversation, fetchConversationMessages, deleteConversation } = useTravel();
  const { isCollapsed } = useSidebar();
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isLoadingMessages, setIsLoadingMessages] = useState(false);
  const [conversationToDelete, setConversationToDelete] = useState<string | null>(null);
  const [, _setIsScrapingImages] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Auto-scroll to bottom when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const scrapeImages = async (query: string) => {
    if (!currentConversation?.id) return;
    
    _setIsScrapingImages(true);
    try {
      const response = await fetch('http://localhost:8000/api/v1/ai-travel/scrape-images', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`
        },
        body: JSON.stringify({
          query,
          conversation_id: currentConversation.id,
          limit: 5
        })
      });
      
      if (response.ok) {
        const data = await response.json();
        return data.images;
      }
    } catch (error) {
      console.error('Error scraping images:', error);
    } finally {
      _setIsScrapingImages(false);
    }
    return [];
  };

  // Load messages when conversation changes
  useEffect(() => {
    const loadConversationMessages = async () => {
      if (currentConversation?.id) {
        console.log('Loading messages for conversation:', currentConversation.id);
        setIsLoadingMessages(true);
        try {
          const fetchedMessages = await fetchConversationMessages(currentConversation.id);
          console.log('Fetched messages:', fetchedMessages);
          
          if (fetchedMessages && fetchedMessages.length > 0) {
            console.log('Raw fetched messages:', fetchedMessages);
            const formattedMessages = fetchedMessages.map((msg: any) => {
              console.log('Processing message:', msg);
              
              // Parse images if they exist
              let parsedImages = null;
              if (msg.images) {
                try {
                  parsedImages = typeof msg.images === 'string' ? JSON.parse(msg.images) : msg.images;
                } catch (e) {
                  console.error('Error parsing images:', e);
                  parsedImages = null;
                }
              }
              
              return {
                id: msg.id,
                content: msg.content,
                role: msg.role || (msg.sender === 'user' ? 'user' : 'assistant'),
                timestamp: new Date(msg.created_at),
                conversationId: msg.conversation_id,
                messageType: msg.message_type || 'text',
                attachments: msg.attachments ? JSON.parse(msg.attachments) : [],
                images: parsedImages,
                message_metadata: msg.message_metadata ? JSON.parse(msg.message_metadata) : null
              };
            });
            console.log('Formatted messages:', formattedMessages);
            setMessages(formattedMessages);
          } else {
            // Show welcome message for empty conversation
            setMessages([
              {
                id: '1',
                content: `Hello! I'm your AI travel assistant. How can I help you plan your next adventure?`,
                role: 'assistant',
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
              role: 'assistant',
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
        role: 'user',
        timestamp: new Date(),
      };

    console.log('Adding user message:', userMessage);
    // Add user message immediately to UI
    setMessages(prev => {
      const newMessages = [...prev, userMessage];
      console.log('Updated messages after adding user message:', newMessages);
      return newMessages;
    });
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
          last_message: response.content?.substring(0, 100) || inputMessage.substring(0, 100)
        };
        setCurrentConversation(newConversation);
      }
      
      // Check if we need to scrape images
      const needsImages = inputMessage.toLowerCase().includes('show') || 
                         inputMessage.toLowerCase().includes('image') ||
                         inputMessage.toLowerCase().includes('photo') ||
                         inputMessage.toLowerCase().includes('picture');
      
      let images = [];
      if (needsImages) {
        images = await scrapeImages(inputMessage);
      }

      const aiMessage: Message = {
        id: (Date.now() + 1).toString(),
        content: response.content || 'I received your message but couldn\'t generate a response.',
        role: 'assistant',
        timestamp: new Date(),
        conversationId: response.conversation_id ? parseInt(response.conversation_id) : undefined,
        messageType: images.length > 0 ? 'image' : 'text',
        attachments: images.map((img: any) => img.url), // Explicitly typed img as any
        message_metadata: { images } // Renamed from metadata
      };

      console.log('Adding AI message:', aiMessage);
      setMessages(prev => {
        const newMessages = [...prev, aiMessage];
        console.log('Updated messages after adding AI message:', newMessages);
        return newMessages;
      });
    } catch (error) {
      console.error('Failed to send message:', error);
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        content: 'Sorry, I encountered an error. Please try again.',
        role: 'assistant',
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

  // Calculate left position based on desktop sidebar state
  // Desktop sidebar: 56px collapsed, 280px expanded
  // Chat sidebar: always 280px
  const desktopSidebarWidth = isCollapsed ? 56 : 280;
  
  const chatPageLeft = `${desktopSidebarWidth}px`;
  const inputAreaLeft = `${desktopSidebarWidth + 280}px`; // desktop sidebar + chat sidebar

  return (
    <div className="grok-chat-page" style={{ left: chatPageLeft }}>
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
              messages.map((message) => {
                console.log('Rendering message:', message);
                return (
                  <div key={message.id} className={`message ${message.role === 'user' ? 'user-message' : 'ai-message'}`}>
                    {message.role === 'user' ? (
                      // User message on the right
                      <>
                        <div className="message-content">
                          <div className="message-text">{message.content || 'No content'}</div>
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
                        <div className="message-text">{message.content || 'No content'}</div>
                        
                        {/* Display RAG images if message has images */}
                        {message.images && message.images.length > 0 && (
                          <div className="mt-3">
                            <div className="mb-2 text-sm text-gray-600 font-medium">
                              📸 Images from your trips:
                            </div>
                            <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                              {message.images.map((image, index) => (
                                <div key={image.id} className="relative group">
                                  <img
                                    src={image.thumbnail_url}
                                    alt={image.title}
                                    className="w-full h-32 object-cover rounded-lg cursor-pointer hover:opacity-90 transition-opacity"
                                    onClick={() => window.open(image.url, '_blank')}
                                  />
                                  <div className="absolute inset-0 bg-black bg-opacity-0 group-hover:bg-opacity-30 transition-all duration-200 rounded-lg flex items-center justify-center">
                                    <div className="opacity-0 group-hover:opacity-100 text-white text-xs text-center p-2">
                                      <div className="font-medium">{image.place_name}</div>
                                      <div className="text-gray-200">{image.place_type}</div>
                                    </div>
                                  </div>
                                  <div className="absolute top-2 right-2 bg-black bg-opacity-50 text-white text-xs px-2 py-1 rounded">
                                    {index + 1}
                                  </div>
                                </div>
                              ))}
                            </div>
                          </div>
                        )}
                        
                        {/* Display legacy attachments if message has attachments */}
                        {message.attachments && message.attachments.length > 0 && (
                          <div className="mt-3 grid grid-cols-2 gap-2">
                            {message.attachments.map((url, index) => (
                              <div key={index} className="relative">
                                <img
                                  src={url}
                                  alt={`Image ${index + 1}`}
                                  className="w-full h-32 object-cover rounded-lg cursor-pointer hover:opacity-90 transition-opacity"
                                  onClick={() => window.open(url, '_blank')}
                                />
                                <div className="absolute top-2 right-2 bg-black bg-opacity-50 text-white text-xs px-2 py-1 rounded">
                                  {index + 1}
                                </div>
                              </div>
                            ))}
                          </div>
                        )}
                        
                        <div className="message-time">{formatTime(message.timestamp)}</div>
                      </div>
                    </>
                  )}
                </div>
                );
              })
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
        <div className="chat-input-area" style={{ left: inputAreaLeft }}>
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
      </div>

      {/* Delete Confirmation Modal */}
      {conversationToDelete && (
        <div className="modal-overlay" onClick={() => setConversationToDelete(null)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <div className="modal-icon">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M12 9V13M12 17H12.01M21 12C21 16.9706 16.9706 21 12 21C7.02944 21 3 16.9706 3 12C3 7.02944 7.02944 3 12 3C16.9706 3 21 7.02944 21 12Z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                </svg>
              </div>
              <h3>Delete Conversation</h3>
            </div>
            <div className="modal-body">
              <p>Are you sure you want to delete this conversation?</p>
              <p className="modal-warning">This action cannot be undone and all messages will be permanently removed.</p>
            </div>
            <div className="modal-actions">
              <button 
                className="btn-secondary" 
                onClick={() => setConversationToDelete(null)}
              >
                Cancel
              </button>
              <button 
                className="btn-danger" 
                onClick={() => handleDeleteConversation(conversationToDelete)}
              >
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M3 6H5H21M8 6V4C8 3.46957 8.21071 2.96086 8.58579 2.58579C8.96086 2.21071 9.46957 2 10 2H14C14.5304 2 15.0391 2.21071 15.4142 2.58579C15.7893 2.96086 16 3.46957 16 4V6M19 6V20C19 20.5304 18.7893 21.0391 18.4142 21.4142C18.0391 21.7893 17.5304 22 17 22H7C6.46957 22 5.96086 21.7893 5.58579 21.4142C5.21071 21.0391 5 20.5304 5 20V6H19Z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                </svg>
                Delete Conversation
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}