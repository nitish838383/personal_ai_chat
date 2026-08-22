"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { authApi, tasksApi, integrationsApi } from "@/lib/api";
import { MessageSquare, CheckSquare, Puzzle, Brain } from "lucide-react";

export default function DashboardPage() {
  const [user, setUser] = useState<any>(null);
  const [tasks, setTasks] = useState<any[]>([]);
  const [apps, setApps] = useState<any[]>([]);

  useEffect(() => {
    authApi.me().then(setUser).catch(() => {});
    tasksApi.list("pending").then(setTasks).catch(() => {});
    integrationsApi.list().then(setApps).catch(() => {});
  }, []);

  const connectedCount = apps.filter((a) => a.connected).length;

  return (
    <div className="p-8 max-w-6xl mx-auto space-y-8">
      <div>
        <h1 className="text-2xl font-bold">
          Welcome{user?.full_name ? `, ${user.full_name}` : ""}
        </h1>
        <p className="text-slate-400 mt-1">Your Personal AI Operating System</p>
      </div>

      {/* Quick AI input */}
      <Link
        href="/chat"
        className="block rounded-xl border border-slate-800 bg-slate-900/50 p-6 hover:border-cyan-600/50 transition"
      >
        <div className="flex items-center gap-3 text-slate-400">
          <MessageSquare className="h-5 w-5 text-cyan-400" />
          <span>Ask your AI anything…</span>
        </div>
      </Link>

      {/* Stats */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="rounded-xl border border-slate-800 bg-slate-900/50 p-5">
          <div className="flex items-center gap-2 text-slate-400 text-sm">
            <CheckSquare className="h-4 w-4" /> Pending tasks
          </div>
          <p className="text-3xl font-bold mt-2">{tasks.length}</p>
        </div>
        <div className="rounded-xl border border-slate-800 bg-slate-900/50 p-5">
          <div className="flex items-center gap-2 text-slate-400 text-sm">
            <Puzzle className="h-4 w-4" /> Connected apps
          </div>
          <p className="text-3xl font-bold mt-2">{connectedCount}</p>
        </div>
        <div className="rounded-xl border border-slate-800 bg-slate-900/50 p-5">
          <div className="flex items-center gap-2 text-slate-400 text-sm">
            <Brain className="h-4 w-4" /> AI ready
          </div>
          <p className="text-3xl font-bold mt-2 text-cyan-400">Yes</p>
        </div>
      </div>

      {/* Recent tasks */}
      <div className="rounded-xl border border-slate-800 bg-slate-900/50 p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="font-semibold">Pending Tasks</h2>
          <Link href="/tasks" className="text-sm text-cyan-400 hover:underline">
            View all
          </Link>
        </div>
        {tasks.length === 0 ? (
          <p className="text-slate-500 text-sm">No pending tasks. Create one from the Tasks page or ask the AI.</p>
        ) : (
          <ul className="space-y-2">
            {tasks.slice(0, 5).map((t) => (
              <li key={t.id} className="flex items-center gap-3 text-sm">
                <span className={`h-2 w-2 rounded-full ${
                  t.priority === "high" ? "bg-red-400" : t.priority === "low" ? "bg-slate-500" : "bg-amber-400"
                }`} />
                <span>{t.title}</span>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}
