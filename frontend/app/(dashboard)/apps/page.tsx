"use client";

import { useEffect, useState } from "react";
import { integrationsApi } from "@/lib/api";
import { Mail, Calendar, HardDrive, MessageSquare, FileText, Smartphone } from "lucide-react";

const ICONS: Record<string, any> = {
  gmail: Mail,
  google_calendar: Calendar,
  google_drive: HardDrive,
  slack: MessageSquare,
  notion: FileText,
  whatsapp: Smartphone,
};

const LABELS: Record<string, string> = {
  gmail: "Gmail",
  google_calendar: "Google Calendar",
  google_drive: "Google Drive",
  slack: "Slack",
  notion: "Notion",
  whatsapp: "WhatsApp",
};

export default function AppsPage() {
  const [apps, setApps] = useState<any[]>([]);
  const [message, setMessage] = useState("");

  const load = () => integrationsApi.list().then(setApps).catch(() => {});
  useEffect(() => { load(); }, []);

  async function connect(provider: string) {
    setMessage("");
    try {
      const res = await integrationsApi.connect(provider);
      if (res.authorization_url) {
        window.open(res.authorization_url, "_blank");
      }
      setMessage(res.message);
    } catch (err: any) {
      setMessage(err.message);
    }
  }

  async function disconnect(provider: string) {
    await integrationsApi.disconnect(provider);
    load();
  }

  return (
    <div className="p-8 max-w-4xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Connected Apps</h1>
        <p className="text-slate-400 text-sm mt-1">
          Connect your accounts so the AI can help with email, calendar, files, and more.
          Tokens are stored securely on the server and never sent to the browser.
        </p>
      </div>

      {message && (
        <div className="rounded-lg border border-cyan-500/30 bg-cyan-500/10 px-4 py-3 text-sm text-cyan-300">
          {message}
        </div>
      )}

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        {apps.map((app) => {
          const Icon = ICONS[app.provider] || FileText;
          return (
            <div key={app.provider} className="rounded-xl border border-slate-800 bg-slate-900/50 p-5">
              <div className="flex items-start gap-4">
                <div className="rounded-lg bg-slate-800 p-2.5">
                  <Icon className="h-5 w-5 text-cyan-400" />
                </div>
                <div className="flex-1">
                  <h3 className="font-medium">{LABELS[app.provider] || app.provider}</h3>
                  {app.connected ? (
                    <>
                      <p className="text-xs text-green-400 mt-0.5">Connected</p>
                      {app.account_email && (
                        <p className="text-xs text-slate-500 mt-0.5">{app.account_email}</p>
                      )}
                    </>
                  ) : (
                    <p className="text-xs text-slate-500 mt-0.5">Not connected</p>
                  )}
                </div>
              </div>
              <div className="mt-4 flex gap-2">
                {app.connected ? (
                  <button
                    onClick={() => disconnect(app.provider)}
                    className="rounded-lg border border-slate-700 px-3 py-1.5 text-xs text-slate-300 hover:bg-slate-800 transition"
                  >
                    Disconnect
                  </button>
                ) : (
                  <button
                    onClick={() => connect(app.provider)}
                    className="rounded-lg bg-cyan-600 px-3 py-1.5 text-xs font-medium hover:bg-cyan-500 transition"
                  >
                    Connect
                  </button>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
