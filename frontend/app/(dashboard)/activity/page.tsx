"use client";

import { useEffect, useState } from "react";
import { activityApi } from "@/lib/api";

export default function ActivityPage() {
  const [logs, setLogs] = useState<any[]>([]);

  useEffect(() => {
    activityApi.list().then(setLogs).catch(() => {});
  }, []);

  return (
    <div className="p-8 max-w-3xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Activity Log</h1>
        <p className="text-slate-400 text-sm mt-1">Audit trail of AI and integration actions for your account only.</p>
      </div>

      {logs.length === 0 ? (
        <p className="text-slate-500 text-sm text-center py-12">
          No activity yet. Actions performed by the AI (calendar checks, email searches, etc.) will appear here.
        </p>
      ) : (
        <ul className="space-y-2">
          {logs.map((log) => (
            <li key={log.id} className="rounded-xl border border-slate-800 bg-slate-900/50 px-4 py-3 flex items-start gap-3">
              <span className={`mt-1 h-2 w-2 rounded-full shrink-0 ${
                log.status === "success" ? "bg-green-400" :
                log.status === "warning" ? "bg-amber-400" :
                log.status === "error" ? "bg-red-400" : "bg-slate-500"
              }`} />
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium">{log.action}</p>
                {log.details && <p className="text-xs text-slate-400 mt-0.5">{log.details}</p>}
                <p className="text-xs text-slate-500 mt-1">
                  {log.application && <span className="mr-2">{log.application}</span>}
                  {new Date(log.created_at).toLocaleString()}
                </p>
              </div>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
