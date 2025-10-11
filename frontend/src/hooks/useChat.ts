import { useState, useRef, useEffect } from "react";
import { Message, FileData } from "@/types/chat";

const useChat = () => {
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

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
      textareaRef.current.style.height = `${Math.min(
        textareaRef.current.scrollHeight,
        200
      )}px`;
    }
  }, [input]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  const handleSend = () => {
    if (!input.trim() && attachedFiles.length === 0) return;

    if (!chatStarted) {
      setChatStarted(true);
      const greetingMessage: Message = {
        id: 1,
        type: "ai",
        text: "Hi! I'm your AI travel assistant. Where would you like to go?",
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

  return {
    messages,
    input,
    setInput,
    isTyping,
    attachedFiles,
    setAttachedFiles,
    showMap,
    setShowMap,
    chatStarted,
    setChatStarted,
    mobileMapOpen,
    setMobileMapOpen,
    messagesEndRef,
    textareaRef,
    fileInputRef,
    handleSend,
    handleKeyPress,
    handleFileSelect,
    removeFile,
  };
};

export default useChat;
