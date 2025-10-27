/* eslint-disable @typescript-eslint/no-unused-vars */
import { useState } from "react"
import { createFileRoute, useParams, useNavigate } from "@tanstack/react-router"
import { useQuery } from "@tanstack/react-query"
import { TravelService } from "@/client"
import { 
  FiMapPin, 
  FiCalendar, 
  FiDollarSign, 
  FiUsers, 
  FiEdit, 
  FiShare2, 
  FiDownload,
  FiNavigation,
  FiMessageCircle,
  FiPlus,
  FiX,
  FiLoader
} from "react-icons/fi"
import ItineraryDisplay from "@/components/ItineraryDisplay"
import PhotoGalleryComponent from "@/components/PhotoGallery"
import MapParserComponent from "@/components/MapParserComponent"

export const Route = createFileRoute("/_layout/trips/$tripId")({
  component: TripDetailsPage,
})

function TripDetailsPage() {
  const { tripId } = useParams({ from: "/_layout/trips/$tripId" })
  const navigate = useNavigate()
  const [activeTab, setActiveTab] = useState(0)
  const [showRaw, setShowRaw] = useState(false)

  console.log('🔍 TripDetailsPage loaded for tripId:', tripId);

  // Fetch real trip data from API
  const { data: trip, isLoading, error } = useQuery({
    queryKey: ['trip', tripId],
    queryFn: async () => {
      console.log('📡 Fetching trip data for:', tripId);
      const response = await TravelService.readTrip({ tripId });
      console.log('✅ Received trip data:', response);
      console.log('🗺️ AI Itinerary Data present?', !!(response as any).ai_itinerary_data);
      if ((response as any).ai_itinerary_data) {
        console.log('📦 AI Itinerary Data length:', (response as any).ai_itinerary_data.length);
        console.log('📦 AI Itinerary Data preview:', (response as any).ai_itinerary_data.substring(0, 200));
        // Print FULL ai_itinerary_data string fetched from database
        console.log('🧾 FULL ai_itinerary_data string (from DB):', (response as any).ai_itinerary_data);
      }
      return response;
    },
    retry: 1,
  });

  // Show loading state
  if (isLoading) {
    return (
      <div className="trip-details-page">
        <div className="loading-container">
          <FiLoader className="icon spinning" />
          <p>Loading trip details...</p>
        </div>
      </div>
    );
  }

  // Show error state
  if (error || !trip) {
    return (
      <div className="trip-details-page">
        <div className="error-container">
          <h2>Trip Not Found</h2>
          <p>The trip you're looking for doesn't exist or you don't have permission to view it.</p>
          <button 
            className="btn btn-primary"
            onClick={() => navigate({ to: '/trips' })}
          >
            Back to Trips
          </button>
        </div>
      </div>
    );
  }

  const mockItinerary = [
    {
      id: "1",
      day: 1,
      date: "2024-03-15",
      title: "Arrival & Eiffel Tower",
      activities: [
        {
          id: "1",
          time: "10:00",
          title: "Check-in at hotel",
          location: "Hotel des Invalides",
          duration: "1 hour",
          type: "accommodation"
        },
        {
          id: "2",
          time: "14:00",
          title: "Eiffel Tower visit",
          location: "Champ de Mars, 7th arrondissement",
          duration: "3 hours",
          type: "attraction",
          cost: 29
        },
        {
          id: "3",
          time: "19:00",
          title: "Dinner at local bistro",
          location: "Le Comptoir du Relais",
          duration: "2 hours",
          type: "dining",
          cost: 45
        }
      ]
    },
    {
      id: "2",
      day: 2,
      date: "2024-03-16",
      title: "Louvre & Seine Cruise",
      activities: [
        {
          id: "4",
          time: "09:00",
          title: "Louvre Museum",
          location: "Rue de Rivoli, 1st arrondissement",
          duration: "4 hours",
          type: "attraction",
          cost: 17
        },
        {
          id: "5",
          time: "15:00",
          title: "Seine River Cruise",
          location: "Port de la Bourdonnais",
          duration: "1 hour",
          type: "activity",
          cost: 15
        }
      ]
    }
  ]

  const mockBookings = [
    {
      id: "1",
      type: "flight",
      title: "Round-trip Flight",
      status: "confirmed",
      date: "2024-03-15",
      cost: 650,
      details: "Air France - Economy Class",
      confirmation_number: "AF123456"
    },
    {
      id: "2",
      type: "hotel",
      title: "Hotel des Invalides",
      status: "confirmed",
      date: "2024-03-15",
      cost: 1200,
      details: "7 nights, Deluxe Room",
      confirmation_number: "HOTEL789"
    },
    {
      id: "3",
      type: "activity",
      title: "Eiffel Tower Tickets",
      status: "confirmed",
      date: "2024-03-15",
      cost: 58,
      details: "Skip-the-line access",
      confirmation_number: "EIF456"
    }
  ]

  const mockCollaborators = [
    {
      id: "1",
      name: "Sarah Johnson",
      email: "sarah@example.com",
      role: "traveler",
      status: "accepted",
      avatar: "https://images.unsplash.com/photo-1494790108755-2616b612b786?w=100&h=100&fit=crop&crop=face"
    },
    {
      id: "2",
      name: "Mike Chen",
      email: "mike@example.com",
      role: "viewer",
      status: "pending",
      avatar: "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=100&h=100&fit=crop&crop=face"
    }
  ]

  const getStatusColor = (status: string) => {
    switch (status) {
      case "confirmed": return "#22C55E"
      case "pending": return "#F59E0B"
      case "cancelled": return "#EF4444"
      case "draft": return "#6B7280"
      default: return "#6B7280"
    }
  }

  // const getActivityTypeIcon = (type: string) => {
  //   switch (type) {
  //     case "attraction": return FiMapPin
  //     case "dining": return FiHeart
  //     case "accommodation": return FiUsers
  //     case "activity": return FiNavigation
  //     default: return FiClock
  //   }
  // }

  // const getBookingTypeIcon = (type: string) => {
  //   switch (type) {
  //     case "flight": return FiNavigation
  //     case "hotel": return FiUsers
  //     case "activity": return FiMapPin
  //     default: return FiCheck
  //   }
  // }

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      weekday: 'long',
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    })
  }

  const calculateDuration = (startDate: string, endDate: string) => {
    const start = new Date(startDate)
    const end = new Date(endDate)
    const diffTime = Math.abs(end.getTime() - start.getTime())
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24))
    return diffDays
  }

  const totalSpent = mockBookings.reduce((sum, booking) => sum + booking.cost, 0)
  const budgetProgress = trip.budget ? (totalSpent / trip.budget) * 100 : 0

  const tabs = ["Itinerary", "Photo Gallery", "Map Parser", "Bookings", "Collaborators", "Documents"]

  return (
    <div style={{ backgroundColor: "#0B1220", minHeight: "100vh", color: "#E5E7EB" }}>
      <div style={{ maxWidth: "1280px", margin: "0 auto", padding: "32px" }}>
        {/* Trip Header */}
        <div style={{ backgroundColor: "#111827", border: "1px solid #1F2937", borderRadius: "12px", overflow: "hidden", boxShadow: "0 1px 3px 0 rgba(0, 0, 0, 0.3)", marginBottom: "24px" }}>
          <div style={{ position: "relative" }}>
            <img
              src={trip.cover_image_url || `https://images.unsplash.com/photo-1488646953014-85cb44e25828?w=800&h=400&fit=crop`}
              alt={trip.title || trip.destination}
              style={{
                height: "300px",
                width: "100%",
                objectFit: "cover"
              }}
            />
            <div
              style={{
                position: "absolute",
                top: 0,
                left: 0,
                right: 0,
                bottom: 0,
                backgroundColor: "rgba(0, 0, 0, 0.6)"
              }}
            />
            <div style={{ position: "absolute", bottom: "24px", left: "24px", right: "24px" }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-end" }}>
                <div>
                  <h1 style={{ fontSize: "32px", fontWeight: "bold", color: "white", marginBottom: "8px" }}>
                    {trip.title}
                  </h1>
                  <div style={{ display: "flex", alignItems: "center", gap: "8px", color: "rgba(255, 255, 255, 0.8)", marginBottom: "8px" }}>
                    <FiMapPin size={20} />
                    <span>{trip.destination}</span>
                  </div>
                  <p style={{ color: "rgba(255, 255, 255, 0.8)" }}>
                    {formatDate(trip.start_date)} - {formatDate(trip.end_date)}
                  </p>
                </div>
                <div style={{ display: "flex", gap: "12px" }}>
                  <button
                    onClick={() => navigate({ to: '/trips' })}
                    style={{
                      backgroundColor: "transparent",
                      color: "white",
                      padding: "12px 16px",
                      borderRadius: "8px",
                      border: "1px solid rgba(255,255,255,0.6)",
                      fontSize: "14px",
                      fontWeight: 500,
                      cursor: "pointer"
                    }}
                  >
                    ← Back
                  </button>
                  <span
                    style={{
                      backgroundColor: getStatusColor(trip.status || 'planning'),
                      color: "white",
                      padding: "8px 16px",
                      borderRadius: "20px",
                      fontSize: "14px",
                      fontWeight: "500",
                      textTransform: "capitalize"
                    }}
                  >
                    {trip.status || 'planning'}
                  </span>
                  <button
                    style={{
                      backgroundColor: "#3B82F6",
                      color: "white",
                      padding: "12px 24px",
                      borderRadius: "8px",
                      border: "none",
                      fontSize: "14px",
                      fontWeight: "500",
                      cursor: "pointer",
                      display: "flex",
                      alignItems: "center",
                      gap: "8px"
                    }}
                  >
                    <FiEdit size={16} />
                    Edit Trip
                  </button>
                  <button
                    style={{
                      backgroundColor: "transparent",
                      color: "white",
                      padding: "12px 24px",
                      borderRadius: "8px",
                      border: "1px solid white",
                      fontSize: "14px",
                      fontWeight: "500",
                      cursor: "pointer",
                      display: "flex",
                      alignItems: "center",
                      gap: "8px"
                    }}
                  >
                    <FiShare2 size={16} />
                    Share
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Trip Stats */}
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", gap: "24px", marginBottom: "24px" }}>
          <div style={{ backgroundColor: "#111827", border: "1px solid #1F2937", borderRadius: "8px", padding: "24px", textAlign: "center", boxShadow: "0 1px 3px 0 rgba(0, 0, 0, 0.3)" }}>
            <FiCalendar size={32} color="#60A5FA" style={{ marginBottom: "8px" }} />
            <p style={{ fontSize: "24px", fontWeight: "bold", color: "#E5E7EB" }}>
              {calculateDuration(trip.start_date, trip.end_date)}
            </p>
            <p style={{ color: "#9CA3AF" }}>Days</p>
          </div>
          <div style={{ backgroundColor: "#111827", border: "1px solid #1F2937", borderRadius: "8px", padding: "24px", textAlign: "center", boxShadow: "0 1px 3px 0 rgba(0, 0, 0, 0.3)" }}>
            <FiDollarSign size={32} color="#22C55E" style={{ marginBottom: "8px" }} />
            <p style={{ fontSize: "24px", fontWeight: "bold", color: "#E5E7EB" }}>
              ${totalSpent.toLocaleString()}
            </p>
            <p style={{ color: "#9CA3AF" }}>Spent</p>
          </div>
          <div style={{ backgroundColor: "#111827", border: "1px solid #1F2937", borderRadius: "8px", padding: "24px", textAlign: "center", boxShadow: "0 1px 3px 0 rgba(0, 0, 0, 0.3)" }}>
            <FiUsers size={32} color="#8B5CF6" style={{ marginBottom: "8px" }} />
            <p style={{ fontSize: "24px", fontWeight: "bold", color: "#E5E7EB" }}>
              {mockCollaborators.length + 1}
            </p>
            <p style={{ color: "#9CA3AF" }}>Travelers</p>
          </div>
          <div style={{ backgroundColor: "#111827", border: "1px solid #1F2937", borderRadius: "8px", padding: "24px", textAlign: "center", boxShadow: "0 1px 3px 0 rgba(0, 0, 0, 0.3)" }}>
            <FiMapPin size={32} color="#F59E0B" style={{ marginBottom: "8px" }} />
            <p style={{ fontSize: "24px", fontWeight: "bold", color: "#E5E7EB" }}>
              {mockItinerary.length}
            </p>
            <p style={{ color: "#9CA3AF" }}>Days Planned</p>
          </div>
        </div>

        {/* Budget Progress */}
        <div style={{ backgroundColor: "#111827", border: "1px solid #1F2937", borderRadius: "12px", padding: "24px", boxShadow: "0 1px 3px 0 rgba(0, 0, 0, 0.3)", marginBottom: "24px" }}>
          <h3 style={{ fontSize: "18px", fontWeight: "600", color: "#E5E7EB", marginBottom: "16px" }}>Budget Overview</h3>
          <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
            <div style={{ display: "flex", justifyContent: "space-between" }}>
              <span>Budget: ${(trip.budget || 0).toLocaleString()}</span>
              <span>Spent: ${totalSpent.toLocaleString()}</span>
              <span>Remaining: ${((trip.budget || 0) - totalSpent).toLocaleString()}</span>
            </div>
            <div style={{
              width: "100%",
              height: "12px",
              backgroundColor: "#1F2937",
              borderRadius: "6px",
              overflow: "hidden"
            }}>
              <div style={{
                width: `${budgetProgress}%`,
                height: "100%",
                backgroundColor: budgetProgress > 80 ? "#EF4444" : budgetProgress > 60 ? "#F59E0B" : "#22C55E",
                transition: "width 0.3s ease"
              }} />
            </div>
          </div>
        </div>

        {/* Tabs */}
        <div style={{ backgroundColor: "#111827", border: "1px solid #1F2937", borderRadius: "12px", boxShadow: "0 1px 3px 0 rgba(0, 0, 0, 0.3)" }}>
          <div style={{ borderBottom: "1px solid #1F2937" }}>
            <div style={{ display: "flex" }}>
              {tabs.map((tab, index) => (
                <button
                  key={tab}
                  onClick={() => setActiveTab(index)}
                  style={{
                    padding: "16px 24px",
                    border: "none",
                    backgroundColor: "transparent",
                    color: activeTab === index ? "#60A5FA" : "#9CA3AF",
                    borderBottom: activeTab === index ? "2px solid #60A5FA" : "2px solid transparent",
                    cursor: "pointer",
                    fontSize: "14px",
                    fontWeight: "500"
                  }}
                >
                  {tab}
                </button>
              ))}
            </div>
          </div>

          <div style={{ padding: "24px" }}>
            {activeTab === 0 && (
              <div>
                {(trip as any).ai_itinerary_data ? (() => {
                  try {
                    const parsedData = JSON.parse((trip as any).ai_itinerary_data);
                    console.log('📦 Parsed itinerary data:', parsedData);
                    
                    // Extract the actual itinerary from nested structure
                    const itineraryData = parsedData.itinerary?.itinerary || parsedData.itinerary || parsedData;
                    console.log('✅ Extracted itinerary:', itineraryData);
                    // Also print FULL parsed JSON for debugging
                    try {
                      console.log('🧾 FULL parsed itinerary JSON:', JSON.stringify(parsedData));
                    } catch (e) {}
                    
                    const jsonText = (trip as any).ai_itinerary_data as string;
                    return (
                      <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
                        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                          <h3 style={{ fontSize: 18, fontWeight: 600, color: "#E5E7EB" }}>AI-generated Itinerary</h3>
                          <button
                            onClick={() => setShowRaw(v => !v)}
                            style={{ backgroundColor: "transparent", color: "#E5E7EB", padding: "8px 12px", borderRadius: 8, border: "1px solid #334155", cursor: "pointer", fontSize: 12 }}
                          >
                            {showRaw ? 'Hide Raw JSON' : 'Show Raw JSON'}
                          </button>
                        </div>
                        {showRaw && (
                          <div style={{ backgroundColor: "#0F172A", border: "1px solid #1F2937", borderRadius: 8, padding: 16, overflow: 'auto' }}>
                            <pre style={{ margin: 0, whiteSpace: 'pre-wrap', wordBreak: 'break-word', color: '#E5E7EB' }}>{jsonText}</pre>
                          </div>
                        )}
                        <ItineraryDisplay itinerary={itineraryData} />
                      </div>
                    );
                  } catch (error) {
                    console.error('❌ Error parsing itinerary:', error);
                    return (
                      <div style={{ textAlign: "center", padding: "48px" }}>
                        <FiMapPin size={48} color="#EF4444" style={{ marginBottom: "16px" }} />
                        <h3 style={{ fontSize: "20px", fontWeight: "600", color: "#1F2937", marginBottom: "8px" }}>
                          Error Loading Itinerary
                        </h3>
                        <p style={{ color: "#6B7280", marginBottom: "24px" }}>
                          There was an error loading your trip itinerary. Please try again.
                        </p>
                      </div>
                    );
                  }
                })() : (
                  <div style={{ textAlign: "center", padding: "48px" }}>
                    <FiMapPin size={48} color="#9CA3AF" style={{ marginBottom: "16px" }} />
                    <h3 style={{ fontSize: "20px", fontWeight: "600", color: "#1F2937", marginBottom: "8px" }}>
                      No AI Itinerary Available
                    </h3>
                    <p style={{ color: "#6B7280", marginBottom: "24px" }}>
                      This trip doesn't have an AI-generated itinerary yet.
                    </p>
                    <button
                      style={{
                        backgroundColor: "#3B82F6",
                        color: "white",
                        padding: "12px 24px",
                        borderRadius: "8px",
                        border: "none",
                        fontSize: "14px",
                        fontWeight: "500",
                        cursor: "pointer"
                      }}
                      onClick={() => window.location.href = '/plan-trip'}
                    >
                      Plan with AI
                    </button>
                  </div>
                )}
              </div>
            )}
            
            {activeTab === 0 && false && (
              <div style={{ display: "flex", flexDirection: "column", gap: "24px" }}>
                {mockItinerary.map((day) => (
                  <div key={day.id} style={{ backgroundColor: "white", border: "1px solid #E5E7EB", borderRadius: "8px", overflow: "hidden" }}>
                    <div style={{ padding: "16px", borderBottom: "1px solid #E5E7EB" }}>
                      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                        <div>
                          <h3 style={{ fontSize: "16px", fontWeight: "600", color: "#1F2937" }}>Day {day.day}</h3>
                          <p style={{ color: "#6B7280" }}>{formatDate(day.date)}</p>
                        </div>
                        <button
                          style={{
                            backgroundColor: "transparent",
                            color: "#3B82F6",
                            border: "1px solid #3B82F6",
                            padding: "8px 16px",
                            borderRadius: "6px",
                            fontSize: "14px",
                            cursor: "pointer",
                            display: "flex",
                            alignItems: "center",
                            gap: "8px"
                          }}
                        >
                          <FiEdit size={16} />
                          Edit Day
                        </button>
                      </div>
                    </div>
                    <div style={{ padding: "16px" }}>
                      <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
                        {day.activities.map((activity) => (
                          <div key={activity.id} style={{ padding: "16px", backgroundColor: "#F9FAFB", borderRadius: "8px" }}>
                            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
                              <div style={{ display: "flex", gap: "12px" }}>
                                <div
                                  style={{
                                    backgroundColor: "#DBEAFE",
                                    padding: "8px",
                                    borderRadius: "6px",
                                    minWidth: "60px",
                                    textAlign: "center"
                                  }}
                                >
                                  <p style={{ fontSize: "14px", fontWeight: "bold", color: "#1D4ED8" }}>
                                    {activity.time}
                                  </p>
                                </div>
                                <div>
                                  <p style={{ fontWeight: "500", color: "#1F2937" }}>
                                    {activity.title}
                                  </p>
                                  <div style={{ display: "flex", alignItems: "center", gap: "4px", color: "#6B7280", fontSize: "14px" }}>
                                    <FiMapPin size={16} />
                                    <span>{activity.location}</span>
                                  </div>
                                  <p style={{ fontSize: "14px", color: "#6B7280" }}>
                                    Duration: {activity.duration}
                                  </p>
                                  {activity.cost && (
                                    <p style={{ fontSize: "14px", color: "#22C55E", fontWeight: "500" }}>
                                      ${activity.cost}
                                    </p>
                                  )}
                                </div>
                              </div>
                              <button
                                style={{
                                  backgroundColor: "transparent",
                                  color: "#6B7280",
                                  border: "none",
                                  padding: "8px",
                                  borderRadius: "6px",
                                  cursor: "pointer"
                                }}
                              >
                                <FiEdit size={16} />
                              </button>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}

            {activeTab === 1 && (
              <PhotoGalleryComponent tripId={tripId} />
            )}

            {activeTab === 2 && (
              <>
                {console.log('🗺️ Trip data for MapParser:', {
                  tripId,
                  hasItineraryData: !!(trip as any).ai_itinerary_data,
                  hasMapData: !!(trip as any).map_data,
                  mapDataLength: (trip as any).map_data ? (trip as any).map_data.length : 0
                })}
                <MapParserComponent 
                  tripId={tripId} 
                  itineraryData={(trip as any).ai_itinerary_data ? (trip as any).ai_itinerary_data : null}
                  existingMapData={(trip as any).map_data || null}
                />
              </>
            )}

            {activeTab === 4 && (
              <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
                {mockBookings.map((booking) => (
                  <div key={booking.id} style={{ backgroundColor: "white", border: "1px solid #E5E7EB", borderRadius: "8px", padding: "16px" }}>
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                      <div style={{ display: "flex", gap: "16px", alignItems: "center" }}>
                        <FiNavigation size={24} color="#3B82F6" />
                        <div>
                          <p style={{ fontWeight: "500", color: "#1F2937" }}>
                            {booking.title}
                          </p>
                          <p style={{ fontSize: "14px", color: "#6B7280" }}>
                            {booking.details}
                          </p>
                          <p style={{ fontSize: "14px", color: "#6B7280" }}>
                            Confirmation: {booking.confirmation_number}
                          </p>
                        </div>
                      </div>
                      <div style={{ display: "flex", flexDirection: "column", alignItems: "flex-end", gap: "4px" }}>
                        <span
                          style={{
                            backgroundColor: getStatusColor(booking.status),
                            color: "white",
                            padding: "4px 8px",
                            borderRadius: "12px",
                            fontSize: "12px",
                            fontWeight: "500",
                            textTransform: "capitalize"
                          }}
                        >
                          {booking.status}
                        </span>
                        <p style={{ fontWeight: "bold", color: "#1F2937" }}>
                          ${booking.cost}
                        </p>
                        <button
                          style={{
                            backgroundColor: "transparent",
                            color: "#3B82F6",
                            border: "1px solid #3B82F6",
                            padding: "4px 8px",
                            borderRadius: "4px",
                            fontSize: "12px",
                            cursor: "pointer",
                            display: "flex",
                            alignItems: "center",
                            gap: "4px"
                          }}
                        >
                          <FiDownload size={12} />
                          Receipt
                        </button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}

            {activeTab === 5 && (
              <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                  <h3 style={{ fontSize: "18px", fontWeight: "600", color: "#1F2937" }}>Trip Collaborators</h3>
                  <button
                    style={{
                      backgroundColor: "#3B82F6",
                      color: "white",
                      padding: "12px 24px",
                      borderRadius: "8px",
                      border: "none",
                      fontSize: "14px",
                      fontWeight: "500",
                      cursor: "pointer",
                      display: "flex",
                      alignItems: "center",
                      gap: "8px"
                    }}
                  >
                    <FiPlus size={16} />
                    Invite Traveler
                  </button>
                </div>
                
                {mockCollaborators.map((collaborator) => (
                  <div key={collaborator.id} style={{ backgroundColor: "white", border: "1px solid #E5E7EB", borderRadius: "8px", padding: "16px" }}>
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                      <div style={{ display: "flex", gap: "16px", alignItems: "center" }}>
                        <img
                          src={collaborator.avatar}
                          alt={collaborator.name}
                          style={{
                            width: "48px",
                            height: "48px",
                            borderRadius: "50%",
                            objectFit: "cover"
                          }}
                        />
                        <div>
                          <p style={{ fontWeight: "500", color: "#1F2937" }}>
                            {collaborator.name}
                          </p>
                          <p style={{ fontSize: "14px", color: "#6B7280" }}>
                            {collaborator.email}
                          </p>
                          <p style={{ fontSize: "14px", color: "#6B7280", textTransform: "capitalize" }}>
                            {collaborator.role}
                          </p>
                        </div>
                      </div>
                      <div style={{ display: "flex", flexDirection: "column", alignItems: "flex-end", gap: "8px" }}>
                        <span
                          style={{
                            backgroundColor: getStatusColor(collaborator.status),
                            color: "white",
                            padding: "4px 8px",
                            borderRadius: "12px",
                            fontSize: "12px",
                            fontWeight: "500",
                            textTransform: "capitalize"
                          }}
                        >
                          {collaborator.status}
                        </span>
                        <div style={{ display: "flex", gap: "8px" }}>
                          <button
                            style={{
                              backgroundColor: "transparent",
                              color: "#6B7280",
                              border: "1px solid #E5E7EB",
                              padding: "8px",
                              borderRadius: "6px",
                              cursor: "pointer"
                            }}
                          >
                            <FiMessageCircle size={16} />
                          </button>
                          <button
                            style={{
                              backgroundColor: "transparent",
                              color: "#EF4444",
                              border: "1px solid #E5E7EB",
                              padding: "8px",
                              borderRadius: "6px",
                              cursor: "pointer"
                            }}
                          >
                            <FiX size={16} />
                          </button>
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}

            {activeTab === 6 && (
              <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                  <h3 style={{ fontSize: "18px", fontWeight: "600", color: "#1F2937" }}>Trip Documents</h3>
                  <button
                    style={{
                      backgroundColor: "#3B82F6",
                      color: "white",
                      padding: "12px 24px",
                      borderRadius: "8px",
                      border: "none",
                      fontSize: "14px",
                      fontWeight: "500",
                      cursor: "pointer",
                      display: "flex",
                      alignItems: "center",
                      gap: "8px"
                    }}
                  >
                    <FiPlus size={16} />
                    Upload Document
                  </button>
                </div>
                
                <p style={{ color: "#6B7280" }}>
                  No documents uploaded yet. Upload your travel documents, receipts, and important files here.
                </p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}