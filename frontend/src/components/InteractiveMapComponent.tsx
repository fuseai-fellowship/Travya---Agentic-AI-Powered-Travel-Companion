import React, { useEffect, useState } from 'react';
import { MapContainer, TileLayer, Marker, Popup, Polyline, useMap } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { 
  FiMapPin, 
  FiNavigation, 
  FiClock, 
  FiTrendingUp,
  FiEye,
  FiEyeOff,
  FiLoader
} from 'react-icons/fi';

// Fix for default markers in react-leaflet
delete (L.Icon.Default.prototype as any)._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
});

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

interface InteractiveMapComponentProps {
  mapData: MapData[];
  text?: string;
}

// Function to get road-based route using OpenRouteService API
const getRoadRoute = async (coordinates: [number, number][]): Promise<[number, number][] | null> => {
  try {
    if (coordinates.length < 2) return null;
    
    // Use OpenRouteService Directions API (free tier)
    const apiKey = '5b3ce3597851110001cf6248b8b4c8a4b3c84c66a8b8b4c8a4b3c84c66'; // Free API key
    const coordinatesString = coordinates.map(coord => `${coord[1]},${coord[0]}`).join('|');
    
    const response = await fetch(
      `https://api.openrouteservice.org/v2/directions/driving-car?api_key=${apiKey}&coordinates=${coordinatesString}&format=geojson`
    );
    
    if (!response.ok) {
      console.warn('OpenRouteService API failed, falling back to straight lines');
      return null;
    }
    
    const data = await response.json();
    
    if (data.features && data.features[0] && data.features[0].geometry) {
      // Convert GeoJSON coordinates to Leaflet format
      return data.features[0].geometry.coordinates.map((coord: number[]) => [coord[1], coord[0]] as [number, number]);
    }
    
    return null;
  } catch (error) {
    console.warn('Error getting road route:', error);
    return null;
  }
};

// Custom marker component for numbered day markers
const DayMarker: React.FC<{ 
  position: [number, number]; 
  day: number; 
  data: MapData;
  color: string;
}> = ({ position, day, data, color }) => {
  const customIcon = L.divIcon({
    className: 'custom-day-marker',
    html: `
      <div style="
        background: ${color};
        color: white;
        border: 2px solid white;
        border-radius: 50%;
        width: 32px;
        height: 32px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: bold;
        font-size: 14px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.3);
        cursor: pointer;
      ">
        ${day}
      </div>
    `,
    iconSize: [32, 32],
    iconAnchor: [16, 16],
    popupAnchor: [0, -16]
  });

  return (
    <Marker position={position} icon={customIcon}>
      <Popup>
        <div style={{ minWidth: '200px' }}>
          <div style={{ 
            display: 'flex', 
            alignItems: 'center', 
            gap: '8px',
            marginBottom: '8px'
          }}>
            <FiMapPin size={16} color={color} />
            <strong style={{ color: '#1F2937' }}>Day {day}: {data.name}</strong>
          </div>
          
          {data.elevation && (
            <div style={{ 
              display: 'flex', 
              alignItems: 'center', 
              gap: '6px',
              marginBottom: '6px',
              fontSize: '14px',
              color: '#6B7280'
            }}>
              <FiTrendingUp size={14} />
              Elevation: {data.elevation}
            </div>
          )}
          
          {data.time && (
            <div style={{ 
              display: 'flex', 
              alignItems: 'center', 
              gap: '6px',
              marginBottom: '6px',
              fontSize: '14px',
              color: '#6B7280'
            }}>
              <FiClock size={14} />
              Time: {data.time}
            </div>
          )}
          
          <div style={{ 
            fontSize: '12px',
            color: '#9CA3AF',
            marginBottom: '6px'
          }}>
            {data.lat.toFixed(4)}, {data.lng.toFixed(4)}
          </div>
          
          {data.description && (
            <div style={{ 
              fontSize: '13px',
              color: '#374151',
              lineHeight: '1.4',
              marginTop: '8px',
              padding: '8px',
              backgroundColor: '#F9FAFB',
              borderRadius: '4px'
            }}>
              {data.description}
            </div>
          )}
          
          {data.hotel && (
            <div style={{ 
              fontSize: '12px',
              color: '#059669',
              marginTop: '6px',
              fontWeight: '500'
            }}>
              🏨 {data.hotel}
            </div>
          )}
        </div>
      </Popup>
    </Marker>
  );
};

// Component to fit map bounds to show all markers
const MapBounds: React.FC<{ mapData: MapData[] }> = ({ mapData }) => {
  const map = useMap();
  
  useEffect(() => {
    if (mapData.length > 0) {
      const bounds = L.latLngBounds(
        mapData.map(point => [point.lat, point.lng])
      );
      map.fitBounds(bounds, { padding: [20, 20] });
    }
  }, [map, mapData]);
  
  return null;
};

const InteractiveMapComponent: React.FC<InteractiveMapComponentProps> = ({ 
  mapData
}) => {
  const [showRoute, setShowRoute] = useState(true);
  const [showMarkers, setShowMarkers] = useState(true);
  const [mapStyle, setMapStyle] = useState<'street' | 'satellite' | 'terrain'>('street');
  const [roadRoutes, setRoadRoutes] = useState<Record<number, [number, number][]>>({});
  const [isLoadingRoutes, setIsLoadingRoutes] = useState(false);

  // Color palette for different days
  const dayColors = [
    '#3B82F6', // Blue
    '#10B981', // Green  
    '#F59E0B', // Yellow
    '#EF4444', // Red
    '#8B5CF6', // Purple
    '#06B6D4', // Cyan
    '#84CC16', // Lime
    '#F97316', // Orange
    '#EC4899', // Pink
    '#6B7280', // Gray
  ];

  // Group data by day for route visualization
  const groupedData = mapData.reduce((acc, item) => {
    if (!acc[item.day]) {
      acc[item.day] = [];
    }
    acc[item.day].push(item);
    return acc;
  }, {} as Record<number, MapData[]>);

  // Load road routes when mapData changes
  useEffect(() => {
    const loadRoadRoutes = async () => {
      if (Object.keys(groupedData).length === 0) return;
      
      setIsLoadingRoutes(true);
      const newRoadRoutes: Record<number, [number, number][]> = {};
      
      for (const [day, locations] of Object.entries(groupedData)) {
        if (locations.length >= 2) {
          const coordinates = locations.map(loc => [loc.lat, loc.lng] as [number, number]);
          const roadRoute = await getRoadRoute(coordinates);
          
          if (roadRoute) {
            newRoadRoutes[parseInt(day)] = roadRoute;
            console.log(`✅ Loaded road route for Day ${day} with ${roadRoute.length} points`);
          } else {
            // Fallback to straight lines
            newRoadRoutes[parseInt(day)] = coordinates;
            console.log(`⚠️ Using straight line route for Day ${day}`);
          }
        }
      }
      
      setRoadRoutes(newRoadRoutes);
      setIsLoadingRoutes(false);
    };

    loadRoadRoutes();
  }, [mapData]);

  // Create route polylines for each day using road routes
  const routePolylines = Object.entries(groupedData).map(([day, locations]) => {
    const dayNum = parseInt(day);
    const positions = roadRoutes[dayNum] || locations.map(loc => [loc.lat, loc.lng] as [number, number]);
    const color = dayColors[(dayNum - 1) % dayColors.length];
    
    return (
      <Polyline
        key={`route-${day}`}
        positions={positions}
        color={color}
        weight={4}
        opacity={0.8}
        dashArray={showRoute ? undefined : '10, 10'}
      />
    );
  });

  // Get tile layer URL based on style
  const getTileUrl = () => {
    switch (mapStyle) {
      case 'satellite':
        return 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}';
      case 'terrain':
        return 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Topo_Map/MapServer/tile/{z}/{y}/{x}';
      default:
        return 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png';
    }
  };

  if (!mapData || mapData.length === 0) {
    return (
      <div style={{ 
        height: '400px',
        backgroundColor: '#1F2937',
        border: '1px solid #374151',
        borderRadius: '8px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        color: '#9CA3AF'
      }}>
        <div style={{ textAlign: 'center' }}>
          <FiMapPin size={48} style={{ marginBottom: '16px', opacity: 0.5 }} />
          <p>No map data available</p>
        </div>
      </div>
    );
  }

  return (
    <div style={{ 
      backgroundColor: '#111827',
      border: '1px solid #1F2937',
      borderRadius: '12px',
      overflow: 'hidden'
    }}>
      {/* Map Controls */}
      <div style={{
        backgroundColor: '#1F2937',
        padding: '12px 16px',
        borderBottom: '1px solid #374151',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        flexWrap: 'wrap',
        gap: '12px'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <FiNavigation size={16} color="#E5E7EB" />
            <span style={{ color: '#E5E7EB', fontSize: '14px', fontWeight: '500' }}>
              Interactive Travel Map
            </span>
          </div>
          
          <div style={{ 
            fontSize: '12px', 
            color: '#9CA3AF',
            backgroundColor: '#374151',
            padding: '4px 8px',
            borderRadius: '4px'
          }}>
            {mapData.length} locations
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          {/* Map Style Selector */}
          <select
            value={mapStyle}
            onChange={(e) => setMapStyle(e.target.value as any)}
            style={{
              backgroundColor: '#374151',
              color: '#E5E7EB',
              border: '1px solid #4B5563',
              borderRadius: '6px',
              padding: '6px 8px',
              fontSize: '12px'
            }}
          >
            <option value="street">Street</option>
            <option value="satellite">Satellite</option>
            <option value="terrain">Terrain</option>
          </select>

          {/* Toggle Controls */}
          <button
            onClick={() => setShowRoute(!showRoute)}
            disabled={isLoadingRoutes}
            style={{
              backgroundColor: showRoute ? '#3B82F6' : '#374151',
              color: 'white',
              border: 'none',
              borderRadius: '6px',
              padding: '6px 12px',
              fontSize: '12px',
              cursor: isLoadingRoutes ? 'not-allowed' : 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '4px',
              opacity: isLoadingRoutes ? 0.6 : 1
            }}
          >
            {isLoadingRoutes ? <FiLoader size={12} className="animate-spin" /> : (showRoute ? <FiEye size={12} /> : <FiEyeOff size={12} />)}
            {isLoadingRoutes ? 'Loading Routes...' : 'Route'}
          </button>

          <button
            onClick={() => setShowMarkers(!showMarkers)}
            style={{
              backgroundColor: showMarkers ? '#10B981' : '#374151',
              color: 'white',
              border: 'none',
              borderRadius: '6px',
              padding: '6px 12px',
              fontSize: '12px',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '4px'
            }}
          >
            <FiMapPin size={12} />
            Markers
          </button>
        </div>
      </div>

      {/* Map Container */}
      <div style={{ height: '500px', width: '100%' }}>
        <MapContainer
          center={[mapData[0]?.lat || 0, mapData[0]?.lng || 0]}
          zoom={8}
          style={{ height: '100%', width: '100%' }}
          zoomControl={true}
          scrollWheelZoom={true}
        >
          <TileLayer
            url={getTileUrl()}
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          />
          
          {/* Fit bounds to show all markers */}
          <MapBounds mapData={mapData} />
          
          {/* Route Lines */}
          {showRoute && routePolylines}
          
          {/* Day Markers */}
          {showMarkers && mapData.map((point, index) => (
            <DayMarker
              key={index}
              position={[point.lat, point.lng]}
              day={point.day}
              data={point}
              color={dayColors[(point.day - 1) % dayColors.length]}
            />
          ))}
        </MapContainer>
      </div>

      {/* Legend */}
      <div style={{
        backgroundColor: '#1F2937',
        padding: '12px 16px',
        borderTop: '1px solid #374151',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        flexWrap: 'wrap',
        gap: '12px'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <div style={{
              width: '16px',
              height: '4px',
              backgroundColor: '#3B82F6',
              borderRadius: '2px'
            }} />
            <span style={{ color: '#9CA3AF', fontSize: '12px' }}>Travel Route</span>
          </div>
          
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <div style={{
              width: '12px',
              height: '12px',
              backgroundColor: '#3B82F6',
              borderRadius: '50%',
              border: '2px solid white'
            }} />
            <span style={{ color: '#9CA3AF', fontSize: '12px' }}>Day Markers</span>
          </div>
        </div>

        <div style={{ fontSize: '12px', color: '#6B7280' }}>
          Click markers for details • Drag to explore • Scroll to zoom
        </div>
      </div>
    </div>
  );
};

export default InteractiveMapComponent;
