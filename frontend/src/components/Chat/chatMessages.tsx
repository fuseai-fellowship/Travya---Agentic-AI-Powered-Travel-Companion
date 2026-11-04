import React, { RefObject } from "react";
import { Box, VStack } from "@chakra-ui/react";

import { Message } from "@/types/chat";
import { MessageItem } from "./messageItem";
import { TypingIndicator } from "./typingIndicator";

interface ChatMessagesProps {
  messages: Message[];
  isTyping: boolean;
  messagesEndRef: RefObject<HTMLDivElement>;
}

export const ChatMessages: React.FC<ChatMessagesProps> = ({
  messages,
  isTyping,
  messagesEndRef,
}) => {
  return (
    <Box flex="1" overflowY="auto" px={6} py={6}>
      <VStack maxW="3xl" mx="auto" spaceY={6} align="stretch">
        {messages.map((message) => (
          <MessageItem key={message.id} message={message} />
        ))}

        {isTyping && <TypingIndicator />}

        <div ref={messagesEndRef} />
      </VStack>
    </Box>
  );
};
