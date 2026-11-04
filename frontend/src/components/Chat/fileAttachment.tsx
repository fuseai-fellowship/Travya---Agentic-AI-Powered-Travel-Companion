import React from "react";
import { Box, Flex, Text, IconButton, Image as ChakraImage } from "@chakra-ui/react";
import { Paperclip, X } from "lucide-react";
import { FileData } from "@/types/chat";

interface FileAttachmentProps {
  file: FileData;
  onRemove?: () => void;
  variant: "preview" | "message";
}

export const FileAttachment: React.FC<FileAttachmentProps> = ({
  file,
  onRemove,
  variant
}) => {
  const isPreview = variant === "preview";
  
  if (file.type.startsWith("image/")) {
    return (
      <Box position="relative">
        <ChakraImage
          src={file.url}
          alt={file.name}
          h={isPreview ? "80px" : "auto"}
          w={isPreview ? "80px" : "full"}
          maxH={!isPreview ? "200px" : undefined}
          objectFit="cover"
          borderRadius="lg"
          border="1px"
          borderColor="gray.200"
        />
        {isPreview && onRemove && (
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
            onClick={onRemove}
          >
            <X size={12} />
          </IconButton>
        )}
      </Box>
    );
  }

  return (
    <Box position="relative">
      <Flex
        align="center"
        gap={2}
        bg={isPreview ? "gray.50" : "gray.100"}
        px={3}
        py={2}
        borderRadius="lg"
        border="1px"
        borderColor="gray.200"
        pr={isPreview ? 8 : 3}
      >
        <Paperclip size={14} />
        <Text fontSize="sm" maxLines={1} maxW={isPreview ? "120px" : undefined}>
          {file.name}
        </Text>
      </Flex>
      {isPreview && onRemove && (
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
          onClick={onRemove}
        >
          <X size={12} />
        </IconButton>
      )}
    </Box>
  );
};