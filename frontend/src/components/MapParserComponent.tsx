import React, { useState, useEffect } from 'react';
import { useMutation } from '@tanstack/react-query';
import { OpenAPI } from '@/client';
import InteractiveMapComponent from './InteractiveMapComponent';
import { 
  FiMap, 
  FiMapPin, 
  FiNavigation, 
  FiLoader, 
  FiRefreshCw,
  FiAlertCircle,
  FiCheckCircle,
  FiEye,
  FiEyeOff
} from 'react-icons/fi';

interface MapData {
  day: number;
  name: string;
  lat: number;
  lng: number;
  description?: string;
  time?: string;
  elevation?: string;
  hotel?: string;
}

interface MapParserResponse {
  chatId: string;
  content_type: string;
  text: string;
  map_data: MapData[];
}

interface MapParserComponentProps {
  tripId: string;
  itineraryData?: any;
  existingMapData?: string; // JSON string of existing map data from database
}

const MapParserComponent: React.FC<MapParserComponentProps> = ({ tripId, itineraryData, existingMapData }) => {
  const [mapData, setMapData] = useState<MapParserResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showMap, setShowMap] = useState(false);
  const [hasAutoParsed, setHasAutoParsed] = useState(false);

  // Load existing map data or auto-parse when itinerary data changes
  useEffect(() => {
    console.log('🔍 MapParserComponent useEffect triggered');
    console.log('📊 Props:', { 
      tripId, 
      hasItineraryData: !!itineraryData, 
      hasExistingMapData: !!existingMapData,
      hasMapData: !!mapData,
      hasAutoParsed 
    });
    
    // First, try to load existing map data from database
    if (existingMapData && !mapData) {
      try {
        console.log('📦 Loading existing map data from database...');
        const parsedMapData = JSON.parse(existingMapData);
        setMapData(parsedMapData);
        setShowMap(true);
        console.log('✅ Loaded existing map data from database:', parsedMapData);
        return;
      } catch (error) {
        console.error('❌ Error parsing existing map data:', error);
      }
    }
    
    // Only parse if no existing data and itinerary is available
    if (itineraryData && !hasAutoParsed && !existingMapData) {
      console.log('🔄 No existing map data found, parsing itinerary...');
      handleParseItinerary();
      setHasAutoParsed(true);
    }
  }, [itineraryData, existingMapData, hasAutoParsed, mapData]);

  // Auto-show map when data is available
  useEffect(() => {
    if (mapData && mapData.map_data.length > 0) {
      setShowMap(true);
    }
  }, [mapData]);

  // Parse itinerary mutation
  const parseItineraryMutation = useMutation({
    mutationFn: async (data: { itinerary_data: any; chat_id: string; trip_id?: string }) => {
      const response = await fetch(`${OpenAPI.BASE}/api/v1/map-parser/parse-itinerary`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`
        },
        body: JSON.stringify(data)
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return response.json();
    },
    onSuccess: (data) => {
      setMapData(data);
      setError(null);
      setIsLoading(false);
    },
    onError: (error) => {
      setError(error.message);
      setIsLoading(false);
    }
  });

  const handleParseItinerary = async () => {
    if (!itineraryData) {
      setError('No itinerary data available to parse');
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      // Handle both JSON and plain text itinerary data
      let parsedData;
      if (typeof itineraryData === 'string') {
        try {
          parsedData = JSON.parse(itineraryData);
        } catch {
          // If it's not JSON, treat it as plain text
          parsedData = {
            itinerary: {
              days: [
                {
                  day: 1,
                  activities: [
                    {
                      time: "",
                      activity: itineraryData,
                      location: "Tokyo, Japan"
                    }
                  ]
                }
              ]
            }
          };
        }
      } else {
        parsedData = itineraryData;
      }

      await parseItineraryMutation.mutateAsync({
        itinerary_data: parsedData,
        chat_id: `trip_${tripId}_${Date.now()}`,
        trip_id: tripId
      });
    } catch (error) {
      console.error('Error parsing itinerary:', error);
    }
  };

  const renderMapVisualization = () => {
    if (!mapData || !mapData.map_data.length) {
      return (
        <div style={{ 
          padding: '40px', 
          textAlign: 'center', 
          color: '#6B7280',
          backgroundColor: '#1F2937',
          borderRadius: '8px',
          border: '1px solid #374151'
        }}>
          <FiMapPin size={48} style={{ marginBottom: '16px', opacity: 0.5 }} />
          <p>No map data available</p>
        </div>
      );
    }

    return (
      <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
        {/* Summary Text */}
        {mapData.text && (
          <div style={{
            backgroundColor: '#1F2937',
            border: '1px solid #374151',
            borderRadius: '8px',
            padding: '16px'
          }}>
            <h3 style={{ 
              color: '#E5E7EB', 
              marginBottom: '12px',
              display: 'flex',
              alignItems: 'center',
              gap: '8px'
            }}>
              <FiNavigation size={20} />
              Itinerary Summary
            </h3>
            <div style={{ 
              color: '#D1D5DB',
              lineHeight: '1.6',
              whiteSpace: 'pre-line'
            }}>
              {mapData.text}
            </div>
          </div>
        )}

        {/* Interactive Map */}
        <InteractiveMapComponent 
          mapData={mapData.map_data}
          text={mapData.text}
        />
      </div>
    );
  };

  return (
    <div style={{ 
      backgroundColor: '#111827',
      border: '1px solid #1F2937',
      borderRadius: '12px',
      padding: '24px'
    }}>
      <div style={{ 
        display: 'flex', 
        justifyContent: 'space-between', 
        alignItems: 'center',
        marginBottom: '20px'
      }}>
        <div>
          <h2 style={{ 
            color: '#E5E7EB', 
            fontSize: '24px',
            fontWeight: 'bold',
            marginBottom: '8px',
            display: 'flex',
            alignItems: 'center',
            gap: '8px'
          }}>
            <FiMap size={24} />
            Travya Map Parser v2
          </h2>
          <p style={{ 
            color: '#9CA3AF',
            fontSize: '14px'
          }}>
            Convert your itinerary into geo-enriched map data for visualization
          </p>
        </div>
        
        <div style={{ display: 'flex', gap: '12px' }}>
          <button
            onClick={() => setShowMap(!showMap)}
            style={{
              backgroundColor: '#374151',
              color: '#E5E7EB',
              border: '1px solid #4B5563',
              borderRadius: '8px',
              padding: '8px 16px',
              fontSize: '14px',
              fontWeight: '500',
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              cursor: 'pointer'
            }}
          >
            {showMap ? <FiEyeOff size={16} /> : <FiEye size={16} />}
            {showMap ? 'Hide Map' : 'Show Map'}
          </button>
          
          <button
            onClick={handleParseItinerary}
            disabled={isLoading || !itineraryData}
            style={{
              backgroundColor: isLoading ? '#6B7280' : '#3B82F6',
              color: 'white',
              border: 'none',
              borderRadius: '8px',
              padding: '8px 16px',
              fontSize: '14px',
              fontWeight: '500',
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              cursor: isLoading ? 'not-allowed' : 'pointer',
              opacity: isLoading ? 0.6 : 1
            }}
          >
            {isLoading ? (
              <FiLoader size={16} className="animate-spin" />
            ) : (
              <FiRefreshCw size={16} />
            )}
            {isLoading ? 'Parsing...' : 'Parse Itinerary'}
          </button>
        </div>
      </div>

      {/* Status Messages */}
      {error && (
        <div style={{
          backgroundColor: '#FEF2F2',
          border: '1px solid #FECACA',
          borderRadius: '8px',
          padding: '12px',
          marginBottom: '16px',
          display: 'flex',
          alignItems: 'center',
          gap: '8px'
        }}>
          <FiAlertCircle size={20} color="#DC2626" />
          <span style={{ color: '#DC2626', fontSize: '14px' }}>
            {error}
          </span>
        </div>
      )}

      {mapData && !error && (
        <div style={{
          backgroundColor: '#F0FDF4',
          border: '1px solid #BBF7D0',
          borderRadius: '8px',
          padding: '12px',
          marginBottom: '16px',
          display: 'flex',
          alignItems: 'center',
          gap: '8px'
        }}>
          <FiCheckCircle size={20} color="#16A34A" />
          <span style={{ color: '#16A34A', fontSize: '14px' }}>
            Successfully parsed {mapData.map_data.length} locations from itinerary
          </span>
        </div>
      )}

      {/* Map Visualization */}
      {showMap && renderMapVisualization()}

      {/* Instructions */}
      {!mapData && !isLoading && (
        <div style={{
          backgroundColor: '#1F2937',
          border: '1px solid #374151',
          borderRadius: '8px',
          padding: '20px',
          textAlign: 'center'
        }}>
          <FiMapPin size={48} style={{ marginBottom: '16px', opacity: 0.5, color: '#6B7280' }} />
          <h3 style={{ color: '#E5E7EB', marginBottom: '8px' }}>
            Ready to Parse Your Itinerary
          </h3>
          <p style={{ color: '#9CA3AF', fontSize: '14px', lineHeight: '1.5' }}>
            Click "Parse Itinerary" to convert your travel data into geo-enriched map locations.
            The parser will extract coordinates, elevations, and create a visual representation of your journey.
          </p>
        </div>
      )}
    </div>
  );
};

export default MapParserComponent;
