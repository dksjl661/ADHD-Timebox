"use client";

import { useState, useRef, useEffect } from "react";
import { api } from "../utils/api";

interface Message {
  role: "user" | "agent";
  content: string;
}

interface ChatInterfaceProps {
  isDark: boolean;
}

export const ChatInterface = ({ isDark }: ChatInterfaceProps) => {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState<Message[]>([
    { role: "agent", content: "Hi! I'm your Orchestrator. How can I help you organize your tasks today?" }
  ]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isOpen]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading) {
      return;
    }

    const userMessage = input.trim();
    setMessages((prev) => [...prev, { role: "user", content: userMessage }]);
    setInput("");
    setIsLoading(true);

    try {
      const result = await api.chat(userMessage);
      setMessages((prev) => [
        ...prev,
        { role: "agent", content: result.response },
      ]);
    } catch (error) {
      console.error("Chat error:", error);
      setMessages((prev) => [
        ...prev,
        { role: "agent", content: "Sorry, I encountered an error communicating with the backend." },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="fixed bottom-6 right-6 z-50 flex flex-col items-end">
      {/* Chat Window */}
      {isOpen && (
        <div
          className={`mb-4 w-96 h-[500px] rounded-2xl shadow-2xl flex flex-col overflow-hidden border ${
            isDark
              ? "bg-slate-900 border-slate-700 text-slate-200"
              : "bg-white border-slate-200 text-slate-800"
          }`}
        >
          {/* Header */}
          <div
            className={`p-4 flex justify-between items-center border-b ${
              isDark ? "bg-slate-800 border-slate-700" : "bg-slate-50 border-slate-100"
            }`}
          >
            <h3 className="font-semibold text-sm">Orchestrator Chat</h3>
            <button
              onClick={() => setIsOpen(false)}
              className={`p-1 rounded hover:bg-opacity-20 ${
                isDark ? "hover:bg-slate-600" : "hover:bg-slate-200"
              }`}
            >
              <svg
                className="w-4 h-4"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M6 18L18 6M6 6l12 12"
                />
              </svg>
            </button>
          </div>

          {/* Messages */}
          <div className="flex-1 overflow-y-auto p-4 space-y-4 custom-scrollbar">
            {messages.map((msg, idx) => (
              <div
                key={idx}
                className={`flex ${
                  msg.role === "user" ? "justify-end" : "justify-start"
                }`}
              >
                <div
                  className={`max-w-[85%] rounded-2xl px-4 py-2 text-sm leading-relaxed whitespace-pre-wrap ${
                    msg.role === "user"
                      ? "bg-indigo-600 text-white rounded-br-none"
                      : isDark
                      ? "bg-slate-800 text-slate-200 rounded-bl-none"
                      : "bg-slate-100 text-slate-800 rounded-bl-none"
                  }`}
                >
                  {msg.content}
                </div>
              </div>
            ))}
            {isLoading && (
              <div className="flex justify-start">
                 <div
                  className={`max-w-[85%] rounded-2xl px-4 py-2 text-sm ${
                     isDark
                      ? "bg-slate-800 text-slate-400 rounded-bl-none"
                      : "bg-slate-100 text-slate-500 rounded-bl-none"
                  }`}
                >
                  Thinking...
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Input */}
          <form
            onSubmit={handleSubmit}
            className={`p-4 border-t ${
              isDark ? "border-slate-700 bg-slate-800" : "border-slate-100 bg-slate-50"
            }`}
          >
            <div className="relative">
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="Ask me to schedule something..."
                className={`w-full rounded-full pl-4 pr-10 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 ${
                  isDark
                    ? "bg-slate-950 text-slate-200 border-slate-700 border placeholder-slate-500"
                    : "bg-white text-slate-800 border-slate-200 border placeholder-slate-400"
                }`}
              />
              <button
                type="submit"
                disabled={isLoading || !input.trim()}
                className={`absolute right-1 top-1 p-1.5 rounded-full transition-colors ${
                  !input.trim()
                    ? "text-slate-400 cursor-not-allowed"
                    : "text-indigo-500 hover:bg-indigo-50"
                }`}
              >
                <svg
                  className="w-5 h-5 transform rotate-90"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8"
                  />
                </svg>
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Toggle Button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-14 h-14 rounded-full bg-indigo-600 hover:bg-indigo-500 text-white shadow-lg flex items-center justify-center transition-all transform hover:scale-105"
      >
        {isOpen ? (
          <svg
            className="w-6 h-6"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M19 9l-7 7-7-7"
            />
          </svg>
        ) : (
          <svg
            className="w-6 h-6"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z"
            />
          </svg>
        )}
      </button>
    </div>
  );
};
