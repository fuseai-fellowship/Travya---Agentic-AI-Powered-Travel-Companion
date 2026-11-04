import React from "react";
import { Box, Flex } from "@chakra-ui/react";

import { FileData } from "@/types/chat";
import { FileAttachment } from "./fileAttachment";

interface FileAttachmentPreviewProps {
  files: FileData[];
  onRemoveFile: (index: number) => void;
}

export const FileAttachmentPreview: React.FC<FileAttachmentPreviewProps> = ({
  files,
  onRemoveFile,
}) => {
  return (
    <Box mb={3}>
      <Flex flexWrap="wrap" gap={2}>
        {files.map((file, index) => (
          <FileAttachment
            key={index}
            file={file}
            onRemove={() => onRemoveFile(index)}
            variant="preview"
          />
        ))}
      </Flex>
    </Box>
  );
};
