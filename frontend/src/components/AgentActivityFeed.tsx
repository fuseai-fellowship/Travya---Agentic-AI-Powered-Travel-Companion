import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  FiCpu, 
  FiSearch, 
  FiMap, 
  FiShoppingBag,
  FiCheckCircle,
  FiClock,
  FiActivity,
  FiZap,
  FiLoader
} from 'react-icons/fi';

interface AgentEvent {
  id: string;
  timestamp: string;
  agent_type: string;
  agent_name: string;
  event_type: 'start' | 'thinking' | 'tool_call' | 'result' | 'complete' | 'error';
  message: string;
  data?: any;
  confidence?: number;
}

interface Props {
  sessionId?: string;
  isActive: boolean;
}

const getAgentIcon = (agentType: string) => {
  switch (agentType) {
    case 'research':
      return <FiSearch className="w-5 h-5" />;
    case 'planner':
      return <FiMap className="w-5 h-5" />;
    case 'booker':
      return <FiShoppingBag className="w-5 h-5" />;
    case 'orchestrator':
      return <FiCpu className="w-5 h-5" />;
    default:
      return <FiActivity className="w-5 h-5" />;
  }
};

const getAgentColor = (agentType: string) => {
  switch (agentType) {
    case 'research':
      return 'bg-blue-500';
    case 'planner':
      return 'bg-green-500';
    case 'booker':
      return 'bg-purple-500';
    case 'orchestrator':
      return 'bg-orange-500';
    default:
      return 'bg-gray-500';
  }
};

const getEventIcon = (eventType: string) => {
  switch (eventType) {
    case 'start':
      return <FiZap className="w-4 h-4" />;
    case 'thinking':
      return <FiActivity className="w-4 h-4" />;
    case 'tool_call':
      return <FiCpu className="w-4 h-4" />;
    case 'result':
      return <FiCheckCircle className="w-4 h-4" />;
    case 'complete':
      return <FiCheckCircle className="w-4 h-4" />;
    case 'error':
      return <FiActivity className="w-4 h-4" />;
    default:
      return <FiClock className="w-4 h-4" />;
  }
};

export default function AgentActivityFeed({ sessionId, isActive }: Props) {
  const [events, setEvents] = useState<AgentEvent[]>([]);
  const [isConnected, setIsConnected] = useState(false);
  const [activeAgents, setActiveAgents] = useState<Set<string>>(new Set());

  useEffect(() => {
    if (!isActive || !sessionId) {
      return;
    }

    // Connect to SSE endpoint
    const eventSource = new EventSource(
      `http://localhost:8000/api/v1/ai-travel/agent-stream/${sessionId}`
    );

    eventSource.onopen = () => {
      console.log('✅ SSE connection established');
      setIsConnected(true);
    };

    eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        console.log('📨 Received agent event:', data);
        
        const agentEvent: AgentEvent = {
          id: `${Date.now()}-${Math.random()}`,
          timestamp: new Date().toISOString(),
          agent_type: data.agent_type || 'unknown',
          agent_name: data.agent_name || 'Agent',
          event_type: data.event_type || 'thinking',
          message: data.message || '',
          data: data.data,
          confidence: data.confidence
        };

        setEvents((prev) => [...prev, agentEvent]);

        // Track active agents
        if (data.event_type === 'start') {
          setActiveAgents((prev) => new Set([...prev, data.agent_type]));
        } else if (data.event_type === 'complete' || data.event_type === 'error') {
          setActiveAgents((prev) => {
            const newSet = new Set(prev);
            newSet.delete(data.agent_type);
            return newSet;
          });
        }
      } catch (error) {
        console.error('Error parsing SSE event:', error);
      }
    };

    eventSource.onerror = (error) => {
      console.error('❌ SSE connection error:', error);
      setIsConnected(false);
      eventSource.close();
    };

    // Cleanup
    return () => {
      console.log('🔌 Closing SSE connection');
      eventSource.close();
      setIsConnected(false);
    };
  }, [sessionId, isActive]);

  if (!isActive) {
    return null;
  }

  return (
    <div className="bg-white rounded-xl shadow-lg border border-gray-200 overflow-hidden">
      {/* Header */}
      <div className="bg-gradient-to-r from-indigo-600 to-purple-600 text-white p-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <FiCpu className="w-6 h-6" />
            <h3 className="text-xl font-bold">AI Agents at Work</h3>
          </div>
          <div className="flex items-center gap-2">
            {isConnected ? (
              <span className="flex items-center gap-1 text-sm bg-green-500/30 px-3 py-1 rounded-full">
                <div className="w-2 h-2 bg-green-300 rounded-full animate-pulse"></div>
                Connected
              </span>
            ) : (
              <span className="flex items-center gap-1 text-sm bg-red-500/30 px-3 py-1 rounded-full">
                <div className="w-2 h-2 bg-red-300 rounded-full"></div>
                Disconnected
              </span>
            )}
          </div>
        </div>

        {/* Active Agents */}
        {activeAgents.size > 0 && (
          <div className="mt-3 flex flex-wrap gap-2">
            {Array.from(activeAgents).map((agent) => (
              <motion.div
                key={agent}
                initial={{ scale: 0 }}
                animate={{ scale: 1 }}
                exit={{ scale: 0 }}
                className={`${getAgentColor(agent)} text-white px-3 py-1 rounded-full text-sm flex items-center gap-2`}
              >
                {getAgentIcon(agent)}
                <span className="capitalize">{agent}</span>
                <FiLoader className="w-3 h-3 animate-spin" />
              </motion.div>
            ))}
          </div>
        )}
      </div>

      {/* Events Feed */}
      <div className="p-4 max-h-[500px] overflow-y-auto">
        {events.length === 0 ? (
          <div className="text-center text-gray-500 py-8">
            <FiClock className="w-12 h-12 mx-auto mb-3 opacity-30" />
            <p>Waiting for agents to start working...</p>
          </div>
        ) : (
          <AnimatePresence>
            <div className="space-y-3">
              {events.map((event, index) => (
                <motion.div
                  key={event.id}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: 20 }}
                  transition={{ delay: index * 0.05 }}
                  className="flex gap-3"
                >
                  {/* Agent Icon */}
                  <div className={`${getAgentColor(event.agent_type)} text-white p-2 rounded-full flex-shrink-0 h-10 w-10 flex items-center justify-center`}>
                    {getAgentIcon(event.agent_type)}
                  </div>

                  {/* Event Content */}
                  <div className="flex-1 bg-gray-50 rounded-lg p-3 border border-gray-200">
                    <div className="flex items-center justify-between mb-1">
                      <div className="flex items-center gap-2">
                        <span className="font-semibold text-gray-900 capitalize">
                          {event.agent_name}
                        </span>
                        <span className="text-xs text-gray-500 flex items-center gap-1">
                          {getEventIcon(event.event_type)}
                          {event.event_type}
                        </span>
                      </div>
                      <span className="text-xs text-gray-400">
                        {new Date(event.timestamp).toLocaleTimeString()}
                      </span>
                    </div>

                    <p className="text-sm text-gray-700">{event.message}</p>

                    {/* Tool Call Data */}
                    {event.event_type === 'tool_call' && event.data && (
                      <div className="mt-2 bg-blue-50 border border-blue-200 rounded p-2">
                        <p className="text-xs text-blue-800 font-mono">
                          🔧 Tool: {event.data.tool_name || 'Unknown'}
                        </p>
                        {event.data.parameters && (
                          <p className="text-xs text-blue-600 mt-1">
                            Params: {JSON.stringify(event.data.parameters)}
                          </p>
                        )}
                      </div>
                    )}

                    {/* Result Data */}
                    {event.event_type === 'result' && event.confidence !== undefined && (
                      <div className="mt-2">
                        <div className="flex items-center gap-2">
                          <span className="text-xs text-gray-600">Confidence:</span>
                          <div className="flex-1 bg-gray-200 rounded-full h-2">
                            <div
                              className="bg-green-500 h-2 rounded-full transition-all"
                              style={{ width: `${event.confidence * 100}%` }}
                            ></div>
                          </div>
                          <span className="text-xs text-gray-600">
                            {Math.round(event.confidence * 100)}%
                          </span>
                        </div>
                      </div>
                    )}

                    {/* Error Details */}
                    {event.event_type === 'error' && event.data && (
                      <div className="mt-2 bg-red-50 border border-red-200 rounded p-2">
                        <p className="text-xs text-red-800">
                          ⚠️ Error: {event.data.error_message || 'Unknown error'}
                        </p>
                      </div>
                    )}
                  </div>
                </motion.div>
              ))}
            </div>
          </AnimatePresence>
        )}
      </div>
    </div>
  );
}

