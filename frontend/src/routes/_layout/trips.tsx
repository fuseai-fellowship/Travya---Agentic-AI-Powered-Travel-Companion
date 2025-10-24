import { useState } from 'react';
import { createFileRoute, useNavigate, Link, Outlet } from '@tanstack/react-router';
import { FiMapPin, FiCalendar, FiDollarSign, FiPlus, FiEdit, FiTrash2, FiEye, FiUsers } from 'react-icons/fi';
import { useTravel } from '@/contexts/TravelContext';

export const Route = createFileRoute('/_layout/trips')({
  component: TripsPage,
});

function TripsPage() {
  const { trips, isLoadingTrips, deleteTrip } = useTravel();
  const navigate = useNavigate();
  const [filter, setFilter] = useState<'all' | 'planning' | 'confirmed' | 'completed' | 'draft'>('all');

  const filteredTrips = Array.isArray(trips) ? trips.filter(trip => {
    if (filter === 'all') return true;
    return trip.status?.toLowerCase() === filter;
  }) : [];

  const getStatusColor = (status: string) => {
    switch (status?.toLowerCase()) {
      case 'confirmed': return '#22C55E';
      case 'planning': return '#3B82F6';
      case 'draft': return '#6B7280';
      case 'in_progress': return '#8B5CF6';
      case 'completed': return '#14B8A6';
      case 'cancelled': return '#EF4444';
      default: return '#6B7280';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status?.toLowerCase()) {
      case 'confirmed': return '✓';
      case 'planning': return '⏳';
      case 'completed': return '✅';
      case 'draft': return '📝';
      default: return '📝';
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric'
    });
  };

  const calculateDuration = (startDate: string, endDate: string) => {
    const start = new Date(startDate);
    const end = new Date(endDate);
    const diffTime = Math.abs(end.getTime() - start.getTime());
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    return diffDays;
  };

  const handleDeleteTrip = async (id: string, e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (window.confirm('Are you sure you want to delete this trip?')) {
      try {
        await deleteTrip(id);
      } catch (error) {
        console.error('Failed to delete trip:', error);
      }
    }
  };

  const filterTabs = [
    { key: 'all', label: 'All Trips', count: trips?.length || 0 },
    { key: 'planning', label: 'Planning', count: trips?.filter(t => t.status?.toLowerCase() === 'planning').length || 0 },
    { key: 'confirmed', label: 'Confirmed', count: trips?.filter(t => t.status?.toLowerCase() === 'confirmed').length || 0 },
    { key: 'completed', label: 'Completed', count: trips?.filter(t => t.status?.toLowerCase() === 'completed').length || 0 },
    { key: 'draft', label: 'Draft', count: trips?.filter(t => t.status?.toLowerCase() === 'draft').length || 0 },
  ];

  return (
    <div className="trips-page">
      <Outlet />
      <div className="page-header">
        <div>
          <h1>My Trips</h1>
          <p>Manage and plan your travel adventures</p>
        </div>
        <Link to="/plan-trip" className="btn btn-primary">
          <FiPlus className="icon" />
          Plan New Trip
        </Link>
      </div>

      <div className="trips-filters">
        <div className="filter-tabs">
          {filterTabs.map((tab) => (
            <button
              key={tab.key}
              className={`filter-tab ${filter === tab.key ? 'active' : ''}`}
              onClick={() => setFilter(tab.key as any)}
            >
              {tab.label}
              <span className="tab-count">{tab.count}</span>
            </button>
          ))}
        </div>
      </div>

      <div className="trips-content">
        {isLoadingTrips ? (
          <div className="loading">Loading trips...</div>
        ) : filteredTrips.length > 0 ? (
          <div className="trips-grid">
            {filteredTrips.map((trip) => (
              <div key={trip.id} className="trip-card">
                <div className="trip-image">
                  <img
                    src={`https://images.unsplash.com/photo-1502602898536-47ad22581b52?w=400&h=200&fit=crop&q=80`}
                    alt={trip.title}
                  />
                  <span 
                    className="trip-status-badge"
                    style={{ backgroundColor: getStatusColor(trip.status || 'draft') }}
                  >
                    <span className="status-icon">{getStatusIcon(trip.status || 'draft')}</span>
                    {trip.status || 'Draft'}
                  </span>
                </div>

                <div className="trip-content">
                  <div className="trip-header">
                    <h3>{trip.title}</h3>
                    <div className="trip-actions">
                      <button 
                        className="btn-icon" 
                        title="View Details"
                        onClick={(e) => {
                          e.preventDefault();
                          e.stopPropagation();
                          console.log('👁️ Eye icon clicked for trip:', trip.id);
                          console.log('🔗 Navigating to:', `/trips/${trip.id}`);
                          navigate({ to: '/trips/$tripId', params: { tripId: String(trip.id) } });
                        }}
                      >
                        <FiEye />
                      </button>
                      <button 
                        className="btn-icon" 
                        title="Edit Trip"
                        onClick={(e) => {
                          e.preventDefault();
                          e.stopPropagation();
                          console.log('✏️ Edit icon clicked for trip:', trip.id);
                          navigate({ to: '/trips/$tripId', params: { tripId: String(trip.id) } });
                        }}
                      >
                        <FiEdit />
                      </button>
                      <button 
                        className="btn-icon btn-danger" 
                        title="Delete Trip"
                        onClick={(e) => handleDeleteTrip(String(trip.id), e)}
                      >
                        <FiTrash2 />
                      </button>
                    </div>
                  </div>

                  <div className="trip-destination">
                    <FiMapPin className="icon" />
                    <span>{trip.destination}</span>
                  </div>
                  
                  <p className="trip-description">{trip.description}</p>

                  <div className="trip-dates">
                    <FiCalendar className="icon" />
                    <span>
                      {formatDate(trip.start_date)} - {formatDate(trip.end_date)}
                    </span>
                  </div>

                  <div className="trip-meta">
                    <div className="trip-budget">
                      <FiDollarSign className="icon" />
                      <span>${trip.budget?.toLocaleString() || '0'}</span>
                    </div>
                    <div className="trip-type">
                      <FiUsers className="icon" />
                      <span style={{ textTransform: 'capitalize' }}>{trip.trip_type || 'Leisure'}</span>
                    </div>
                    <div className="trip-duration">
                      <span>{calculateDuration(trip.start_date, trip.end_date)} days</span>
                    </div>
                  </div>

                  <div className="trip-progress">
                    <div className="progress-bar">
                      <div 
                        className="progress-fill" 
                        style={{ 
                          width: trip.status === 'completed' ? '100%' : 
                                 trip.status === 'confirmed' ? '75%' : 
                                 trip.status === 'planning' ? '50%' : '25%' 
                        }}
                      ></div>
                    </div>
                    <span className="progress-text">
                      {trip.status === 'completed' ? 'Completed' : 
                       trip.status === 'confirmed' ? 'Ready to go' : 
                       trip.status === 'planning' ? 'In progress' : 'Draft'}
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="empty-state">
            <FiMapPin className="empty-icon" />
            <h3>No trips found</h3>
            <p>
              {filter === 'all' 
                ? "You haven't created any trips yet. Start planning your first adventure!"
                : `No ${filter} trips found. Try a different filter or create a new trip.`
              }
            </p>
            <Link to="/plan-trip" className="btn btn-primary">Plan Your First Trip</Link>
          </div>
        )}
      </div>
    </div>
  );
}