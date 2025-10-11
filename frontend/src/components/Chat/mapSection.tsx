import React from "react";
import { Box, Flex, Text, IconButton } from "@chakra-ui/react";
import { MapPin, X } from "lucide-react";

interface MapSectionProps {
  isMobile?: boolean;
  onClose?: () => void;
}

export const MapSection: React.FC<MapSectionProps> = ({ 
  isMobile = false, 
  onClose 
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
        <Box h="calc(100vh - 65px)">
          <iframe
            width="100%"
            height="100%"
            style={{ border: 0 }}
            loading="lazy"
            src="https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d3022.2412648750455!2d-73.98823492346688!3d40.748817!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x89c259a9b3117469%3A0xd134e199a405a163!2sEmpire%20State%20Building!5e0!3m2!1sen!2sus!4v1234567890"
          ></iframe>
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
      <Box p={4} borderBottom="1px" borderColor="gray.200" bg="white">
        <Flex align="center" gap={2}>
          <MapPin size={18} color="#06b6d4" />
          <Text fontSize="sm" fontWeight="semibold" color="gray.900">
            Destination Map
          </Text>
        </Flex>
      </Box>
      <Box h="calc(100% - 57px)" position="relative">
        <iframe
          width="100%"
          height="100%"
          style={{ border: 0 }}
          loading="lazy"
          src="https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d3022.2412648750455!2d-73.98823492346688!3d40.748817!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x89c259a9b3117469%3A0xd134e199a405a163!2sEmpire%20State%20Building!5e0!3m2!1sen!2sus!4v1234567890"
        ></iframe>
      </Box>
    </Box>
  );
};