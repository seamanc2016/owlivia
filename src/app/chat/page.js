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

  const isLoading = status === "submitted" || status === "streaming";

  const lastMessage = messages.at(-1);

  const assistantHasStarted =
    lastMessage?.role === "assistant" &&
    lastMessage.parts.some(
      (part) =>
        part.type === "text" &&
        part.text.trim().length > 0
    );

  const showLoadingBuffer = isLoading && !assistantHasStarted;

  const handleSubmit = (message) => {
    if (isLoading) {
      return;
    }

    if (message.text.trim()) {
      sendMessage({ text: message.text });
      setInput("");
    }
  };

  const handleSuggestionClick = (suggestion) => {
    if (isLoading) {
      return;
    }

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
                  <>
                    {messages.map((message) => (
                      <Message
                        from={message.role}
                        key={message.id}
                        className={
                          message.role === "assistant"
                            ? "animate-in fade-in slide-in-from-bottom-2 duration-300"
                            : ""
                        }
                      >
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
                    ))}

                    {showLoadingBuffer && (
                      <Message
                        from="assistant"
                        className="animate-in fade-in slide-in-from-bottom-2 duration-300"
                      >
                        <div className="flex items-end gap-x-2">
                          <Avatar className="size-8 shrink-0">
                            <AvatarImage
                              src="/owlivia_avatar.png"
                              alt="Owlivia"
                            />
                            <AvatarFallback>O</AvatarFallback>
                          </Avatar>

                          <MessageContent>
                            <div
                              className="flex items-center gap-1 px-1 py-2"
                              aria-label="Owlivia is generating a response"
                            >
                              <span className="size-2 animate-bounce rounded-full bg-muted-foreground [animation-delay:-0.3s]" />
                              <span className="size-2 animate-bounce rounded-full bg-muted-foreground [animation-delay:-0.15s]" />
                              <span className="size-2 animate-bounce rounded-full bg-muted-foreground" />
                            </div>
                          </MessageContent>
                        </div>

                        <div className="mr-auto flex gap-1 text-xs text-muted-foreground">
                          <span className="font-medium">
                            Owlivia
                          </span>

                          <span>
                            Thinking...
                          </span>
                        </div>
                      </Message>
                    )}
                  </>
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
                    disabled={isLoading}
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
                placeholder={
                  isLoading
                    ? "Owlivia is responding..."
                    : "Type something..."
                }
                onChange={(e) => setInput(e.currentTarget.value)}
                disabled={isLoading}
                className="pr-12 min-h-0 bg-muted"
              />
              <PromptInputSubmit
                status={isLoading ? "streaming" : "ready"}
                disabled={isLoading || !input.trim()}
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