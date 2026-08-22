"use client";

import { useEffect, useState } from "react";
import { memoryApi } from "@/lib/api";
import { Plus, Trash2, Search } from "lucide-react";

const CATEGORIES = ["preferences", "projects", "goals", "people", "facts", "decisions", "habits", "other"];

export default function MemoryPage() {
  const [memories, setMemories] = useState<any[]>([]);
  const [q, setQ] = useState("");
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({ category: "facts", content: "", importance: 0.5 });

  const load = () => memoryApi.list(q ? { q } : undefined).then(setMemories).catch(() => {});

  useEffect(() => { load(); }, []);

  async function create() {
    if (!form.content.trim()) return;
    await memoryApi.create(form);
    setForm({ category: "facts", content: "", importance: 0.5 });
    setShowForm(false);
    load();
  }

  async function remove(id: string) {
    await memoryApi.delete(id);
    load();
  }

  return (
    <div className="p-8 max-w-4xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Long-term Memory</h1>
          <p className="text-slate-400 text-sm mt-1">Your AI remembers what matters. You control everything.</p>
        </div>
        <button
          onClick={() => setShowForm(!showForm)}
          className="flex items-center gap-2 rounded-lg bg-cyan-600 px-4 py-2 text-sm font-medium hover:bg-cyan-500 transition"
        >
          <Plus className="h-4 w-4" /> Add memory
        </button>
      </div>

      <div className="relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-500" />
        <input
          value={q}
          onChange={(e) => setQ(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && load()}
          placeholder="Search memories…"
          className="w-full rounded-lg border border-slate-700 bg-slate-900 pl-10 pr-4 py-2.5 text-sm focus:border-cyan-500 focus:outline-none"
        />
      </div>

      {showForm && (
        <div className="rounded-xl border border-slate-800 bg-slate-900/50 p-5 space-y-4">
          <select
            value={form.category}
            onChange={(e) => setForm({ ...form, category: e.target.value })}
            className="w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-sm"
          >
            {CATEGORIES.map((c) => (
              <option key={c} value={c}>{c}</option>
            ))}
          </select>
          <textarea
            value={form.content}
            onChange={(e) => setForm({ ...form, content: e.target.value })}
            placeholder="What should your AI remember?"
            rows={3}
            className="w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-sm focus:border-cyan-500 focus:outline-none"
          />
          <div className="flex items-center gap-4">
            <label className="text-sm text-slate-400">Importance: {form.importance.toFixed(1)}</label>
            <input
              type="range"
              min={0}
              max={1}
              step={0.1}
              value={form.importance}
              onChange={(e) => setForm({ ...form, importance: parseFloat(e.target.value) })}
              className="flex-1"
            />
            <button onClick={create} className="rounded-lg bg-cyan-600 px-4 py-2 text-sm hover:bg-cyan-500">
              Save
            </button>
          </div>
        </div>
      )}

      <div className="space-y-3">
        {memories.length === 0 && (
          <p className="text-slate-500 text-sm text-center py-12">No memories yet. Add one or let the AI extract them from conversations.</p>
        )}
        {memories.map((m) => (
          <div key={m.id} className="group rounded-xl border border-slate-800 bg-slate-900/50 p-4 flex gap-4">
            <div className="flex-1">
              <div className="flex items-center gap-2 mb-1">
                <span className="text-xs font-medium uppercase tracking-wider text-cyan-400">{m.category}</span>
                <span className="text-xs text-slate-500">importance {m.importance?.toFixed(1)}</span>
              </div>
              <p className="text-sm text-slate-200">{m.content}</p>
              <p className="text-xs text-slate-500 mt-2">{new Date(m.created_at).toLocaleString()}</p>
            </div>
            <button
              onClick={() => remove(m.id)}
              className="opacity-0 group-hover:opacity-100 text-slate-500 hover:text-red-400 transition"
              title="Forget this memory"
            >
              <Trash2 className="h-4 w-4" />
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}
