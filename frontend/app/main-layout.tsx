"use client"

import { Button } from "@/components/ui/button"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { LayoutGrid, ChevronRight, Settings } from "lucide-react"
import { useState } from "react"
import type React from "react"
import { OpenAISettingsModal } from "./components/openai-settings-modal"

export default function Layout({ children }: { children: React.ReactNode }) {
  const [isRightPanelOpen, setIsRightPanelOpen] = useState(true)
  const [isSettingsOpen, setIsSettingsOpen] = useState(false)

  return (
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
            <h1 className="text-sm font-medium">Codegen</h1>
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
                  <div className="rounded-lg border p-3">
                    <p className="text-sm text-muted-foreground">Analyzing logical consistency...</p>
                    <p className="text-sm mt-2">Current assessment: High coherence in user statements.</p>
                  </div>
                </TabsContent>
                <TabsContent value="balthasar" className="mt-4 space-y-4">
                  <div className="rounded-lg border p-3">
                    <p className="text-sm text-muted-foreground">Evaluating emotional context...</p>
                    <p className="text-sm mt-2">Current assessment: Neutral emotional state detected.</p>
                  </div>
                </TabsContent>
                <TabsContent value="casper" className="mt-4 space-y-4">
                  <div className="rounded-lg border p-3">
                    <p className="text-sm text-muted-foreground">Processing behavioral patterns...</p>
                    <p className="text-sm mt-2">Current assessment: Standard interaction patterns observed.</p>
                  </div>
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
  )
}

