import React, { useEffect } from "react";
import { Box, Flex, Text, IconButton } from "@chakra-ui/react";
import { MapPin, X } from "lucide-react";
import { MapContainer, Marker, TileLayer, Popup, useMap } from "react-leaflet";
import "leaflet/dist/leaflet.css";

interface MapSectionProps {
  isMobile?: boolean;
  onClose?: () => void;
}
//if not used the map does not load properly
function MapResizer() {
  const map = useMap();

  useEffect(() => {
    const timer = setTimeout(() => {
      map.invalidateSize();
    }, 100);

    return () => clearTimeout(timer);
  }, [map]);

  return null;
}
export const MapSection: React.FC<MapSectionProps> = ({
  isMobile = false,
  onClose,
}) => {
  if (isMobile) {
    return (
      <Box
        position="fixed"
        top="0"
        left="0"
        right="0"
        bottom="0"
        zIndex="9999"
        bg="white"
      >
        <style>
          {`
            .map-container .leaflet-container {
              height: 100%;
              width: 100%;
            }
          `}
        </style>
        {/* Header */}
        <Flex
          p={4}
          borderBottom="1px"
          borderColor="gray.200"
          align="center"
          justify="space-between"
        >
          <Flex align="center" gap={2}>
            <MapPin size={18} color="#06b6d4" />
            <Text fontSize="md" fontWeight="semibold">
              Destination Map
            </Text>
          </Flex>
          <IconButton
            aria-label="Close map"
            onClick={onClose}
            bg="transparent"
            color="gray.600"
            borderRadius="lg"
            minW="32px"
            h="32px"
            _hover={{ bg: "gray.100" }}
          >
            <X size={18} />
          </IconButton>
        </Flex>

        {/* Map */}
        <Box h="calc(100vh - 65px)" className="map-container">
          <MapContainer
            center={[27.696, 85.376]}
            zoom={11}
            scrollWheelZoom={true}
            style={{ height: "100%", width: "100%" }}
          >
            <MapResizer />
            <TileLayer
              attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
              url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
            />
            <Marker position={[27.7172, 85.324]}>
              <Popup>
                Kathmandu, Nepal <br /> Your destination
              </Popup>
            </Marker>
            <Marker position={[27.6748, 85.4274]}>
              <Popup>
                Bhaktapur, Nepal <br /> Your destination
              </Popup>
            </Marker>
          </MapContainer>
        </Box>
      </Box>
    );
  }

  return (
    <Box
      flex="0 0 50%"
      bg="gray.50"
      position="relative"
      overflow="hidden"
      display={{ base: "none", md: "block" }}
      borderLeft="1px"
      borderColor="gray.200"
    >
      <style>
        {`
          .map-container .leaflet-container {
            height: 100%;
            width: 100%;
          }
        `}
      </style>
      <Box p={4} borderBottom="1px" borderColor="gray.200" bg="white">
        <Flex align="center" gap={2}>
          <MapPin size={18} color="#06b6d4" />
          <Text fontSize="sm" fontWeight="semibold" color="gray.900">
            Destinations
          </Text>
        </Flex>
      </Box>
      <Box h="calc(100% - 57px)" position="relative" className="map-container">
        <MapContainer
          center={[27.696, 85.376]}
          zoom={11}
          scrollWheelZoom={true}
          style={{ height: "100%", width: "100%" }}
        >
          <MapResizer />
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />
          <Marker position={[27.7172, 85.324]}>
            <Popup>
              Kathmandu, Nepal <br /> Your destination
            </Popup>
          </Marker>
          <Marker position={[27.6748, 85.4274]}>
            <Popup>
              Bhaktapur, Nepal <br /> Your destination
            </Popup>
          </Marker>
        </MapContainer>
      </Box>
    </Box>
  );
};
