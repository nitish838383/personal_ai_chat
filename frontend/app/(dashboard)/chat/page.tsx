"use client";

import { useEffect, useState, useRef } from "react";
import { chatApi } from "@/lib/api";
import { Send, Plus, Trash2 } from "lucide-react";
import ReactMarkdown from "react-markdown";

export default function ChatPage() {
  const [conversations, setConversations] = useState<any[]>([]);
  const [activeId, setActiveId] = useState<string | null>(null);
  const [messages, setMessages] = useState<any[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  const loadConversations = () =>
    chatApi.listConversations().then(setConversations).catch(() => {});

  useEffect(() => {
    loadConversations();
  }, []);

  useEffect(() => {
    if (activeId) {
      chatApi.getConversation(activeId).then((c) => {
        setMessages(c.messages || []);
      }).catch(() => {});
    } else {
      setMessages([]);
    }
  }, [activeId]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  async function send() {
    if (!input.trim() || loading) return;
    const text = input.trim();
    setInput("");
    setLoading(true);
    // Optimistic user message
    setMessages((prev) => [
      ...prev,
      { id: "tmp-user", role: "user", content: text, created_at: new Date().toISOString() },
    ]);
    try {
      const reply = await chatApi.sendMessage(text, activeId || undefined);
      if (!activeId) {
        setActiveId(reply.conversation_id);
        loadConversations();
      }
      setMessages((prev) => [
        ...prev.filter((m) => m.id !== "tmp-user"),
        { id: "tmp-user2", role: "user", content: text, created_at: new Date().toISOString() },
        reply,
      ]);
      // Reload full conversation for consistency
      if (reply.conversation_id) {
        const c = await chatApi.getConversation(reply.conversation_id);
        setMessages(c.messages || []);
        setActiveId(reply.conversation_id);
      }
    } catch (err: any) {
      setMessages((prev) => [
        ...prev,
        { id: "err", role: "assistant", content: `Error: ${err.message}`, created_at: new Date().toISOString() },
      ]);
    } finally {
      setLoading(false);
    }
  }

  async function newChat() {
    setActiveId(null);
    setMessages([]);
  }

  async function deleteConv(id: string) {
    await chatApi.deleteConversation(id);
    if (activeId === id) {
      setActiveId(null);
      setMessages([]);
    }
    loadConversations();
  }

  return (
    <div className="flex h-full">
      {/* Conversation list */}
      <div className="w-72 border-r border-slate-800 flex flex-col">
        <div className="p-4 border-b border-slate-800">
          <button
            onClick={newChat}
            className="flex w-full items-center justify-center gap-2 rounded-lg bg-cyan-600 py-2 text-sm font-medium hover:bg-cyan-500 transition"
          >
            <Plus className="h-4 w-4" /> New chat
          </button>
        </div>
        <div className="flex-1 overflow-y-auto p-2 space-y-1">
          {conversations.map((c) => (
            <div
              key={c.id}
              className={`group flex items-center gap-2 rounded-lg px-3 py-2.5 text-sm cursor-pointer transition ${
                activeId === c.id ? "bg-slate-800 text-white" : "text-slate-400 hover:bg-slate-900"
              }`}
              onClick={() => setActiveId(c.id)}
            >
              <span className="flex-1 truncate">{c.title}</span>
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  deleteConv(c.id);
                }}
                className="opacity-0 group-hover:opacity-100 text-slate-500 hover:text-red-400"
              >
                <Trash2 className="h-3.5 w-3.5" />
              </button>
            </div>
          ))}
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 flex flex-col">
        <div className="flex-1 overflow-y-auto p-6 space-y-4">
          {messages.length === 0 && (
            <div className="flex h-full items-center justify-center text-slate-500">
              <div className="text-center space-y-2">
                <p className="text-lg">How can I help you today?</p>
                <p className="text-sm">Ask about your schedule, emails, tasks, or anything else.</p>
              </div>
            </div>
          )}
          {messages.map((m) => (
            <div
              key={m.id}
              className={`flex ${m.role === "user" ? "justify-end" : "justify-start"}`}
            >
              <div
                className={`max-w-[75%] rounded-2xl px-4 py-3 text-sm ${
                  m.role === "user"
                    ? "bg-cyan-600 text-white"
                    : "bg-slate-800 text-slate-200"
                }`}
              >
                {m.role === "assistant" ? (
                  <ReactMarkdown className="prose prose-invert prose-sm max-w-none">
                    {m.content}
                  </ReactMarkdown>
                ) : (
                  m.content
                )}
              </div>
            </div>
          ))}
          {loading && (
            <div className="flex justify-start">
              <div className="bg-slate-800 rounded-2xl px-4 py-3 text-sm text-slate-400">
                Thinking…
              </div>
            </div>
          )}
          <div ref={bottomRef} />
        </div>

        {/* Input */}
        <div className="border-t border-slate-800 p-4">
          <div className="flex gap-3 max-w-3xl mx-auto">
            <input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && send()}
              placeholder="Message your Personal AI OS…"
              className="flex-1 rounded-xl border border-slate-700 bg-slate-900 px-4 py-3 text-sm focus:border-cyan-500 focus:outline-none focus:ring-1 focus:ring-cyan-500"
              disabled={loading}
            />
            <button
              onClick={send}
              disabled={loading || !input.trim()}
              className="rounded-xl bg-cyan-600 px-4 py-3 text-white hover:bg-cyan-500 disabled:opacity-50 transition"
            >
              <Send className="h-4 w-4" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
