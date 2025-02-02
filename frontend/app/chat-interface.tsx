"use client"

import { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Textarea } from "@/components/ui/textarea"
import { ScrollArea } from "@/components/ui/scroll-area"
import { cn } from "@/lib/utils"
import { useToast } from "@/hooks/use-toast"

interface Message {
  role: "agent" | "user"
  content: string
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
  const { toast } = useToast()

  useEffect(() => {
    setMessages([
      {
        role: "agent",
        content: "Hello, I'm an Codegen agent. Please let me know what type of codes do you want to generate?",
        timestamp: new Date().toLocaleTimeString(),
      }
    ])

    setIsLocked(false)
  }, [])

  const sendMessage = async () => {
    if (!input.trim() || isLoading) return

    const timestamp = new Date().toLocaleTimeString('zh-CN', {
      hour12: false,
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit"
    })

    const userMessage: Message = {
      role: "user",
      content: input,
      timestamp,
    }

    setMessages(prev => [...prev, userMessage])
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
      const response = await fetch(`${baseUrl}/chat/completions`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${apiToken}`,
        },
        body: JSON.stringify({
          model: 'gpt-4',
          messages: [{ role: 'user', content: input }],
          stream: true,
        }),
      })

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const reader = response.body?.getReader()
      if (!reader) throw new Error('No reader available')

      let agentMessage: Message = {
        role: "agent",
        content: "",
        timestamp,
      }

      setMessages(prev => [...prev, agentMessage])

      for await (const chunk of streamReader(reader)) {
        agentMessage.content += chunk
        setMessages(prev => [...prev.slice(0, -1), { ...agentMessage }])
      }

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

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage()
    }
  }

  return (
    <div className="flex-1 flex flex-col">
      <ScrollArea className="flex-1 p-4">
        <div className="space-y-4">
          {messages.map((message, index) => (
            <div key={index} className={cn("flex gap-2 max-w-[80%]", message.role === "user" && "ml-auto")}>
              {message.role === "agent" && <div className="h-8 w-8 rounded-full bg-primary flex-shrink-0" />}
              <div className="space-y-2">
                <div className="flex items-center gap-2">
                  <span className="text-sm font-medium">{message.role === "agent" ? "AI" : "You"}</span>
                  <span className="text-sm text-muted-foreground">{message.timestamp}</span>
                </div>
                <div className="p-3 bg-muted/50 rounded-lg">
                  <p className="text-sm whitespace-pre-wrap">{message.content}</p>
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
