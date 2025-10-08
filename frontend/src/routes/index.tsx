import React, { useState, useEffect } from "react";
import {
  Box,
  Container,
  Heading,
  Text,
  Button,
  Flex,
  HStack,
  IconButton,
  VStack,
} from "@chakra-ui/react";
import { MessageCircle } from "lucide-react";
import { useNavigate } from "@tanstack/react-router";
import { createFileRoute } from "@tanstack/react-router";

export const Route = createFileRoute("/")({
  component: TravelPlannerLanding,
});

function TravelPlannerLanding() {
  const [currentImage, setCurrentImage] = useState<number>(0);
  const navigate = useNavigate();

  // Random images picked from unsplash
  const travelImages: string[] = [
    "https://images.unsplash.com/photo-1488646953014-85cb44e25828?w=1920&h=1080&fit=crop",
    "https://images.unsplash.com/photo-1476514525535-07fb3b4ae5f1?w=1920&h=1080&fit=crop",
    "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?w=1920&h=1080&fit=crop",
    "https://images.unsplash.com/photo-1469854523086-cc02fe5d8800?w=1920&h=1080&fit=crop",
    "https://images.unsplash.com/photo-1530789253388-582c481c54b0?w=1920&h=1080&fit=crop",
  ];

  useEffect(() => {
    const interval = setInterval(() => {
      setCurrentImage((prev) => (prev + 1) % travelImages.length);
    }, 5000);

    return () => clearInterval(interval);
  }, [travelImages.length]);

  return (
    <Box position="relative" w="full" h="100vh" overflow="hidden">
      {/* Sliding Background Images */}
      <Box position="absolute" inset="0">
        {travelImages.map((image, index) => (
          <Box
            key={index}
            position="absolute"
            inset="0"
            transition="opacity 1s"
            opacity={index === currentImage ? 1 : 0}
            backgroundImage={`url(${image})`}
            backgroundSize="cover"
            backgroundPosition="center"
          />
        ))}
        {/* Overlay for visibility cause white bg not very useful hhhehe*/}
        <Box position="absolute" inset="0" bg="rgba(0, 0, 0, 0.6)" />
      </Box>

      {/* Main Content */}
      <Flex
        position="relative"
        zIndex={10}
        direction="column"
        align="center"
        justify="center"
        h="full"
        px={4}
      >
        <Container maxW="container.lg" textAlign="center">
          <VStack gapX={6} align="center">
            <Heading
              as="h1"
              size={{ base: "2xl", md: "4xl" }}
              color="white"
              textShadow="0 4px 6px rgba(0, 0, 0, 0.3)"
              fontWeight="bold"
            >
              Travya: Your AI Travel Companion
            </Heading>
            <Text
              fontSize={{ base: "xl", md: "2xl" }}
              color="cyan.100"
              textShadow="0 2px 4px rgba(0, 0, 0, 0.3)"
              textAlign="center"
            >
              Plan your perfect journey with personalized recommendations
            </Text>
            <Button
              size="lg"
              px={8}
              py={6}
              bgGradient="linear(to-r, cyan.500, blue.600)"
              color="white"
              fontSize="lg"
              fontWeight="semibold"
              borderRadius="full"
              boxShadow="2xl"
              _hover={{
                transform: "scale(1.05)",
                boxShadow: "0 0 40px rgba(6, 182, 212, 0.5)",
              }}
              transition="all 0.3s"
              onClick={() => navigate({ to: "/chat" })}
            >
              <Flex align="center" gap={2} justify="center">
                <MessageCircle size={20} />
                Start
              </Flex>
            </Button>
          </VStack>
        </Container>

        {/* Image indicators */}
        <HStack position="absolute" bottom={8} gap={2}>
          {travelImages.map((_, index) => (
            <IconButton
              key={index}
              aria-label={`Go to image ${index + 1}`}
              size="xs"
              minW={index === currentImage ? "32px" : "8px"}
              h="8px"
              borderRadius="full"
              bg={index === currentImage ? "white" : "whiteAlpha.500"}
              _hover={{
                bg: index === currentImage ? "white" : "whiteAlpha.700",
              }}
              transition="all 0.3s"
              onClick={() => setCurrentImage(index)}
            />
          ))}
        </HStack>
      </Flex>
    </Box>
  );
}

export default TravelPlannerLanding;
