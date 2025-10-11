export interface Message {
  id: number;
  type: "ai" | "user";
  text: string;
  files?: FileData[];
  timestamp: Date;
}

export interface FileData {
  name: string;
  type: string;
  size: number;
  url: string;
}

export interface ChatInputProps {
  input: string;
  setInput: (value: string) => void;
  attachedFiles: FileData[];
  onSend: () => void;
  onFileSelect: (e: React.ChangeEvent<HTMLInputElement>) => void;
  onRemoveFile: (index: number) => void;
  onKeyPress: (e: React.KeyboardEvent) => void;
  showMap?: boolean;
  isMobile?: boolean;
  onToggleMap?: () => void;
  variant?: "welcome" | "chat";
}