import React, { useState, useRef, useEffect } from "react";
import {
  Box,
  Flex,
  VStack,
  HStack,
  Text,
  Input,
  Button,
  IconButton,
  Grid,
  Image as ChakraImage,
} from "@chakra-ui/react";
import {
  Send,
  Sparkles,
  Plane,
  Map,
  Calendar,
  DollarSign,
  Mic,
  Image,
  Paperclip,
  X,
} from "lucide-react";

import { createFileRoute } from "@tanstack/react-router";

interface Message {
  id: number;
  type: "ai" | "user";
  text: string;
  files?: FileData[];
  timestamp: Date;
}

interface FileData {
  name: string;
  type: string;
  size: number;
  url: string;
}

interface QuickAction {
  icon: React.ElementType;
  text: string;
  color: string;
}

export const Route = createFileRoute("/chat")({
  component: TravyaChatInterface,
});

export default function TravyaChatInterface() {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: 1,
      type: "ai",
      text: "Hi! I'm your AI travel assistant. Where would you like to go? 🌍",
      timestamp: new Date(),
    },
  ]);
  const [input, setInput] = useState("");
  const [isTyping, setIsTyping] = useState(false);
  const [attachedFiles, setAttachedFiles] = useState<FileData[]>([]);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const quickActions: QuickAction[] = [
    {
      icon: Plane,
      text: "Plan a trip",
      color: "linear(to-br, blue.500, cyan.500)",
    },
    {
      icon: Map,
      text: "Find destinations",
      color: "linear(to-br, purple.500, pink.500)",
    },
    {
      icon: Calendar,
      text: "Weekend getaway",
      color: "linear(to-br, orange.500, red.500)",
    },
    {
      icon: DollarSign,
      text: "Budget travel",
      color: "linear(to-br, green.500, green.400)",
    },
  ];

  const handleSend = () => {
    if (!input.trim() && attachedFiles.length === 0) return;

    const userMessage: Message = {
      id: messages.length + 1,
      type: "user",
      text: input || "",
      files: attachedFiles,
      timestamp: new Date(),
    };

    setMessages([...messages, userMessage]);
    setInput("");
    setAttachedFiles([]);
    setIsTyping(true);

    setTimeout(() => {
      let responseText = "Great! ";
      if (attachedFiles.length > 0) {
        if (attachedFiles[0].type.startsWith("image/")) {
          responseText +=
            "I can see your image. Let me analyze this destination and find similar places for you! ";
        } else {
          responseText +=
            "I've received your document. Let me process that information. ";
        }
      }
      responseText +=
        "Let me search for the best options for you. I'll create itinerary based on your preferences.";

      const aiMessage: Message = {
        id: messages.length + 2,
        type: "ai",
        text: responseText,
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, aiMessage]);
      setIsTyping(false);
    }, 1500);
  };

  const handleQuickAction = (text: string) => {
    setInput(text);
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || []);
    const fileData: FileData[] = files.map((file) => ({
      name: file.name,
      type: file.type,
      size: file.size,
      url: URL.createObjectURL(file),
    }));
    setAttachedFiles([...attachedFiles, ...fileData]);
  };

  const removeFile = (index: number) => {
    setAttachedFiles(attachedFiles.filter((_, i) => i !== index));
  };

  const getFileIcon = (type: string) => {
    if (type.startsWith("image/")) return <Image size={16} />;
    return <Paperclip size={16} />;
  };

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return bytes + " B";
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + " KB";
    return (bytes / (1024 * 1024)).toFixed(1) + " MB";
  };

  return (
    <Flex
      direction="column"
      h="100vh"
      bgGradient="linear(to-br, gray.50, gray.100)"
    >
      {/* header */}
      <Box
        bg="white"
        borderBottom="1px"
        borderColor="gray.200"
        px={4}
        py={4}
        shadow="sm"
      >
        <Flex maxW="4xl" mx="auto" align="center" gap={3}>
          <Flex
            w="40px"
            h="40px"
            bgGradient="linear(to-br, cyan.500, blue.600)"
            borderRadius="full"
            align="center"
            justify="center"
          >
            <Sparkles size={20} color="white" />
          </Flex>
          <Box>
            <Text fontSize="lg" fontWeight="semibold" color="gray.800">
              Travya AI
            </Text>
            <Text fontSize="xs" color="gray.500">
              Your intelligent travel companion
            </Text>
          </Box>
        </Flex>
      </Box>

      {/* Messages Container */}
      <Box flex="1" overflowY="auto" px={4} py={6}>
        <VStack maxW="4xl" mx="auto" spaceY={4} align="stretch">
          {messages.map((message) => (
            <Flex
              key={message.id}
              justify={message.type === "user" ? "flex-end" : "flex-start"}
            >
              <Box
                maxW={{ base: "80%", md: "70%" }}
                borderRadius="2xl"
                px={4}
                py={3}
                bg={
                  message.type === "user"
                    ? "linear-gradient(to right, var(--chakra-colors-cyan-500), var(--chakra-colors-blue-600))"
                    : "white"
                }
                color={message.type === "user" ? "white" : "gray.800"}
                shadow={message.type === "user" ? "none" : "sm"}
                border={message.type === "user" ? "none" : "1px"}
                borderColor="gray.100"
              >
                {/* File Attachments */}
                {message.files && message.files.length > 0 && (
                  <VStack mb={2} spaceY={2} align="stretch">
                    {message.files.map((file, idx) => (
                      <Box key={idx}>
                        {file.type.startsWith("image/") ? (
                          <ChakraImage
                            src={file.url}
                            alt={file.name}
                            borderRadius="lg"
                            maxH="192px"
                            w="full"
                            objectFit="cover"
                          />
                        ) : (
                          <Flex
                            align="center"
                            gap={2}
                            px={3}
                            py={2}
                            borderRadius="lg"
                            bg={
                              message.type === "user"
                                ? "whiteAlpha.200"
                                : "gray.100"
                            }
                          >
                            <Paperclip size={16} />
                            <Text fontSize="sm" truncate>
                              {file.name}
                            </Text>
                          </Flex>
                        )}
                      </Box>
                    ))}
                  </VStack>
                )}

                {message.text && (
                  <Text
                    fontSize={{ base: "sm", md: "md" }}
                    lineHeight="relaxed"
                  >
                    {message.text}
                  </Text>
                )}

                <Text
                  fontSize="xs"
                  mt={1}
                  color={message.type === "user" ? "cyan.100" : "gray.400"}
                >
                  {message.timestamp.toLocaleTimeString([], {
                    hour: "2-digit",
                    minute: "2-digit",
                  })}
                </Text>
              </Box>
            </Flex>
          ))}

          {/* Typing Indicator */}
          {isTyping && (
            <Flex justify="flex-start">
              <Box
                bg="white"
                borderRadius="2xl"
                px={4}
                py={3}
                shadow="sm"
                border="1px"
                borderColor="gray.100"
              >
                <HStack spaceX={1}>
                  <Box
                    w="8px"
                    h="8px"
                    bg="gray.400"
                    borderRadius="full"
                    animation="bounce 1s infinite"
                    style={{ animationDelay: "0ms" }}
                  />
                  <Box
                    w="8px"
                    h="8px"
                    bg="gray.400"
                    borderRadius="full"
                    animation="bounce 1s infinite"
                    style={{ animationDelay: "150ms" }}
                  />
                  <Box
                    w="8px"
                    h="8px"
                    bg="gray.400"
                    borderRadius="full"
                    animation="bounce 1s infinite"
                    style={{ animationDelay: "300ms" }}
                  />
                </HStack>
              </Box>
            </Flex>
          )}

          <div ref={messagesEndRef} />
        </VStack>
      </Box>

      {/* Quick Actions buttons */}
      {messages.length <= 1 && (
        <Box px={4} pb={4}>
          <Box maxW="4xl" mx="auto">
            <Text fontSize="xs" color="gray.500" mb={3} textAlign="center">
              Quick actions
            </Text>
            <Grid
              templateColumns={{ base: "repeat(2, 1fr)", md: "repeat(4, 1fr)" }}
              gap={2}
            >
              {quickActions.map((action, index) => (
                <Button
                  key={index}
                  onClick={() => handleQuickAction(action.text)}
                  variant="outline"
                  justifyContent="flex-start"
                  h="auto"
                  py={2}
                  px={3}
                  bg="white"
                  borderColor="gray.200"
                  _hover={{ borderColor: "gray.300", shadow: "sm" }}
                >
                  <HStack spaceX={2}>
                    <Flex
                      w="32px"
                      h="32px"
                      bgGradient={action.color}
                      borderRadius="lg"
                      align="center"
                      justify="center"
                      flexShrink={0}
                    >
                      <action.icon size={16} color="white" />
                    </Flex>
                    <Text fontSize="sm" textAlign="left" color="gray.700">
                      {action.text}
                    </Text>
                  </HStack>
                </Button>
              ))}
            </Grid>
          </Box>
        </Box>
      )}

      {/* File Preview */}
      {attachedFiles.length > 0 && (
        <Box px={4} pb={2}>
          <Box
            maxW="4xl"
            mx="auto"
            bg="white"
            borderRadius="lg"
            border="1px"
            borderColor="gray.200"
            p={3}
          >
            <Flex flexWrap="wrap" gap={2}>
              {attachedFiles.map((file, index) => (
                <Box key={index} position="relative" role="group">
                  {file.type.startsWith("image/") ? (
                    <Box position="relative">
                      <ChakraImage
                        src={file.url}
                        alt={file.name}
                        h="64px"
                        w="64px"
                        objectFit="cover"
                        borderRadius="lg"
                      />
                      {/* remove attavhments */}
                      <IconButton
                        aria-label="Remove file"
                        size="xs"
                        position="absolute"
                        top="-8px"
                        right="-8px"
                        borderRadius="full"
                        colorScheme="red"
                        opacity={1}
                        zIndex={10}
                        bg="red.500"
                        color="white"
                        onClick={() => removeFile(index)}
                      >
                        <X size={12} />
                      </IconButton>
                    </Box>
                  ) : (
                    <Box position="relative">
                      <Flex
                        align="center"
                        gap={2}
                        bg="gray.100"
                        px={3}
                        py={2}
                        borderRadius="lg"
                        pr={8}
                      >
                        {getFileIcon(file.type)}
                        <Box fontSize="xs">
                          <Text
                            fontWeight="medium"
                            color="gray.700"
                            truncate
                            maxW="128px"
                          >
                            {file.name}
                          </Text>
                          <Text color="gray.500">
                            {formatFileSize(file.size)}
                          </Text>
                        </Box>
                      </Flex>
                      <IconButton
                        aria-label="Remove file"
                        size="xs"
                        position="absolute"
                        top="-8px"
                        right="-8px"
                        borderRadius="full"
                        colorScheme="red"
                        opacity={0}
                        _groupHover={{ opacity: 1 }}
                        onClick={() => removeFile(index)}
                      >
                        <X size={12} />
                      </IconButton>
                    </Box>
                  )}
                </Box>
              ))}
            </Flex>
          </Box>
        </Box>
      )}

      {/* Input Area */}
      <Box bg="white" borderTop="1px" borderColor="gray.200" px={4} py={4}>
        <Box maxW="4xl" mx="auto">
          <Flex gap={2} align="flex-end">
            {/* Input Actions button for file i/p */}
            <HStack spaceX={1}>
              <Input
                ref={fileInputRef}
                type="file"
                multiple
                accept="image/*,.pdf,.doc,.docx"
                onChange={handleFileSelect}
                display="none"
              />
              <IconButton
                aria-label="Attach file"
                onClick={() => fileInputRef.current?.click()}
                bg="gray.100"
                _hover={{ bg: "gray.200" }}
                borderRadius="full"
                color="gray.600"
              >
                <Paperclip size={20} />
              </IconButton>
            </HStack>

            {/* Text */}
            <Input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Tell me about your dream trip..."
              flex="1"
              bg="gray.50"
              border="1px"
              borderColor="gray.200"
              borderRadius="full"
              _focus={{
                outline: "none",
                ring: 2,
                ringColor: "cyan.500",
                borderColor: "transparent",
              }}
              color="gray.800"
              _placeholder={{ color: "gray.400" }}
            />

            {/* Send */}
            <IconButton
              aria-label="Send message"
              onClick={handleSend}
              disabled={!input.trim() && attachedFiles.length === 0}
              bgGradient="linear(to-r, cyan.500, blue.600)"
              color="white"
              borderRadius="full"
              w="48px"
              h="48px"
              _hover={{ shadow: "lg", transform: "scale(1.05)" }}
              _disabled={{
                opacity: 0.5,
                cursor: "not-allowed",
                _hover: { transform: "none" },
              }}
              transition="all 0.2s"
            >
              <Send size={20} />
            </IconButton>
          </Flex>
        </Box>
      </Box>
    </Flex>
  );
}
