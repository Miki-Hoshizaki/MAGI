"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"

export function OpenAISettingsModal({
  open,
  onOpenChange,
}: {
  open: boolean
  onOpenChange: (open: boolean) => void
}) {
  const [baseUrl, setBaseUrl] = useState(() => {
    if (typeof window !== 'undefined') {
      return localStorage.getItem('openai_base_url') || ""
    }
    return ""
  })
  const [token, setToken] = useState(() => {
    if (typeof window !== 'undefined') {
      return localStorage.getItem('openai_api_token') || ""
    }
    return ""
  })
  const [model, setModel] = useState(() => {
    if (typeof window !== 'undefined') {
      return localStorage.getItem('openai_model') || "gpt-4o"
    }
    return "gpt-4o"
  })

  const handleSave = () => {
    localStorage.setItem('openai_base_url', baseUrl)
    localStorage.setItem('openai_api_token', token)
    localStorage.setItem('openai_model', model)
    onOpenChange(false)
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[425px]">
        <DialogHeader>
          <DialogTitle>OpenAI Settings</DialogTitle>
          <DialogDescription>
            Configure your OpenAI API settings here. Make sure to keep your API key secure.
          </DialogDescription>
        </DialogHeader>
        <div className="grid gap-4 py-4">
          <div className="grid gap-2">
            <Label htmlFor="baseUrl">Base URL</Label>
            <Input
              id="baseUrl"
              placeholder="https://api.openai.com/v1"
              value={baseUrl}
              onChange={(e) => setBaseUrl(e.target.value)}
            />
          </div>
          <div className="grid gap-2">
            <Label htmlFor="token">API Token</Label>
            <Input id="token" type="password" value={token} onChange={(e) => setToken(e.target.value)} />
          </div>
          <div className="grid gap-2">
            <Label htmlFor="model">Model</Label>
            <Select value={model} onValueChange={setModel}>
              <SelectTrigger>
                <SelectValue placeholder="Select a model" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="gpt-4o">gpt-4o</SelectItem>
                <SelectItem value="gpt-4o-mini">gpt-4o-mini</SelectItem>
                <SelectItem value="claude-3.5-sonnet">claude-3.5-sonnet</SelectItem>
              </SelectContent>
            </Select>
            <Input 
              id="model" 
              placeholder="Custom model name" 
              value={model} 
              onChange={(e) => setModel(e.target.value)}
              className="mt-2"
            />
          </div>
        </div>
        <DialogFooter>
          <Button onClick={handleSave}>Save changes</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
