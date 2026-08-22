"use client";

import { useEffect, useState } from "react";
import { authApi } from "@/lib/api";

export default function SettingsPage() {
  const [user, setUser] = useState<any>(null);

  useEffect(() => {
    authApi.me().then(setUser).catch(() => {});
  }, []);

  return (
    <div className="p-8 max-w-2xl mx-auto space-y-8">
      <div>
        <h1 className="text-2xl font-bold">Settings</h1>
        <p className="text-slate-400 text-sm mt-1">Profile and security preferences.</p>
      </div>

      <section className="rounded-xl border border-slate-800 bg-slate-900/50 p-6 space-y-4">
        <h2 className="font-semibold">Profile</h2>
        {user && (
          <div className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-slate-400">Email</span>
              <span>{user.email}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-400">Name</span>
              <span>{user.full_name || "—"}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-400">User ID</span>
              <span className="font-mono text-xs text-slate-500">{user.id}</span>
            </div>
          </div>
        )}
      </section>

      <section className="rounded-xl border border-slate-800 bg-slate-900/50 p-6 space-y-3">
        <h2 className="font-semibold">AI Permissions</h2>
        <p className="text-sm text-slate-400">
          Fine-grained permission controls for Gmail, Calendar, Drive, Slack, and Notion will appear here once those integrations are connected.
          By default, high-risk actions (send email, delete files) always require confirmation.
        </p>
      </section>

      <section className="rounded-xl border border-slate-800 bg-slate-900/50 p-6 space-y-3">
        <h2 className="font-semibold text-red-400">Danger Zone</h2>
        <p className="text-sm text-slate-400">
          Account deletion and full data export endpoints can be added here. All user data is isolated and can be removed on request.
        </p>
      </section>
    </div>
  );
}
