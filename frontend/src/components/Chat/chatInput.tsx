import React, { useRef } from "react";
import { Box, Flex, Textarea, IconButton, Input } from "@chakra-ui/react";
import { Send, Paperclip, MapPin } from "lucide-react";

import { ChatInputProps } from "@/types/chat";
import { FileAttachmentPreview } from "./filePreview";

export const ChatInput: React.FC<ChatInputProps> = ({
  input,
  setInput,
  attachedFiles,
  onSend,
  onFileSelect,
  onRemoveFile,
  onKeyPress,
  showMap,
  isMobile,
  onToggleMap,
  variant = "chat",
}) => {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const isWelcomeVariant = variant === "welcome";
  const containerStyles = isWelcomeVariant
    ? {
        bg: "white",
        borderRadius: "2xl",
        border: "2px",
        borderColor: "gray.200",
        shadow: "lg",
        _focusWithin: {
          borderColor: "cyan.500",
          shadow: "0 0 0 3px rgba(6, 182, 212, 0.1)",
        },
      }
    : {
        bg: "gray.50",
        borderRadius: "2xl",
        border: "1px",
        borderColor: "gray.200",
        _focusWithin: {
          borderColor: "cyan.500",
          shadow: "0 0 0 1px var(--chakra-colors-cyan-500)",
        },
      };

  const wrapperStyles = isWelcomeVariant
    ? { px: 6, py: 4, bg: "white" }
    : { borderTop: "1px", borderColor: "gray.200", px: 6, py: 4, bg: "white" };

  return (
    <Box {...wrapperStyles} flexShrink={0}>
      <Box maxW="3xl" mx="auto">
        {/* File Preview */}
        {attachedFiles.length > 0 && (
          <FileAttachmentPreview
            files={attachedFiles}
            onRemoveFile={onRemoveFile}
          />
        )}

        <Flex align="flex-end" gap={2} p={2} {...containerStyles}>
          <Input
            ref={fileInputRef}
            type="file"
            multiple
            accept="image/*,.pdf,.doc,.docx"
            onChange={onFileSelect}
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
            onKeyPress={onKeyPress}
            placeholder={
              isWelcomeVariant
                ? "Describe your ideal vacation..."
                : "Message Travya..."
            }
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
              onClick={onToggleMap}
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
            onClick={onSend}
            disabled={!input.trim() && attachedFiles.length === 0}
            bg={
              input.trim() || attachedFiles.length > 0 ? "gray.900" : "gray.200"
            }
            color="white"
            borderRadius="xl"
            minW="44px"
            h="44px"
            _hover={
              input.trim() || attachedFiles.length > 0 ? { bg: "gray.800" } : {}
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
  );
};
