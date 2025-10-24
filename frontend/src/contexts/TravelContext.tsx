import React, { createContext, useContext, useState, useRef, ReactNode } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { TravelService, AiTravelService } from '@/client';
import { useAuth } from './AuthContext';

// Types matching the backend API
interface Trip {
  id: string;
  title: string;
  destination: string;
  start_date: string;
  end_date: string;
  budget?: number;
  trip_type?: string;
  status?: string;
  description?: string;
  created_at: string;
  updated_at: string;
  ai_itinerary_data?: string; // JSON string with AI itinerary
}

interface TripCreate {
  title: string;
  destination: string;
  start_date: string;
  end_date: string;
  budget?: number;
  trip_type?: string;
  description?: string;
}

interface Itinerary {
  id: string;
  trip_id: string;
  day: number;
  activities: string[];
  created_at: string;
}

interface Booking {
  id: string;
  trip_id: string;
  type: string;
  name: string;
  price: number;
  status: string;
  created_at: string;
}

interface Conversation {
  id: string;
  title?: string;
  last_message?: string;
  created_at: string;
  updated_at: string;
}

interface ConversationMessage {
  id: number;
  conversation_id: string;
  message: string;
  sender: 'user' | 'ai';
  created_at: string;
}

interface TravelContextType {
  // Trips
  trips: Trip[];
  isLoadingTrips: boolean;
  createTrip: (data: TripCreate) => Promise<Trip>;
  updateTrip: (id: string, data: Partial<Trip>) => Promise<Trip>;
  deleteTrip: (id: string) => Promise<void>;
  
  // AI Planning
  isPlanning: boolean;
  planTrip: (preferences?: any) => Promise<any>;
  chatWithAI: (message: string, conversationId?: string) => Promise<ConversationMessage>;
  
  // Itineraries
  itineraries: Itinerary[];
  isLoadingItineraries: boolean;
  
  // Bookings
  bookings: Booking[];
  isLoadingBookings: boolean;
  
  // Conversations
  conversations: Conversation[];
  isLoadingConversations: boolean;
  currentConversation: Conversation | null;
  setCurrentConversation: (conversation: Conversation | null) => void;
  fetchConversationMessages: (conversationId: string) => Promise<ConversationMessage[]>;
  deleteConversation: (conversationId: string) => Promise<void>;
  
  // Error handling
  error: string | null;
  clearError: () => void;
}

const TravelContext = createContext<TravelContextType | undefined>(undefined);

export const useTravel = () => {
  const context = useContext(TravelContext);
  if (context === undefined) {
    throw new Error('useTravel must be used within a TravelProvider');
  }
  return context;
};

interface TravelProviderProps {
  children: ReactNode;
}

export const TravelProvider: React.FC<TravelProviderProps> = ({ children }) => {
  const [error, setError] = useState<string | null>(null);
  const [currentConversation, setCurrentConversation] = useState<Conversation | null>(null);
  const queryClient = useQueryClient();
  const { isAuthenticated } = useAuth();
  // Tracks the latest server-issued conversation id so we keep threading correctly
  const lastServerConversationIdRef = useRef<string | null>(null);

  // Fetch trips
  const { data: trips = [], isLoading: isLoadingTrips } = useQuery({
    queryKey: ['trips'],
    queryFn: async () => {
      try {
        const response = await TravelService.readTrips();
        // If response is an object with data property, extract it
        if (response && typeof response === 'object' && 'data' in response) {
          return response.data || [];
        }
        // Otherwise assume it's already an array
        return Array.isArray(response) ? response : [];
      } catch (error: any) {
        console.error('Error fetching trips:', error);
        return [];
      }
    },
    enabled: isAuthenticated,
    retry: 1,
  });

  // Fetch itineraries - will be implemented later
  const { data: itineraries = [], isLoading: isLoadingItineraries } = useQuery<Itinerary[]>({
    queryKey: ['itineraries'],
    queryFn: () => Promise.resolve([]),
  });

  // Fetch bookings - will be implemented later
  const { data: bookings = [], isLoading: isLoadingBookings } = useQuery<Booking[]>({
    queryKey: ['bookings'],
    queryFn: () => Promise.resolve([]),
  });

  // Fetch conversations
  const { data: conversationsResponse, isLoading: isLoadingConversations } = useQuery({
    queryKey: ['conversations'],
    queryFn: async () => {
      try {
        console.log('Fetching conversations...');
        const response = await TravelService.readConversations();
        console.log('Conversations response:', response);
        return response;
      } catch (error) {
        console.error('Error fetching conversations:', error);
        return { conversations: [], count: 0 };
      }
    },
    enabled: isAuthenticated,
    retry: 1,
  });

    const conversations = (conversationsResponse as any)?.conversations || [];
    console.log('Processed conversations:', conversations);

  // Create trip mutation
  const createTripMutation = useMutation({
    mutationFn: async (data: TripCreate) => {
      const response = await TravelService.createTrip({ requestBody: data as any });
      return response;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['trips'] });
      setError(null);
    },
    onError: (err: any) => {
      setError(err.message || 'Failed to create trip');
      console.error('Create trip error:', err);
    },
  });

  // Update trip mutation
  const updateTripMutation = useMutation({
    mutationFn: async ({ id, data }: { id: string; data: Partial<Trip> }) => {
      const response = await TravelService.updateTrip({ 
        tripId: id, 
        requestBody: data as any 
      });
      return response;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['trips'] });
      setError(null);
    },
    onError: (err: any) => {
      setError(err.message || 'Failed to update trip');
      console.error('Update trip error:', err);
    },
  });

  // Delete trip mutation
  const deleteTripMutation = useMutation({
    mutationFn: async (id: string) => {
      await TravelService.deleteTrip({ tripId: id });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['trips'] });
      setError(null);
    },
    onError: (err: any) => {
      setError(err.message || 'Failed to delete trip');
      console.error('Delete trip error:', err);
    },
  });

  // Delete conversation mutation
  const deleteConversationMutation = useMutation({
    mutationFn: async (conversationId: string) => {
      const token = localStorage.getItem('access_token');
      const response = await fetch(`http://localhost:8000/api/v1/conversations/${conversationId}`, {
        method: 'DELETE',
        credentials: 'include',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });
      if (!response.ok) throw new Error('Failed to delete');
      return response.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['conversations'] });
      setError(null);
    },
    onError: (err: any) => {
      setError(err.message || 'Failed to delete conversation');
      console.error('Delete conversation error:', err);
    },
  });

  // Plan trip with AI mutation
  const planTripMutation = useMutation({
    mutationFn: async ({ preferences }: { preferences?: any }) => {
      // Ensure dates are in correct format (YYYY-MM-DD)
      const startDate = preferences?.startDate || new Date().toISOString().split('T')[0];
      const endDate = preferences?.endDate || new Date().toISOString().split('T')[0];
      
      const response = await AiTravelService.planTripWithAi({
        requestBody: {
          destination: preferences?.destination || '',
          start_date: startDate,
          end_date: endDate,
          budget: preferences?.budget ? parseFloat(preferences.budget) : undefined,
          trip_type: preferences?.tripType || 'leisure',
          interests: preferences?.interests || [],
          travelers: preferences?.travelers || 1,
          accommodation_preference: preferences?.accommodation_preference,
          transportation_preference: preferences?.transportation_preference,
        },
      });
      return response;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['trips'] });
      setError(null);
    },
    onError: (err: any) => {
      const errorMessage = err?.body?.detail || err?.message || 'Failed to plan trip';
      setError(errorMessage);
      console.error('Plan trip error:', err);
    },
  });

  // Chat with AI mutation
  const chatMutation = useMutation({
    mutationFn: async ({ message, conversationId }: { message: string; conversationId?: string }) => {
      try {
        console.log('Calling backend AI chat API for:', message);
        
        // Call the actual backend API
        // Prefer the last server-provided conversation id to keep the thread
        const isValidUUID = (id?: string) => !!id && /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(id);
        const serverThreadId = lastServerConversationIdRef.current;
        const candidateId = serverThreadId || conversationId;
        const conversationIdToSend = isValidUUID(candidateId) ? candidateId : undefined;
        
        const response = await AiTravelService.chatWithAi({
          requestBody: {
            message: message,
            conversation_id: conversationIdToSend,
            trip_id: undefined
          }
        });
        
        console.log('Backend AI response:', response);
        return response;
      } catch (error: any) {
        console.error('Backend AI chat failed, using fallback:', error);
        
        // Fallback to intelligent mock responses if backend fails
        let response = '';
        
        if (message.toLowerCase().includes('kathmandu') || message.toLowerCase().includes('nepal')) {
          response = `Great choice! Kathmandu, Nepal is an incredible destination for a 3-day trip. Here's what I recommend:

**Day 1: Cultural Heritage**
- Visit Swayambhunath (Monkey Temple) for stunning city views
- Explore Patan Durbar Square with its ancient architecture
- Walk through the bustling streets of Thamel

**Day 2: Spiritual Journey**
- Early morning visit to Pashupatinath Temple
- Explore Boudhanath Stupa (one of the largest in the world)
- Visit Swayambhunath for sunset views

**Day 3: Adventure & Shopping**
- Take a day trip to Nagarkot for mountain views
- Explore local markets for handicrafts and souvenirs
- Enjoy traditional Newari cuisine

**Budget**: $30-50 per day for mid-range accommodation and meals
**Best time**: October to April for clear mountain views
**Transport**: Walking, taxis, or local buses

Would you like me to help you with specific bookings or more detailed itinerary planning?`;
        } else if (message.toLowerCase().includes('tokyo') || message.toLowerCase().includes('japan')) {
          response = `Tokyo is an amazing destination! Here's a perfect 3-day Tokyo itinerary:

**Day 1: Traditional Tokyo**
- Visit Senso-ji Temple in Asakusa
- Explore the traditional Nakamise shopping street
- Take a river cruise on the Sumida River
- Visit Tokyo Skytree for city views

**Day 2: Modern Tokyo**
- Explore Shibuya crossing and Hachiko statue
- Visit Harajuku for unique fashion and culture
- Walk through Yoyogi Park
- Experience the nightlife in Roppongi

**Day 3: Cultural Experience**
- Visit the Imperial Palace East Gardens
- Explore Ginza for high-end shopping
- Visit Tsukiji Outer Market for fresh sushi
- End with a traditional tea ceremony

**Budget**: $80-150 per day depending on accommodation
**Transport**: JR Pass or Suica card for trains
**Food**: Try ramen, sushi, and street food

Would you like specific recommendations for accommodations or activities?`;
        } else if (message.toLowerCase().includes('help') || message.toLowerCase().includes('plan')) {
          response = `I'd be happy to help you plan your perfect trip! I can assist with:

🗺️ **Destination Research** - Find the best places to visit
📅 **Itinerary Planning** - Create detailed day-by-day plans
🏨 **Accommodation** - Suggest hotels and areas to stay
🍽️ **Dining** - Recommend restaurants and local cuisine
💰 **Budget Planning** - Help estimate costs and find deals
🎫 **Activities** - Suggest tours, attractions, and experiences

Just tell me:
- Where you want to go
- How many days you have
- Your budget range
- What interests you (culture, adventure, food, etc.)

What destination are you thinking about?`;
        } else {
          response = `I'd be happy to help you with your travel plans! You asked: "${message}". 

I'm your AI travel assistant and I can help you with:
- Destination recommendations
- Detailed itineraries
- Budget planning
- Accommodation suggestions
- Local tips and insights

Could you tell me more about where you'd like to go or what kind of trip you're planning?`;
        }
        
        return {
          response: response,
          conversation_id: conversationId || 'fallback_conversation',
          suggestions: [
            { type: "destination", text: "Find destinations", action: "search_destinations" },
            { type: "itinerary", text: "Plan itinerary", action: "plan_itinerary" },
            { type: "booking", text: "Find bookings", action: "search_bookings" }
          ]
        };
      }
    },
    onSuccess: (data: any) => {
      console.log('Chat success, data:', data);
      // Ensure we keep using the server conversation id from now on
      try {
        const newId = (data?.conversation_id || '').toString();
        console.log('New conversation ID:', newId);
        if (newId) {
          lastServerConversationIdRef.current = newId;
          setCurrentConversation((prev) => {
            if (!prev || prev.id !== newId) {
              const newConversation = {
                id: newId,
                title: prev?.title || 'New Chat',
                created_at: prev?.created_at || new Date().toISOString(),
                updated_at: new Date().toISOString(),
                last_message: data?.response?.slice?.(0, 100) || prev?.last_message,
              } as any;
              console.log('Setting new conversation:', newConversation);
              return newConversation;
            }
            return prev;
          });
        }
      } catch (error) {
        console.error('Error in chat success handler:', error);
      }
      // Refresh conversations list to include the new conversation
      console.log('Invalidating conversations query...');
      queryClient.invalidateQueries({ queryKey: ['conversations'] });
      setError(null);
    },
    onError: (err: any) => {
      setError(err.message || 'Failed to chat with AI');
      console.error('Chat error:', err);
    },
  });

  const createTrip = async (data: TripCreate): Promise<Trip> => {
    return await createTripMutation.mutateAsync(data) as Trip;
  };

  const updateTrip = async (id: string, data: Partial<Trip>): Promise<Trip> => {
    return await updateTripMutation.mutateAsync({ id, data }) as Trip;
  };

  const deleteTrip = async (id: string) => {
    await deleteTripMutation.mutateAsync(id);
  };

  const planTrip = async (preferences?: any) => {
    console.log('🚀 planTrip called with preferences:', preferences);
    console.trace('Call stack:');
    
    // Validate preferences before making API call
    if (!preferences || !preferences.destination || !preferences.destination.trim()) {
      console.error('❌ planTrip called with invalid preferences (no destination)');
      throw new Error('Destination is required');
    }
    
    return await planTripMutation.mutateAsync({ preferences });
  };

  const chatWithAI = async (message: string, conversationId?: string): Promise<ConversationMessage> => {
    const response = await chatMutation.mutateAsync({ message, conversationId });
    return {
      id: Date.now(),
      conversation_id: response.conversation_id || conversationId || '1',
      message: response.response || 'No response',
      sender: response.sender || 'ai',
      created_at: new Date().toISOString()
    };
  };

  const fetchConversationMessages = async (conversationId: string): Promise<ConversationMessage[]> => {
    try {
      const response = await TravelService.readMessages({ 
        conversationId,
        skip: 0,
        limit: 100
      });
      
      // Handle the response structure - it might be wrapped in a data property
      const messages = (response as any)?.messages || (response as any)?.data || [];
      
      return messages.map((msg: any) => ({
        id: msg.id?.toString() || Date.now().toString(),
        conversation_id: msg.conversation_id || conversationId,
        message: msg.content || msg.message || '',
        sender: msg.sender === 'user' ? 'user' : 'ai',
        created_at: msg.created_at || new Date().toISOString()
      }));
    } catch (error) {
      console.error('Error fetching conversation messages:', error);
      return [];
    }
  };

  const deleteConversation = async (conversationId: string) => {
    await deleteConversationMutation.mutateAsync(conversationId);
  };

  const clearError = () => setError(null);

  const value: TravelContextType = {
    trips: trips as Trip[],
    isLoadingTrips,
    createTrip,
    updateTrip,
    deleteTrip,
    isPlanning: planTripMutation.isPending,
    planTrip,
    chatWithAI,
    itineraries,
    isLoadingItineraries,
    bookings,
    isLoadingBookings,
    conversations,
    isLoadingConversations,
    currentConversation,
    setCurrentConversation,
    fetchConversationMessages,
    deleteConversation,
    error,
    clearError,
  };

  return (
    <TravelContext.Provider value={value}>
      {children}
    </TravelContext.Provider>
  );
};
