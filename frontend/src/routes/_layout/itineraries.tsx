import { createFileRoute } from '@tanstack/react-router';
import { FiCalendar, FiMapPin, FiClock, FiPlus, FiChevronLeft, FiChevronRight } from 'react-icons/fi';
import { useTravel } from '@/contexts/TravelContext';
import { Link } from '@tanstack/react-router';
import { useMemo, useState } from 'react';

export const Route = createFileRoute('/_layout/itineraries')({
  component: ItinerariesPage,
});

function ItinerariesPage() {
  const { trips, isLoadingTrips } = useTravel();
  const [currentIndex, setCurrentIndex] = useState(0);
  const [selectedItineraryIndex, setSelectedItineraryIndex] = useState(0);

  // Build virtual itineraries from trips that have ai_itinerary_data
  const tripItineraries = useMemo(() => {
    const source = Array.isArray(trips) ? trips : [] as any[];
    return source
      .filter((t: any) => !!t.ai_itinerary_data)
      .map((t: any) => {
        try {
          const parsed = JSON.parse(t.ai_itinerary_data);
          const inner = parsed.itinerary?.itinerary || parsed.itinerary || parsed;
          const overview = inner.overview;
          const days = inner.days || [];
          return { trip: t, overview, days };
        } catch (e) {
          return null;
        }
      })
      .filter(Boolean) as Array<{ trip: any; overview: any; days: any[] }>;
  }, [trips]);

  const goPrev = () => setCurrentIndex((i) => Math.max(0, i - 1));
  const goNext = () => setCurrentIndex((i) => Math.min((tripItineraries[selectedItineraryIndex]?.days?.length || 1) - 1, i + 1));

  const current = tripItineraries[selectedItineraryIndex];
  const currentDay = current?.days?.[currentIndex];

  return (
    <div className="itineraries-page">
      <div className="page-header">
        <div>
          <h1>Itineraries</h1>
          <p>Manage your travel plans and daily activities</p>
        </div>
        <Link to="/plan-trip" className="btn btn-primary">
          <FiPlus className="icon" />
          Create Itinerary
        </Link>
      </div>

      <div className="itineraries-content">
        {isLoadingTrips ? (
          <div className="loading">Loading itineraries...</div>
        ) : tripItineraries.length > 0 ? (
          <>
            {/* Itinerary Selector */}
            {tripItineraries.length > 1 && (
              <div className="itinerary-selector">
                {tripItineraries.map((it, idx) => (
                  <button
                    key={it.trip.id}
                    className={`itinerary-selector-btn ${idx === selectedItineraryIndex ? 'active' : ''}`}
                    onClick={() => {
                      setSelectedItineraryIndex(idx);
                      setCurrentIndex(0);
                    }}
                  >
                    {it.trip.title}
                  </button>
                ))}
              </div>
            )}

            {current ? (
              <div className="itinerary-view">
                <div className="itinerary-header">
                  <div className="itinerary-info">
                    <h3>{current.trip.title}</h3>
                    <p className="itinerary-destination">
                      <FiMapPin className="icon" />
                      {current.overview?.destination || current.trip.destination}
                    </p>
                  </div>
                  <div className="itinerary-day">
                    <button className="btn-icon" onClick={goPrev} disabled={currentIndex === 0} title="Prev day"><FiChevronLeft /></button>
                    <span className="day-number">Day {currentDay?.day || currentIndex + 1}</span>
                    <button className="btn-icon" onClick={goNext} disabled={currentIndex >= (current.days.length - 1)} title="Next day"><FiChevronRight /></button>
                  </div>
                </div>

                {currentDay ? (
                  <div className="itinerary-card">
                    <div className="itinerary-activities">
                      <h4>{currentDay.theme || 'Planned Activities'}</h4>
                      {Array.isArray(currentDay.activities) && currentDay.activities.length > 0 ? (
                        <ul className="activities-list">
                          {currentDay.activities.map((a: any, idx: number) => (
                            <li key={idx} className="activity-item">
                              <FiClock className="icon" />
                              <span>{`${a.time || ''} ${a.activity || a.title || ''} ${a.location ? '• ' + a.location : ''}`.trim()}</span>
                            </li>
                          ))}
                        </ul>
                      ) : (
                        <p className="no-activities">No activities for this day</p>
                      )}
                    </div>

                    <div className="itinerary-actions">
                      <Link to={`/trips/${current.trip.id}`} className="btn btn-outline btn-sm">
                        <FiMapPin className="icon" />
                        View Full Trip
                      </Link>
                    </div>
                  </div>
                ) : (
                  <p>No day selected.</p>
                )}
              </div>
            ) : (
              <div className="empty-state">
                <FiCalendar className="empty-icon" />
                <h3>No itinerary data available</h3>
              </div>
            )}
          </>
        ) : (
          <div className="empty-state">
            <FiCalendar className="empty-icon" />
            <h3>No itineraries yet</h3>
            <p>Create your first travel itinerary to get started!</p>
            <Link to="/plan-trip" className="btn btn-primary">Create Itinerary</Link>
          </div>
        )}
      </div>
    </div>
  );
}
