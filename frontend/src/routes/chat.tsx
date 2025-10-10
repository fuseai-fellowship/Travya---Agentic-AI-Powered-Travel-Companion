import React, { useState, useRef, useEffect } from "react";
import {
  Box,
  Flex,
  VStack,
  Text,
  Textarea,
  IconButton,
  Image as ChakraImage,
  Input,
  useBreakpointValue,
  Portal,
} from "@chakra-ui/react";
import { Send, Sparkles, Paperclip, X, MapPin } from "lucide-react";
import { isLoggedIn } from "@/hooks/useAuth";
import { createFileRoute, redirect } from "@tanstack/react-router";

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

export const Route = createFileRoute("/chat")({
  component: TravyaChatInterface,
  beforeLoad: async () => {
    if (!isLoggedIn()) {
      throw redirect({
        to: "/login",
      });
    }
  },
});

export default function TravyaChatInterface() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isTyping, setIsTyping] = useState(false);
  const [attachedFiles, setAttachedFiles] = useState<FileData[]>([]);
  const [showMap, setShowMap] = useState(false);
  const [chatStarted, setChatStarted] = useState(false);
  const [mobileMapOpen, setMobileMapOpen] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const isMobile = useBreakpointValue({ base: true, md: false });
  const shouldShowMap = showMap && !isMobile;

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 200)}px`;
    }
  }, [input]);

  const handleSend = () => {
    if (!input.trim() && attachedFiles.length === 0) return;

    // Start chat on first message
    if (!chatStarted) {
      setChatStarted(true);
      // Greeting
      const greetingMessage: Message = {
        id: 1,
        type: "ai",
        text: `Hi ! I'm your AI travel assistant. Where would you like to go?`,
        timestamp: new Date(),
      };
      setMessages([greetingMessage]);
    }

    const userMessage: Message = {
      id: messages.length + 1,
      type: "user",
      text: input,
      files: attachedFiles,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setAttachedFiles([]);
    setIsTyping(true);

    setTimeout(() => {
      let responseText = "";
      if (attachedFiles.length > 0) {
        if (attachedFiles[0].type.startsWith("image/")) {
          responseText =
            "I can see your image! That looks like an amazing destination. Let me find similar places for you.";
        } else {
          responseText =
            "I've received your document. Let me process that information.";
        }
      } else {
        responseText =
          "Great! Let me search for the best options for you. I'll create an itinerary based on your preferences.";
      }

      const aiMessage: Message = {
        id: messages.length + 2,
        type: "ai",
        text: responseText,
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, aiMessage]);
      setIsTyping(false);
      setShowMap(true);
    }, 1500);
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

  // Map Component (reusable for both desktop and mobile)
  const MapContent = () => (
    <>
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
    </>
  );

  // Initial before chat starts
  if (!chatStarted) {
    return (
      <Flex direction="column" align="center" justify="center" h="full" px={4}>
        <VStack spaceX={6} maxW="2xl" w="full">
          {/* Hero Section */}
          <VStack spaceX={3} textAlign="center">
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
              Tell me about your dream destination and I'll help plan your
              perfect trip
            </Text>
          </VStack>

          {/* Input Area */}
          <Box w="full">
            {/* File Preview */}
            {attachedFiles.length > 0 && (
              <Box mb={3}>
                <Flex flexWrap="wrap" gap={2}>
                  {attachedFiles.map((file, index) => (
                    <Box key={index} position="relative">
                      {file.type.startsWith("image/") ? (
                        <Box position="relative">
                          <ChakraImage
                            src={file.url}
                            alt={file.name}
                            h="80px"
                            w="80px"
                            objectFit="cover"
                            borderRadius="lg"
                            border="1px"
                            borderColor="gray.200"
                          />
                          <IconButton
                            aria-label="Remove file"
                            size="xs"
                            position="absolute"
                            top="-6px"
                            right="-6px"
                            borderRadius="full"
                            bg="gray.900"
                            color="white"
                            minW="20px"
                            h="20px"
                            _hover={{ bg: "gray.800" }}
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
                            bg="gray.50"
                            px={3}
                            py={2}
                            borderRadius="lg"
                            border="1px"
                            borderColor="gray.200"
                            pr={8}
                          >
                            <Paperclip size={14} />
                            <Text fontSize="sm" maxLines={1} maxW="120px">
                              {file.name}
                            </Text>
                          </Flex>
                          <IconButton
                            aria-label="Remove file"
                            size="xs"
                            position="absolute"
                            top="-6px"
                            right="-6px"
                            borderRadius="full"
                            bg="gray.900"
                            color="white"
                            minW="20px"
                            h="20px"
                            _hover={{ bg: "gray.800" }}
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
            )}

            <Flex
              align="flex-end"
              gap={2}
              bg="white"
              borderRadius="2xl"
              border="2px"
              borderColor="gray.200"
              p={2}
              shadow="lg"
              _focusWithin={{
                borderColor: "cyan.500",
                shadow: "0 0 0 3px rgba(6, 182, 212, 0.1)",
              }}
            >
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
                bg="transparent"
                color="gray.600"
                borderRadius="lg"
                minW="40px"
                h="40px"
                _hover={{ bg: "gray.100" }}
              >
                <Paperclip size={18} />
              </IconButton>
              <Textarea
                ref={textareaRef}
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="Describe your ideal vacation..."
                resize="none"
                border="none"
                _focus={{ outline: "none", boxShadow: "none" }}
                bg="transparent"
                color="gray.900"
                fontSize="md"
                px={3}
                py={2}
                minH="44px"
                maxH="200px"
                rows={1}
                _placeholder={{ color: "gray.500" }}
              />
              <IconButton
                aria-label="Send message"
                onClick={handleSend}
                disabled={!input.trim() && attachedFiles.length === 0}
                bg={
                  input.trim() || attachedFiles.length > 0
                    ? "gray.900"
                    : "gray.200"
                }
                color="white"
                borderRadius="xl"
                minW="44px"
                h="44px"
                _hover={
                  input.trim() || attachedFiles.length > 0
                    ? { bg: "gray.800" }
                    : {}
                }
                _disabled={{
                  opacity: 1,
                  cursor: "not-allowed",
                }}
                transition="all 0.2s"
              >
                <Send size={18} />
              </IconButton>
            </Flex>
          </Box>
        </VStack>
      </Flex>
    );
  }

  // After chat starts
  return (
    <>
      <Flex direction="column" h="full">
      
        <Flex flex="1" overflow="hidden" position="relative">
          {/* Chat Section */}
          <Flex
            direction="column"
            flex={shouldShowMap ? { base: "1", md: "0 0 50%" } : "1"}
            overflow="hidden"
          >
            {/* Messages Area */}
            <Box flex="1" overflowY="auto" px={6} py={6}>
              <VStack maxW="3xl" mx="auto" spaceX={6} align="stretch">
                {messages.map((message) => (
                  <Flex
                    key={message.id}
                    justify={
                      message.type === "user" ? "flex-end" : "flex-start"
                    }
                  >
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
                          <Text
                            fontSize="sm"
                            fontWeight="medium"
                            color="gray.700"
                          >
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
                          <VStack mb={3} spaceX={2} align="stretch">
                            {message.files.map((file, idx) => (
                              <Box key={idx}>
                                {file.type.startsWith("image/") ? (
                                  <ChakraImage
                                    src={file.url}
                                    alt={file.name}
                                    borderRadius="lg"
                                    maxH="200px"
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
                                    <Paperclip size={14} />
                                    <Text fontSize="sm" maxLines={1}>
                                      {file.name}
                                    </Text>
                                  </Flex>
                                )}
                              </Box>
                            ))}
                          </VStack>
                        )}

                        <Text
                          fontSize="md"
                          lineHeight="tall"
                          whiteSpace="pre-wrap"
                        >
                          {message.text}
                        </Text>
                      </Box>
                    </Box>
                  </Flex>
                ))}

                {/* Typing Indicator */}
                {isTyping && (
                  <Flex justify="flex-start">
                    <Box maxW="85%">
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
                        <Text
                          fontSize="sm"
                          fontWeight="medium"
                          color="gray.700"
                        >
                          Travya
                        </Text>
                      </Flex>
                      <Box bg="gray.50" borderRadius="2xl" px={4} py={3}>
                        <Flex gap={1}>
                          <Box
                            w="6px"
                            h="6px"
                            bg="gray.400"
                            borderRadius="full"
                            animation="bounce 1.4s infinite"
                            style={{ animationDelay: "0ms" }}
                          />
                          <Box
                            w="6px"
                            h="6px"
                            bg="gray.400"
                            borderRadius="full"
                            animation="bounce 1.4s infinite"
                            style={{ animationDelay: "200ms" }}
                          />
                          <Box
                            w="6px"
                            h="6px"
                            bg="gray.400"
                            borderRadius="full"
                            animation="bounce 1.4s infinite"
                            style={{ animationDelay: "400ms" }}
                          />
                        </Flex>
                      </Box>
                    </Box>
                  </Flex>
                )}

                <div ref={messagesEndRef} />
              </VStack>
            </Box>

            {/* Input Area */}
            <Box
              borderTop="1px"
              borderColor="gray.200"
              px={6}
              py={4}
              bg="white"
              flexShrink={0}
            >
              <Box maxW="3xl" mx="auto">
                {/* File Preview */}
                {attachedFiles.length > 0 && (
                  <Box mb={3}>
                    <Flex flexWrap="wrap" gap={2}>
                      {attachedFiles.map((file, index) => (
                        <Box key={index} position="relative">
                          {file.type.startsWith("image/") ? (
                            <Box position="relative">
                              <ChakraImage
                                src={file.url}
                                alt={file.name}
                                h="80px"
                                w="80px"
                                objectFit="cover"
                                borderRadius="lg"
                                border="1px"
                                borderColor="gray.200"
                              />
                              <IconButton
                                aria-label="Remove file"
                                size="xs"
                                position="absolute"
                                top="-6px"
                                right="-6px"
                                borderRadius="full"
                                bg="gray.900"
                                color="white"
                                minW="20px"
                                h="20px"
                                _hover={{ bg: "gray.800" }}
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
                                bg="gray.50"
                                px={3}
                                py={2}
                                borderRadius="lg"
                                border="1px"
                                borderColor="gray.200"
                                pr={8}
                              >
                                <Paperclip size={14} />
                                <Text fontSize="sm" maxLines={1} maxW="120px">
                                  {file.name}
                                </Text>
                              </Flex>
                              <IconButton
                                aria-label="Remove file"
                                size="xs"
                                position="absolute"
                                top="-6px"
                                right="-6px"
                                borderRadius="full"
                                bg="gray.900"
                                color="white"
                                minW="20px"
                                h="20px"
                                _hover={{ bg: "gray.800" }}
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
                )}

                <Flex
                  align="flex-end"
                  gap={2}
                  bg="gray.50"
                  borderRadius="2xl"
                  border="1px"
                  borderColor="gray.200"
                  p={2}
                  _focusWithin={{
                    borderColor: "cyan.500",
                    shadow: "0 0 0 1px var(--chakra-colors-cyan-500)",
                  }}
                >
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
                    bg="transparent"
                    color="gray.600"
                    borderRadius="lg"
                    minW="40px"
                    h="40px"
                    _hover={{ bg: "gray.100" }}
                  >
                    <Paperclip size={18} />
                  </IconButton>
                  <Textarea
                    ref={textareaRef}
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    onKeyPress={handleKeyPress}
                    placeholder="Message Travya..."
                    resize="none"
                    border="none"
                    _focus={{ outline: "none", boxShadow: "none" }}
                    bg="transparent"
                    color="gray.900"
                    fontSize="md"
                    px={3}
                    py={2}
                    minH="44px"
                    maxH="200px"
                    rows={1}
                    _placeholder={{ color: "gray.500" }}
                  />
                  {/* Map button for mobile */}
                  {isMobile && showMap && (
                    <IconButton
                      aria-label="Show map"
                      onClick={() => setMobileMapOpen(true)}
                      bg="transparent"
                      color="cyan.600"
                      borderRadius="lg"
                      minW="40px"
                      h="40px"
                      _hover={{ bg: "gray.100" }}
                    >
                      <MapPin size={18} />
                    </IconButton>
                  )}
                  <IconButton
                    aria-label="Send message"
                    onClick={handleSend}
                    disabled={!input.trim() && attachedFiles.length === 0}
                    bg={
                      input.trim() || attachedFiles.length > 0
                        ? "gray.900"
                        : "gray.200"
                    }
                    color="white"
                    borderRadius="xl"
                    minW="44px"
                    h="44px"
                    _hover={
                      input.trim() || attachedFiles.length > 0
                        ? { bg: "gray.800" }
                        : {}
                    }
                    _disabled={{
                      opacity: 1,
                      cursor: "not-allowed",
                    }}
                    transition="all 0.2s"
                  >
                    <Send size={18} />
                  </IconButton>
                </Flex>
              </Box>
            </Box>
          </Flex>

          {/* Desktop Map Section */}
          {shouldShowMap && (
            <Box
              flex="0 0 50%"
              bg="gray.50"
              position="relative"
              overflow="hidden"
              display={{ base: "none", md: "block" }}
              borderLeft="1px"
              borderColor="gray.200"
            >
              <MapContent />
            </Box>
          )}
        </Flex>
      </Flex>

      {/* Mobile Map Modal */}
      {mobileMapOpen && (
        <Portal>
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
                onClick={() => setMobileMapOpen(false)}
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
        </Portal>
      )}
    </>
  );
}
