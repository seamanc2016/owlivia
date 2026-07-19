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
import {
  Avatar,
  AvatarFallback,
  AvatarImage,
} from "@/components/ui/avatar";
import { Suggestion, Suggestions } from "@/components/ai-elements/suggestion";
import { useRef, useState } from "react";
import { useChat } from "@ai-sdk/react";
import { Button } from "@/components/ui/button";
import { LogOut, Sidebar } from "lucide-react";
import Link from "next/link";
import { ChatNavbar } from "@/components/ui/chat-navbar";



const suggestions = [
  "Graduation",
  "Forms",
  "Degree Requirements",
  "Academic Calendar",
  "Contact Advisor"
];

const ChatPage = () => {
  const [input, setInput] = useState("");
  const { id, messages, sendMessage, status } = useChat();
  const messageTimestamps = useRef({});

  const handleSubmit = (message) => {
    if (message.text.trim()) {
      sendMessage({ text: message.text });
      setInput("");
    }
  };

  const handleSuggestionClick = (suggestion) => {
    sendMessage({ text: suggestion });
  };


  messages.forEach((message) => {
    if (!messageTimestamps.current[message.id]) {
      messageTimestamps.current[message.id] = new Date();
    }
  });

  return (
    <>
      <div className="h-screen">
        <div className="flex flex-col h-full bg-primary-foreground">
          {/* Top bar*/}
          <ChatNavbar />

          {/* Centered content*/}
          <div className="flex flex-col h-full items-center min-h-0 md:max-w-5xl w-full bg-primary-foreground mx-auto">
            <Conversation className={
              messages.length === 0 ?
                "flex-none bg-primary-foreground w-full min-h-0 my-auto" :
                "bg-primary-foreground w-full min-h-0 my-auto h-full"
            }>
              <ConversationContent>
                {messages.length === 0 ? (
                  <ConversationEmptyState
                    icon={
                      <img
                        src="/logo_fau_blue.png"
                        alt="Owlivia Logo"
                        className="size-30 md:size-50 "
                      />}
                    title="Start a conversation"
                    description="How can Owlivia help you today?"
                  />
                ) : (
                  messages.map((message) => (
                    <Message from={message.role} key={message.id}>
                      <div className="flex items-end gap-x-2">
                        {message.role === "assistant" && (
                          <Avatar className="size-8 shrink-0">
                            <AvatarImage
                              src="/owlivia_avatar.png"
                              alt="Owlivia"
                            />
                            <AvatarFallback>O</AvatarFallback>
                          </Avatar>
                        )}

                        <MessageContent>
                          {message.parts.map((part, i) => {
                            if (part.type !== "text") {
                              return null;
                            }

                            return (
                              <MessageResponse key={`${message.id}-${i}`}>
                                {part.text}
                              </MessageResponse>
                            );
                          })}
                        </MessageContent>
                      </div>

                      <div
                        className={
                          message.role === "assistant"
                            ? "mr-auto flex gap-1 text-xs text-muted-foreground"
                            : "ml-auto flex gap-1 text-xs text-muted-foreground"
                        }
                      >
                        <span className="font-medium">
                          {message.role === "assistant" ? "Owlivia" : "You"}
                        </span>

                        <span>
                          {messageTimestamps.current[
                            message.id
                          ]?.toLocaleTimeString([], {
                            hour: "numeric",
                            minute: "2-digit",
                          })}
                        </span>
                      </div>
                    </Message>
                  ))
                )}
              </ConversationContent>
              {/* <ConversationDownload messages={messages} /> */}
              <ConversationScrollButton />
            </Conversation>
          </div>
          <div className="py-2 md:mx-auto">
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
          </div>
          <div className="bg-primary px-2">
            <PromptInput
              onSubmit={handleSubmit}
              className="my-2 w-full max-w-5xl mx-auto relative rounded-full bg-primary-foreground"
            >
              <PromptInputTextarea
                value={input}
                placeholder="Type something..."
                onChange={(e) => setInput(e.currentTarget.value)}
                className="pr-12 min-h-0 bg-muted"
              />
              <PromptInputSubmit
                status={status === "streaming" ? "streaming" : "ready"}
                disabled={!input.trim()}
                className="absolute bottom-1 right-1 rounded-full"
              />
            </PromptInput>

            <p className="text-xs text-primary-foreground text-center py-1 hidden lg:block">
              Owlivia is AI and can make mistakes. Please double check all answers provided
            </p>
          </div>

        </div>
      </div>
    </>
  );
};

export default ChatPage;