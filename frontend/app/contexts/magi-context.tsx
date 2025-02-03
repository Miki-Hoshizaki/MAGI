"use client"

import { createContext, useContext } from 'react';

interface Message {
  requestId: string;
  content: string;
  timestamp: string;
}

interface AgentState {
  messages: Message[];
  decision: "POSITIVE" | "NEGATIVE" | null;
}

interface MAGIContextType {
  agentStates: {
    melchior: AgentState;
    balthasar: AgentState;
    casper: AgentState;
  };
  setAgentStates: React.Dispatch<React.SetStateAction<{
    melchior: AgentState;
    balthasar: AgentState;
    casper: AgentState;
  }>>;
}

export const MAGIContext = createContext<MAGIContextType | null>(null);

export function useMAGI() {
  const context = useContext(MAGIContext);
  if (!context) {
    throw new Error('useMAGI must be used within a MAGIProvider');
  }
  return context;
}
