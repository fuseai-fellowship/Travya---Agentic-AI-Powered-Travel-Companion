import { createFileRoute } from '@tanstack/react-router';
import { useAuth } from '@/contexts/AuthContext';
import { useTravel } from '@/contexts/TravelContext';
import { Link } from '@tanstack/react-router';
import { FiPlus, FiMapPin, FiCalendar, FiMessageCircle, FiTrendingUp, FiDollarSign, FiUsers } from 'react-icons/fi';

export const Route = createFileRoute('/_layout/')({
  component: Index,
});

function Index() {
  const { user } = useAuth();
  const { trips, isLoadingTrips, conversations, isLoadingConversations } = useTravel();

  // Safely handle data with proper checks
  const recentTrips = Array.isArray(trips) ? trips.slice(0, 3) : [];
  const recentConversations = Array.isArray(conversations) ? conversations.slice(0, 3) : [];

  const stats = [
    {
      title: 'Total Trips',
      value: Array.isArray(trips) ? trips.length : 0,
      icon: FiMapPin,
      color: 'blue',
      subtitle: Array.isArray(trips) ? `${trips.filter(trip => {
        try {
          const tripDate = new Date(trip.created_at);
          const now = new Date();
          return tripDate.getMonth() === now.getMonth() && tripDate.getFullYear() === now.getFullYear();
        } catch {
          return false;
        }
      }).length} this month` : '0 this month',
    },
    {
      title: 'Active Conversations',
      value: Array.isArray(conversations) ? conversations.length : 0,
      icon: FiMessageCircle,
      color: 'green',
      subtitle: 'With AI assistant',
    },
    {
      title: 'Countries Visited',
      value: Array.isArray(trips) ? new Set(trips.map(trip => {
        try {
          return trip.destination?.split(',')[1]?.trim();
        } catch {
          return null;
        }
      }).filter(Boolean)).size : 0,
      icon: FiTrendingUp,
      color: 'purple',
      subtitle: 'Unique destinations',
    },
    {
      title: 'Total Budget',
      value: Array.isArray(trips) ? trips.reduce((sum, trip) => {
        try {
          return sum + (trip.budget || 0);
        } catch {
          return sum;
        }
      }, 0) : 0,
      icon: FiDollarSign,
      color: 'orange',
      subtitle: 'Across all trips',
    },
  ];

  const quickActions = [
    {
      title: 'Plan New Trip',
      description: 'Create a personalized itinerary with AI',
      icon: FiPlus,
      color: 'blue',
      path: '/plan-trip',
    },
    {
      title: 'AI Chat',
      description: 'Get travel advice and recommendations',
      icon: FiMessageCircle,
      color: 'green',
      path: '/chat',
    },
    {
      title: 'My Trips',
      description: 'View and manage your trips',
      icon: FiMapPin,
      color: 'purple',
      path: '/trips',
    },
    {
      title: 'Itineraries',
      description: 'Browse your travel plans',
      icon: FiCalendar,
      color: 'orange',
      path: '/itineraries',
    },
  ];

  const getStatusColor = (status: string) => {
    switch (status?.toLowerCase()) {
      case 'confirmed': return 'status-confirmed';
      case 'planning': return 'status-planning';
      case 'draft': return 'status-draft';
      case 'completed': return 'status-completed';
      default: return 'status-draft';
    }
  };

  return (
    <div className="dashboard">
      <div className="dashboard-header">
        <div>
          <h1>Welcome back, {user?.email?.split('@')[0] || 'Traveler'}! 👋</h1>
          <p>Ready to plan your next adventure? Let's make it amazing!</p>
        </div>
        <Link to="/plan-trip" className="btn btn-primary">
          <FiPlus className="icon" />
          Plan New Trip
        </Link>
      </div>

      <div className="stats-grid">
        {stats.map((stat, index) => (
          <div key={index} className={`stat-card stat-${stat.color}`}>
            <div className="stat-icon">
              <stat.icon />
            </div>
            <div className="stat-content">
              <h3>{stat.value.toLocaleString()}</h3>
              <p>{stat.title}</p>
              <span className="stat-subtitle">{stat.subtitle}</span>
            </div>
          </div>
        ))}
      </div>

      <div className="quick-actions">
        <h2>Quick Actions</h2>
        <div className="actions-grid">
          {quickActions.map((action, index) => (
            <Link key={index} to={action.path} className={`action-card action-${action.color}`}>
              <div className="action-icon">
                <action.icon />
              </div>
              <div className="action-content">
                <h3>{action.title}</h3>
                <p>{action.description}</p>
              </div>
            </Link>
          ))}
        </div>
      </div>

      <div className="dashboard-content">
        <div className="content-section">
          <div className="section-header">
            <h2>Recent Trips</h2>
            <Link to="/trips" className="btn btn-outline">View All</Link>
          </div>
          <div className="trips-grid">
            {isLoadingTrips ? (
              <div className="loading">Loading trips...</div>
            ) : recentTrips.length > 0 ? (
              recentTrips.map((trip) => (
                <Link key={trip.id} to={`/trips/${trip.id}`} className="trip-card">
                  <div className="trip-header">
                    <h3>{trip.title || 'Untitled Trip'}</h3>
                    <span className={`trip-status ${getStatusColor(trip.status || 'draft')}`}>
                      {trip.status || 'Draft'}
                    </span>
                  </div>
                  <p className="trip-destination">{trip.destination || 'No destination'}</p>
                  <div className="trip-dates">
                    <FiCalendar className="icon" />
                    <span>
                      {trip.start_date ? new Date(trip.start_date).toLocaleDateString() : 'No start date'} - {trip.end_date ? new Date(trip.end_date).toLocaleDateString() : 'No end date'}
                    </span>
                  </div>
                  {trip.budget && (
                    <div className="trip-budget">
                      <FiDollarSign className="icon" />
                      <span>${trip.budget.toLocaleString()}</span>
                    </div>
                  )}
                </Link>
              ))
            ) : (
              <div className="empty-state">
                <FiMapPin className="empty-icon" />
                <h3>No trips yet</h3>
                <p>Start planning your first adventure!</p>
                <Link to="/plan-trip" className="btn btn-primary">Plan Trip</Link>
              </div>
            )}
          </div>
        </div>

        <div className="content-section">
          <div className="section-header">
            <h2>Recent Conversations</h2>
            <Link to="/chat" className="btn btn-outline">View All</Link>
          </div>
          <div className="conversations-list">
            {isLoadingConversations ? (
              <div className="loading">Loading conversations...</div>
            ) : recentConversations.length > 0 ? (
              recentConversations.map((conversation) => (
                <Link key={conversation.id} to="/chat" className="conversation-item">
                  <div className="conversation-icon">
                    <FiMessageCircle />
                  </div>
                  <div className="conversation-content">
                    <h4>{conversation.title || 'Travel Chat'}</h4>
                    <p>{conversation.last_message || 'Start a conversation...'}</p>
                  </div>
                  <div className="conversation-time">
                    {conversation.updated_at ? new Date(conversation.updated_at).toLocaleDateString() : ''}
                  </div>
                </Link>
              ))
            ) : (
              <div className="empty-state">
                <FiMessageCircle className="empty-icon" />
                <h3>No conversations yet</h3>
                <p>Start chatting with your AI travel assistant!</p>
                <Link to="/chat" className="btn btn-primary">Start Chat</Link>
              </div>
            )}
          </div>
        </div>

        <div className="content-section">
          <div className="section-header">
            <h2>AI Insights</h2>
          </div>
          <div className="insights-grid">
            <div className="insight-card insight-blue">
              <div className="insight-icon">
                <FiTrendingUp />
              </div>
              <div className="insight-content">
                <h4>Savings Alert</h4>
                <p>You've saved $1,200 this year using our AI recommendations!</p>
              </div>
            </div>
            <div className="insight-card insight-green">
              <div className="insight-icon">
                <FiUsers />
              </div>
              <div className="insight-content">
                <h4>Travel Tip</h4>
                <p>Spring is the best time to visit Japan for cherry blossoms!</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}