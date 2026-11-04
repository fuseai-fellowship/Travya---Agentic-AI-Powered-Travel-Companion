import { Flex, useBreakpointValue, Portal } from "@chakra-ui/react";
import useChat from "@/hooks/useChat";
import { ChatWelcomeScreen } from "./chatWelcome";
import { ChatInput } from "./chatInput";
import { MapSection } from "./mapSection";
import { ChatMessages } from "./chatMessages";

export default function TravyaChatInterface() {
  const {
    messages,
    input,
    setInput,
    isTyping,
    attachedFiles,
    // setAttachedFiles,
    showMap,
    // setShowMap,
    chatStarted,
    // setChatStarted,
    mobileMapOpen,
    setMobileMapOpen,
    handleSend,
    handleKeyPress,
    handleFileSelect,
    removeFile,
    messagesEndRef,
  } = useChat();

  const isMobile = useBreakpointValue({ base: true, md: false });
  const shouldShowMap = showMap && !isMobile;

  if (!chatStarted) {
    return (
      <ChatWelcomeScreen
        input={input}
        setInput={setInput}
        attachedFiles={attachedFiles}
        onSend={handleSend}
        onFileSelect={handleFileSelect}
        onRemoveFile={removeFile}
        onKeyPress={handleKeyPress}
      />
    );
  }

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
            <ChatMessages
              messages={messages}
              isTyping={isTyping}
              messagesEndRef={messagesEndRef}
            />

            <ChatInput
              input={input}
              setInput={setInput}
              attachedFiles={attachedFiles}
              onSend={handleSend}
              onFileSelect={handleFileSelect}
              onRemoveFile={removeFile}
              onKeyPress={handleKeyPress}
              showMap={showMap}
              isMobile={isMobile}
              onToggleMap={() => setMobileMapOpen(true)}
            />
          </Flex>

          {/* Desktop Map Section */}
          {shouldShowMap && <MapSection />}
        </Flex>
      </Flex>

      {/* Mobile Map Modal */}
      {mobileMapOpen && (
        <Portal>
          <MapSection isMobile onClose={() => setMobileMapOpen(false)} />
        </Portal>
      )}
    </>
  );
}
