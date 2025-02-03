"use client"

import { Button } from "@/components/ui/button"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { LayoutGrid, ChevronRight, Settings } from "lucide-react"
import { useState, useEffect, useCallback } from "react"
import type React from "react"
import { OpenAISettingsModal } from "./components/openai-settings-modal"
import { cn } from "@/lib/utils"
import { MAGIContext } from "./contexts/magi-context"

// Agent IDs mapping
const AGENT_MAP = {
  "d37c1cc8-bcc4-4b73-9f49-a93a30971f2c": "melchior",
  "6634d0ec-d700-4a92-9066-4960a0f11927": "balthasar",
  "89cbe912-25d0-47b0-97da-b25622bfac0d": "casper"
} as const;

interface Message {
  requestId: string;
  content: string;
  timestamp: string;
}

interface AgentResponse {
  agentId: string;
  content: string;
  requestId: string;
  timestamp: string;
  status: "streaming" | "completed";
}

interface AgentState {
  messages: Message[];
  decision: "POSITIVE" | "NEGATIVE" | null;
}

export default function Layout({ children }: { children: React.ReactNode }) {
  const [isRightPanelOpen, setIsRightPanelOpen] = useState(true);
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);
  const [agentStates, setAgentStates] = useState<{
    melchior: AgentState;
    balthasar: AgentState;
    casper: AgentState;
  }>({
    melchior: { messages: [], decision: null },
    balthasar: { messages: [], decision: null },
    casper: { messages: [], decision: null }
  });

  // Extract decision from message content
  const extractDecision = (content: string): "POSITIVE" | "NEGATIVE" | null => {
    const match = content.match(/<decision>(POSITIVE|NEGATIVE)<\/decision>/);
    return match ? match[1] as "POSITIVE" | "NEGATIVE" : null;
  };

  // Handle agent response
  const handleAgentResponse = useCallback((event: CustomEvent<AgentResponse>) => {
    const { agentId, content, requestId, timestamp } = event.detail;
    const agentKey = AGENT_MAP[agentId as keyof typeof AGENT_MAP];
    
    if (!agentKey) return;

    setAgentStates(prev => {
      const agentState = prev[agentKey];
      const lastMessage = agentState.messages[agentState.messages.length - 1];

      if (lastMessage && lastMessage.requestId === requestId) {
        // Update existing message content
        const updatedMessages = [
          ...agentState.messages.slice(0, -1),
          {
            ...lastMessage,
            content: lastMessage.content + content
          }
        ];

        return {
          ...prev,
          [agentKey]: {
            ...agentState,
            messages: updatedMessages,
          }
        };
      } else {
        // Create new message
        return {
          ...prev,
          [agentKey]: {
            ...agentState,
            messages: [
              ...agentState.messages,
              {
                requestId,
                content,
                timestamp
              }
            ]
          }
        };
      }
    });
  }, []);

  // Handle agent completion
  const handleAgentComplete = useCallback((event: CustomEvent<AgentResponse>) => {
    const { agentId, requestId } = event.detail;
    const agentKey = AGENT_MAP[agentId as keyof typeof AGENT_MAP];
    
    if (!agentKey) return;

    setAgentStates(prev => {
      const agentState = prev[agentKey];
      const lastMessage = agentState.messages[agentState.messages.length - 1];
      
      if (lastMessage && lastMessage.requestId === requestId) {
        const decision = extractDecision(lastMessage.content);
        return {
          ...prev,
          [agentKey]: {
            ...agentState,
            decision
          }
        };
      }
      return prev;
    });
  }, []);

  // Add and remove event listeners
  useEffect(() => {
    const handleResponseEvent = (e: Event) => handleAgentResponse(e as CustomEvent<AgentResponse>);
    const handleCompleteEvent = (e: Event) => handleAgentComplete(e as CustomEvent<AgentResponse>);
    
    window.addEventListener('agent_response', handleResponseEvent);
    window.addEventListener('agent_complete', handleCompleteEvent);
    
    return () => {
      window.removeEventListener('agent_response', handleResponseEvent);
      window.removeEventListener('agent_complete', handleCompleteEvent);
    };
  }, [handleAgentResponse, handleAgentComplete]);

  return (
    <MAGIContext.Provider value={{ agentStates, setAgentStates }}>
      <div className="flex h-screen bg-background">
        {/* Sidebar */}
        <div className="w-48 border-r bg-muted/10 flex flex-col">
          <div className="p-4 border-b">
            <div className="flex items-center gap-2">
              <div className="h-6 w-6 rounded-full bg-primary" />
              <span className="font-semibold">MAGI System</span>
            </div>
          </div>

          {/* Main Navigation */}
          <div className="flex-1">
            <ScrollArea className="h-full">
              <div className="p-4">
                <nav className="space-y-2">
                  <Button variant="ghost" className="w-full justify-start">
                    <LayoutGrid className="mr-2 h-4 w-4" />
                    Demo1
                  </Button>
                </nav>
              </div>
            </ScrollArea>
          </div>

          {/* Bottom Settings Button */}
          <div className="p-4 border-t">
            <Button variant="ghost" className="w-full justify-start" onClick={() => setIsSettingsOpen(true)}>
              <Settings className="mr-2 h-4 w-4" />
              OpenAI Key
            </Button>
          </div>
        </div>

        {/* Main Content */}
        <div className="flex-1 flex">
          <div className="flex-1 flex flex-col">
            {/* Header */}
            <header className="h-14 border-b px-4 flex items-center">
              <h1 className="text-lg font-medium">Codegen</h1>
            </header>
            {children}
          </div>

          {/* Right Panel */}
          <div className={`border-l flex ${isRightPanelOpen ? "w-[500px]" : "w-0"} transition-all duration-300`}>
            <div className="flex-1 overflow-hidden">
              <div className="h-14 border-b px-4 flex items-center justify-between">
                <h2 className="font-medium">MAGI Judgements</h2>
                <Button variant="ghost" size="sm" className="h-8 w-8 p-0" onClick={() => setIsRightPanelOpen(false)}>
                  <ChevronRight className="h-4 w-4" />
                </Button>
              </div>
              <div className="p-4">
                <Tabs defaultValue="melchior" className="w-full">
                  <TabsList className="grid w-full grid-cols-3">
                    <TabsTrigger value="melchior">Melchior</TabsTrigger>
                    <TabsTrigger value="balthasar">Balthasar</TabsTrigger>
                    <TabsTrigger value="casper">Casper</TabsTrigger>
                  </TabsList>
                  <TabsContent value="melchior" className="mt-4 space-y-4">
                    {agentStates.melchior.decision && (
                      <div 
                        data-agent-decision={agentStates.melchior.decision}
                        className={cn(
                          "px-4 py-2 rounded-md text-sm font-medium",
                          agentStates.melchior.decision === "POSITIVE" 
                            ? "bg-green-100 text-green-800" 
                            : "bg-red-100 text-red-800"
                        )}>
                        Decision: {agentStates.melchior.decision}
                      </div>
                    )}
                    <ScrollArea className="h-[calc(100vh-200px)]">
                      {agentStates.melchior.messages.map((msg, index) => (
                        <div key={index} className="rounded-lg border p-3 mb-2">
                          <div className="text-xs text-muted-foreground mb-1">
                            {new Date(msg.timestamp).toLocaleTimeString()}
                          </div>
                          <p className="text-sm whitespace-pre-wrap" id="melchior-response">{msg.content}</p>
                        </div>
                      ))}
                    </ScrollArea>
                  </TabsContent>
                  <TabsContent value="balthasar" className="mt-4 space-y-4">
                    {agentStates.balthasar.decision && (
                      <div 
                        data-agent-decision={agentStates.balthasar.decision}
                        className={cn(
                          "px-4 py-2 rounded-md text-sm font-medium",
                          agentStates.balthasar.decision === "POSITIVE" 
                            ? "bg-green-100 text-green-800" 
                            : "bg-red-100 text-red-800"
                        )}>
                        Decision: {agentStates.balthasar.decision}
                      </div>
                    )}
                    <ScrollArea className="h-[calc(100vh-200px)]">
                      {agentStates.balthasar.messages.map((msg, index) => (
                        <div key={index} className="rounded-lg border p-3 mb-2">
                          <div className="text-xs text-muted-foreground mb-1">
                            {new Date(msg.timestamp).toLocaleTimeString()}
                          </div>
                          <p className="text-sm whitespace-pre-wrap" id="balthasar-response">{msg.content}</p>
                        </div>
                      ))}
                    </ScrollArea>
                  </TabsContent>
                  <TabsContent value="casper" className="mt-4 space-y-4">
                    {agentStates.casper.decision && (
                      <div 
                        data-agent-decision={agentStates.casper.decision}
                        className={cn(
                          "px-4 py-2 rounded-md text-sm font-medium",
                          agentStates.casper.decision === "POSITIVE" 
                            ? "bg-green-100 text-green-800" 
                            : "bg-red-100 text-red-800"
                        )}>
                        Decision: {agentStates.casper.decision}
                      </div>
                    )}
                    <ScrollArea className="h-[calc(100vh-200px)]">
                      {agentStates.casper.messages.map((msg, index) => (
                        <div key={index} className="rounded-lg border p-3 mb-2">
                          <div className="text-xs text-muted-foreground mb-1">
                            {new Date(msg.timestamp).toLocaleTimeString()}
                          </div>
                          <p className="text-sm whitespace-pre-wrap" id="casper-response">{msg.content}</p>
                        </div>
                      ))}
                    </ScrollArea>
                  </TabsContent>
                </Tabs>
              </div>
            </div>
            {!isRightPanelOpen && (
              <Button
                variant="ghost"
                size="sm"
                className="h-14 -ml-8 border-l bg-background"
                onClick={() => setIsRightPanelOpen(true)}
              >
                <ChevronRight className="h-4 w-4 rotate-180" />
              </Button>
            )}
          </div>
        </div>

        <OpenAISettingsModal open={isSettingsOpen} onOpenChange={setIsSettingsOpen} />
      </div>
    </MAGIContext.Provider>
  )
}
