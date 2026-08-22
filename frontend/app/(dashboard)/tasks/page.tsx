"use client";

import { useEffect, useState } from "react";
import { tasksApi } from "@/lib/api";
import { Plus, Trash2 } from "lucide-react";

export default function TasksPage() {
  const [tasks, setTasks] = useState<any[]>([]);
  const [title, setTitle] = useState("");
  const [priority, setPriority] = useState("medium");

  const load = () => tasksApi.list().then(setTasks).catch(() => {});
  useEffect(() => { load(); }, []);

  async function add() {
    if (!title.trim()) return;
    await tasksApi.create({ title: title.trim(), priority });
    setTitle("");
    load();
  }

  async function toggle(task: any) {
    const next = task.status === "completed" ? "pending" : "completed";
    await tasksApi.update(task.id, { status: next });
    load();
  }

  async function remove(id: string) {
    await tasksApi.delete(id);
    load();
  }

  return (
    <div className="p-8 max-w-3xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Tasks</h1>
        <p className="text-slate-400 text-sm mt-1">Manage your tasks or let the AI create them for you.</p>
      </div>

      <div className="flex gap-3">
        <input
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && add()}
          placeholder="Add a task…"
          className="flex-1 rounded-lg border border-slate-700 bg-slate-900 px-4 py-2.5 text-sm focus:border-cyan-500 focus:outline-none"
        />
        <select
          value={priority}
          onChange={(e) => setPriority(e.target.value)}
          className="rounded-lg border border-slate-700 bg-slate-900 px-3 py-2.5 text-sm"
        >
          <option value="low">Low</option>
          <option value="medium">Medium</option>
          <option value="high">High</option>
        </select>
        <button onClick={add} className="rounded-lg bg-cyan-600 px-4 py-2.5 text-sm font-medium hover:bg-cyan-500">
          <Plus className="h-4 w-4" />
        </button>
      </div>

      <ul className="space-y-2">
        {tasks.map((t) => (
          <li
            key={t.id}
            className="group flex items-center gap-3 rounded-xl border border-slate-800 bg-slate-900/50 px-4 py-3"
          >
            <input
              type="checkbox"
              checked={t.status === "completed"}
              onChange={() => toggle(t)}
              className="h-4 w-4 rounded border-slate-600"
            />
            <span className={`flex-1 text-sm ${t.status === "completed" ? "line-through text-slate-500" : ""}`}>
              {t.title}
            </span>
            <span className={`text-xs px-2 py-0.5 rounded ${
              t.priority === "high" ? "bg-red-500/20 text-red-400" :
              t.priority === "low" ? "bg-slate-700 text-slate-400" :
              "bg-amber-500/20 text-amber-400"
            }`}>{t.priority}</span>
            <button onClick={() => remove(t.id)} className="opacity-0 group-hover:opacity-100 text-slate-500 hover:text-red-400">
              <Trash2 className="h-4 w-4" />
            </button>
          </li>
        ))}
        {tasks.length === 0 && (
          <p className="text-center text-slate-500 text-sm py-12">No tasks yet.</p>
        )}
      </ul>
    </div>
  );
}
