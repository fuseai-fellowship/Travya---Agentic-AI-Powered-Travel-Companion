import React from "react";
import { Box, Flex, Text, VStack } from "@chakra-ui/react";
import { Sparkles } from "lucide-react";

import { Message } from "@/types/chat";
import { FileAttachment } from "./fileAttachment";

interface MessageItemProps {
  message: Message;
}

export const MessageItem: React.FC<MessageItemProps> = ({ message }) => {
  return (
    <Flex justify={message.type === "user" ? "flex-end" : "flex-start"}>
      <Box maxW="85%">
        {message.type === "ai" && (
          <Flex align="center" gap={2} mb={2}>
            <Flex
              w="24px"
              h="24px"
              bgGradient="linear(to-br, cyan.500, blue.600)"
              borderRadius="md"
              align="center"
              justify="center"
            >
              <Sparkles size={14} color="white" />
            </Flex>
            <Text fontSize="sm" fontWeight="medium" color="gray.700">
              Travya
            </Text>
          </Flex>
        )}

        <Box
          borderRadius="2xl"
          px={4}
          py={3}
          bg={message.type === "user" ? "gray.900" : "gray.50"}
          color={message.type === "user" ? "white" : "gray.900"}
        >
          {/* File Attachments */}
          {message.files && message.files.length > 0 && (
            <VStack mb={3} spaceY={2} align="stretch">
              {message.files.map((file, idx) => (
                <FileAttachment key={idx} file={file} variant="message" />
              ))}
            </VStack>
          )}

          <Text fontSize="md" lineHeight="tall" whiteSpace="pre-wrap">
            {message.text}
          </Text>
        </Box>
      </Box>
    </Flex>
  );
};
