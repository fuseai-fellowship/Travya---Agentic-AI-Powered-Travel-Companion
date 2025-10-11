import React from "react";
import { Flex, Box, VStack, Text } from "@chakra-ui/react";
import { Sparkles } from "lucide-react";
import { ChatInputProps } from "@/types/chat";
import { ChatInput } from "./chatInput";

export const ChatWelcomeScreen: React.FC<ChatInputProps> = (props) => {
  return (
    <Flex direction="column" align="center" justify="center" h="full" px={4}>
      <VStack spaceY={6} maxW="2xl" w="full">
        {/* Hero Section */}
        <VStack spaceY={3} textAlign="center">
          <Flex
            w="48px"
            h="48px"
            bgGradient="linear(to-br, cyan.500, blue.600)"
            borderRadius="xl"
            align="center"
            justify="center"
          >
            <Sparkles size={24} color="white" />
          </Flex>
          <Text fontSize="3xl" fontWeight="bold" color="gray.900">
            Where to next?
          </Text>
          <Text fontSize="lg" color="gray.600" maxW="md">
            Tell me about your dream destination and I'll help plan your perfect
            trip
          </Text>
        </VStack>

        {/* Input Area */}
        <Box w="full">
          <ChatInput {...props} variant="welcome" />
        </Box>
      </VStack>
    </Flex>
  );
};
