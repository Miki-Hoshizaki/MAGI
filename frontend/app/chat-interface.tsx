"use client"

import { useState, useEffect, useCallback } from "react"
import { Button } from "@/components/ui/button"
import { Textarea } from "@/components/ui/textarea"
import { ScrollArea } from "@/components/ui/scroll-area"
import { cn } from "@/lib/utils"
import { useToast } from "@/hooks/use-toast"
import { useMAGI } from "./contexts/magi-context"
import hash from 'hash.js'
import { v4 as uuidv4 } from 'uuid'

// WebSocket connection parameters
const GATEWAY_URL_PREFIX = typeof window !== 'undefined' ? window.location.host : ''
const APP_ID = "b75fce6f-e8af-4207-9c32-f8166afb4520";
const AGENT_IDS = {
  melchior: "d37c1cc8-bcc4-4b73-9f49-a93a30971f2c",
  balthasar: "6634d0ec-d700-4a92-9066-4960a0f11927",
  casper: "89cbe912-25d0-47b0-97da-b25622bfac0d"
};

interface Message {
  role: "agent" | "user" | "system"
  content: string
  id?: string
  pending?: boolean
  timestamp: string
}

async function* streamReader(reader: ReadableStreamDefaultReader<Uint8Array>) {
  const decoder = new TextDecoder()
  let buffer = ''

  while (true) {
    const { done, value } = await reader.read()
    if (done) break

    buffer += decoder.decode(value, { stream: true })
    const lines = buffer.split('\n')
    
    buffer = lines.pop() || ''
    
    for (const line of lines) {
      if (line.startsWith('data: ')) {
        const data = line.slice(6)
        if (data === '[DONE]') {
            // Show notification when message is complete
            return
        }
        try {
          const parsed = JSON.parse(data)
          const content = parsed.choices[0]?.delta?.content
          if (content) yield content
        } catch (e) {
          console.error('Failed to parse JSON:', e)
        }
      }
    }
  }
}

export default function ChatInterface() {
  const [input, setInput] = useState("")
  const [messages, setMessages] = useState<Message[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [isLocked, setIsLocked] = useState(false)
  const [ws, setWs] = useState<WebSocket | null>(null)
  const [magiJudgementId, setMagiJudgementId] = useState<string | null>(null)
  const [completedAgents, setCompletedAgents] = useState<Set<string>>(new Set())
  const { agentStates, setAgentStates } = useMAGI()
  const { toast } = useToast()

  // Generate authentication token
  const generateToken = useCallback(() => {
    const currentMinute = Math.floor(Date.now() / 60000);
    const secret = "magi-gateway-development-secret";
    const rawStr = `${APP_ID}${secret}${currentMinute}`;
    return hash.sha256().update(rawStr).digest('hex').slice(0, 10);
  }, []);

  // Connect to WebSocket
  const connectWebSocket = useCallback(async () => {
    const token = await generateToken();
    const wsProtocol = window.location.protocol === 'https:' ? 'wss://' : 'ws://';
    const wsUrl = `${wsProtocol}${GATEWAY_URL_PREFIX}/ws?appid=${APP_ID}&token=${token}`;
    const newWs = new WebSocket(wsUrl);

    newWs.onopen = () => {
      console.log("Connected to MAGI Gateway");
    };

    newWs.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.type === "agent_response") {
        const eventType = data.status === "completed" ? "agent_complete" : "agent_response";
        const customEvent = new CustomEvent(eventType, {
          detail: {
            agentId: data.agent_id,
            content: data.content || '',  // Ensure content is always a string
            requestId: data.request_id,
            timestamp: data.timestamp,
            status: data.status
          }
        });
        window.dispatchEvent(customEvent);
      }
      console.log("Received WebSocket message:", data);
    };

    newWs.onerror = (error) => {
      console.error("WebSocket error:", error);
    };

    newWs.onclose = () => {
      console.log("WebSocket connection closed");
      setTimeout(connectWebSocket, 5000); // Reconnect after 5 seconds
    };

    setWs(newWs);
  }, []);

  // Handle agent completion event
  useEffect(() => {
    const handleAgentComplete = (event: CustomEvent<any>) => {
      if (!magiJudgementId) return;
      
      const { requestId, agentId } = event.detail;
      if (requestId !== magiJudgementId) return;

      setCompletedAgents(prev => {
        const newSet = new Set(prev);
        newSet.add(agentId);
        return newSet;
      });
    };

    window.addEventListener('agent_complete', (event: Event) => handleAgentComplete(event as CustomEvent<{requestId: string, agentId: string}>));
    return () => window.removeEventListener('agent_complete', (event: Event) => handleAgentComplete(event as CustomEvent<{requestId: string, agentId: string}>));
  }, [magiJudgementId]);

  // Monitor the number of completed agents
  useEffect(() => {
    if (!magiJudgementId || completedAgents.size < 3) return;

    // Get all agent decisions from agentStates
    const decisions = [
      agentStates.melchior.decision,
      agentStates.balthasar.decision,
      agentStates.casper.decision
    ];
    
    // Ensure all agents have made a decision
    if (decisions.some(d => d === null)) return;
    
    const positiveCount = decisions.filter(d => d === 'POSITIVE').length;
    const finalDecision = positiveCount >= 2 ? 'POSITIVE' : 'NEGATIVE';

    // Update system message
    setMessages(prev => {
      const newMessages = [...prev];
      const magiMsgIndex = newMessages.findIndex(msg => msg.role === 'system' && msg.content.includes('MAGI System is processing'));
      if (magiMsgIndex !== -1) {
        newMessages[magiMsgIndex] = {
          role: 'system',
          content: `MAGI System has made a decision: ${finalDecision}`,
          timestamp: new Date().toISOString(),
        };
      }

      // Add colored decision result message
      newMessages.push({
        role: 'system',
        content: finalDecision === 'POSITIVE' 
          ? '<span style="color: #22c55e; font-weight: bold;">POSITIVE</span>' 
          : '<span style="color: #ef4444; font-weight: bold;">NEGATIVE</span>',
        timestamp: new Date().toISOString(),
      });

      return newMessages;
    });

    // If the decision is NEGATIVE, collect feedback and resubmit
    if (finalDecision === 'NEGATIVE') {
      // Get the original user request and AI output
      const userRequest = messages.find(msg => msg.role === 'user')?.content || '';
      
      // Get the last non-pending agent message
      const agentMessages = messages.filter(msg => msg.role === 'agent' && !msg.pending);
      const aiResponse = agentMessages[agentMessages.length - 1]?.content || '';

      // Get the last message from each agent
      const melchiorFeedback = agentStates.melchior.messages[agentStates.melchior.messages.length - 1]?.content || '';
      const balthasarFeedback = agentStates.balthasar.messages[agentStates.balthasar.messages.length - 1]?.content || '';
      const casperFeedback = agentStates.casper.messages[agentStates.casper.messages.length - 1]?.content || '';

      // Add a system message indicating resubmission
      setMessages(prev => [...prev, {
        role: 'system',
        content: 'Submitting MAGI results to AI',
        timestamp: new Date().toISOString(),
      }]);

      // Construct the resubmitted message
      const resubmitMessage = `
Original request:
${userRequest}

Previous AI response:
${aiResponse}

MAGI System Feedback:
Melchior:
${melchiorFeedback}

Balthasar:
${balthasarFeedback}

Casper:
${casperFeedback}

Please revise the code based on the feedback above.
`;

      // Send the resubmitted message
      handleSubmit(resubmitMessage);
    }
  }, [completedAgents, magiJudgementId, agentStates]);

  // Send message to WebSocket
  const sendToWebSocket = useCallback((userInput: string, response: string) => {
    if (!ws) return;

    const requestId = uuidv4();
    setMagiJudgementId(requestId);
    setCompletedAgents(new Set());

    // Reset all agent decisions to null
    setAgentStates(prev => ({
      melchior: { ...prev.melchior, decision: null },
      balthasar: { ...prev.balthasar, decision: null },
      casper: { ...prev.casper, decision: null }
    }));

    // Add system message
    setMessages(prev => [...prev, {
      role: 'system',
      content: 'MAGI System is processing...',
      id: requestId,
      pending: true,
      timestamp: new Date().toLocaleTimeString('en-US', {
        hour12: false,
        hour: "2-digit",
        minute: "2-digit",
        second: "2-digit"
      })
    }]);

    const message = {
      type: "agent_judgement",
      request_id: requestId,
      request: `<user_input>\n${userInput}\n</user_input>\n<response>\n${response}\n</response>`,
      timestamp: Date.now() / 1000,
      agents: [
        {agent_id: AGENT_IDS.melchior}, {agent_id: AGENT_IDS.balthasar}, {agent_id: AGENT_IDS.casper}
      ]
    };

    ws.send(JSON.stringify(message));
  }, [ws, setAgentStates]);

  useEffect(() => {
    setMessages([
      {
        role: "agent",
        content: "Hello, I'm an Codegen agent. Please let me know what type of codes do you want to generate?",
        timestamp: new Date().toLocaleTimeString('en-US', {
          hour12: false,
          hour: "2-digit",
          minute: "2-digit",
          second: "2-digit"
        })
      }
    ])

    connectWebSocket();
    setIsLocked(false)

    return () => {
      if (ws) {
        ws.close();
      }
    };
  }, [connectWebSocket])

  const sendMessage = async (message?: string) => {
    const messageToSend = message || input.trim();
    if (!messageToSend || isLoading) return
    
    const timestamp = new Date().toLocaleTimeString('en-US', {
      hour12: false,
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit"
    })

    const userMessage: Message = {
      role: "user",
      content: messageToSend,
      timestamp,
    }

    if (message) {
    const systemMessage: Message = {
        role: "system",
        content: "Regenerating...",
        timestamp,
    }
      setMessages(prev => [...prev, systemMessage])
    } else {
      setMessages(prev => [...prev, userMessage])
    }

    setInput("")
    setIsLoading(true)

    const baseUrl = localStorage.getItem('openai_base_url') || 'https://api.openai.com/v1'
    const apiToken = localStorage.getItem('openai_api_token')

    if (!apiToken) {
      setMessages(prev => [...prev, {
        role: "agent",
        content: "Please configure OpenAI API Token in settings first.",
        timestamp,
      }])
      setIsLoading(false)
      return
    }

    try {
      console.log('Sending message:', messageToSend)
      const response = await fetch(`${baseUrl}/chat/completions`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${apiToken}`,
        },
        body: JSON.stringify({
          model: 'gpt-4',
          messages: [
            { role: 'system', content: 'You are a programming expert. Generate and only generate codes without any explanation. If user provide your previors generated codes with reviewer feedbacks, use them as reference.' },
            { role: 'user', content: messageToSend }
          ],
          stream: true,
        }),
      })

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const reader = response.body?.getReader()
      if (!reader) throw new Error('No reader available')

      const agentMessage: Message = {
        role: "agent",
        content: '',
        pending: true,
        timestamp,
      }

      setMessages(prev => [...prev, { ...agentMessage }])

      for await (const chunk of streamReader(reader)) {
        agentMessage.content += chunk
        setMessages(prev => {
          const lastMessage = prev[prev.length - 1];
          if (lastMessage.role === 'agent') {
            return [...prev.slice(0, -1), { ...agentMessage }];
          }
          return [...prev, { ...agentMessage }];
        });
      }

      // Set message pending state to false
      agentMessage.pending = false;
      setMessages(prev => {
        const lastMessage = prev[prev.length - 1];
        if (lastMessage.role === 'agent') {
          return [...prev.slice(0, -1), { ...agentMessage }];
        }
        return [...prev, { ...agentMessage }];
      });

      // Output user input to console
      console.log('<user_input>')
      console.log(messageToSend)
      console.log('</user_input>\n')

      // Output complete model response to console
      console.log('<response>')
      console.log(agentMessage.content)
      console.log('</response>')

      // Send message to WebSocket
      sendToWebSocket(messageToSend, agentMessage.content);

      console.log('Stream complete')
      setIsLocked(true)


    } catch (error) {
      console.error('Error:', error)
      setMessages(prev => [...prev, {
        role: "agent",
        content: "Sorry, an error occurred. Please check your API settings and network connection.",
        timestamp,
      }])
    } finally {
      setIsLoading(false)
    }
  }

  const handleSubmit = async (message: string) => {
    setInput(message)
    await sendMessage(message)
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage()
    }
  }

  return (
    <div className="flex-1 flex flex-col h-[calc(100vh-4rem)]">
      <ScrollArea className="flex-1 p-4">
        <div className="space-y-4">
          {messages.map((message, index) => (
            <div key={index} className={cn("flex gap-2 max-w-[80%]", message.role === "user" ? "ml-auto flex-row-reverse" : "")}>
              {message.role === "agent" && <div className="h-8 w-8 rounded-full bg-primary flex-shrink-0" />}
              <div className="space-y-2">
                <div className="flex items-center gap-2">
                  <span className="text-sm font-medium">{message.role === "agent" ? "AI" : message.role === "system" ? "System" : "You"}</span>
                  <span className="text-sm text-muted-foreground">{message.timestamp}</span>
                </div>
                <div
                  className={cn(
                    "p-3 rounded-lg",
                    message.role === "user" ? "bg-primary text-primary-foreground" : message.role === "system" ? "bg-muted/50" : "bg-muted/50",
                  )}
                >
                  <p className="text-sm whitespace-pre-wrap" dangerouslySetInnerHTML={{ __html: message.content }}></p>
                </div>
              </div>
            </div>
          ))}
        </div>
      </ScrollArea>
      <div className="p-4 border-t">
        <div className="flex gap-2">
          <Textarea
            placeholder={isLocked ? "**Please fresh the page for next conversation.**" : "Enter your coding requirements..."}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            className="min-h-[44px] max-h-32"
            disabled={isLoading || isLocked}
          />
          <Button 
            className="px-8" 
            disabled={isLoading || isLocked}
          >
            {isLoading ? (isLocked ? "Sent" : "Sending...") : "Send"}
          </Button>
        </div>
      </div>
    </div>
  )
}
