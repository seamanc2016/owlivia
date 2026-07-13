"use client";

import {
  Conversation,
  ConversationContent,
  ConversationDownload,
  ConversationEmptyState,
  ConversationScrollButton,
} from "@/components/ai-elements/conversation";
import {
  PromptInput,
  PromptInputTextarea,
  PromptInputSubmit,
} from "@/components/ai-elements/prompt-input";
import {
  Message,
  MessageContent,
  MessageResponse,
} from "@/components/ai-elements/message";
import { Suggestion, Suggestions } from "@/components/ai-elements/suggestion";
import { useState } from "react";
import { useChat } from "@ai-sdk/react";
import { Button } from "@/components/ui/button";
import { Sidebar } from "lucide-react";





const suggestions = [
  "Graduation",
  "Forms",
  "Degree Requirements",
  "Academic Calendar",
  "Contact Advisor"
];

const ChatPage = () => {
  const [input, setInput] = useState("");
  const [state, setState] = useState("default")
  const { id, messages, sendMessage, status } = useChat();

  console.log(messages);

  const handleSubmit = (message) => {
    if (message.text.trim()) {
      sendMessage({ text: message.text });
      setInput("");
    }
  };

  const handleSuggestionClick = (suggestion) => {
    sendMessage({ text: suggestion });
  };

  return (
    <>
      <div className="h-screen bg-blue-200">
        <div className="flex flex-col h-full justify-between">
          {/* Top bar*/}
          <div className="bg-primary text-primary-foreground flex justify-between items-center p-2">
            <div className="font-bold text-xl">Owlivia</div>
            <Button className="bg-transparent">
              <Sidebar />
            </Button>
          </div>
          {/* Centered content*/}
          <div className="flex flex-col bg-red-200 h-full items-center">
            <Conversation className="bg-green-300 w-full">
              <ConversationContent className="h-full">
                {messages.length === 0 ? (
                  <ConversationEmptyState
                    icon={
                      <img
                        src="/logo_fau_blue.png"
                        alt="Owlivia Thumbs Up"
                        className="size-30 md:size-50 "
                      />}
                    title="Start a conversation"
                    description="How can Owlivia help you today?"
                  />
                ) : (
                  messages.map((message) => (
                    <Message from={message.role} key={message.id}>
                      <MessageContent>
                        {message.parts.map((part, i) => {
                          switch (part.type) {
                            case "text": // we don't use any reasoning or tool calls in this example
                              return (
                                <MessageResponse key={`${message.id}-${i}`}>
                                  {part.text}
                                </MessageResponse>
                              );
                            default:
                              return null;
                          }
                        })}
                      </MessageContent>
                    </Message>
                  ))
                )}
              </ConversationContent>
              {/* <ConversationDownload messages={messages} /> */}
              <ConversationScrollButton />
            </Conversation>
          </div>
          <div className="bg-purple-200 p-2">
            {messages.length === 0 && (
              <Suggestions className="overflow-x-auto">
                {suggestions.map((suggestion) => (
                  <Suggestion
                    key={suggestion}
                    onClick={handleSuggestionClick}
                    suggestion={suggestion}
                    className="bg-primary text-primary-foreground"
                  />
                ))}
              </Suggestions>

            )}

            <PromptInput
              onSubmit={handleSubmit}
              className="my-2 w-full max-w-2xl mx-auto relative"
            >
              <PromptInputTextarea
                value={input}
                placeholder="Type something..."
                onChange={(e) => setInput(e.currentTarget.value)}
                className="pr-12 min-h-0 bg-amber-300"
              />
              <PromptInputSubmit
                status={status === "streaming" ? "streaming" : "ready"}
                disabled={!input.trim()}
                className="absolute bottom-1 right-1 rounded-full"
              />
            </PromptInput>

            {/* <p className="text-xs text-center">
            Owlivia is AI and can make mistakes. Please double check all answers provided.
          </p> */}
          </div>
        </div>
      </div>
    </>
  );
};

export default ChatPage;