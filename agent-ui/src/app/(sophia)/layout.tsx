"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { ReactNode } from "react";

const navItems = [
  { href: "/unified", label: "Unified", icon: "🧭" },
  { href: "/dashboard", label: "Dashboard", icon: "📊" },
  { href: "/chat", label: "Chat", icon: "💬" },
  { href: "/insights", label: "Insights", icon: "💡" },
  { href: "/pipeline", label: "Pipeline", icon: "🔄" },
  { href: "/teams", label: "Teams", icon: "👥" },
  { href: "/integrations", label: "Integrations", icon: "🔌" },
  { href: "/analytics", label: "Analytics", icon: "📈" },
  { href: "/notifications", label: "Alerts", icon: "🔔" },
];

export default function SophiaLayout({ children }: { children: ReactNode }) {
  const pathname = usePathname();

  return (
    <div className="h-screen flex">
      {/* Sidebar */}
      <div className="w-64 bg-gray-900 text-white flex flex-col">
        <div className="p-4 border-b border-gray-800">
          <h1 className="text-xl font-bold flex items-center gap-2">
            <span className="text-2xl">🧠</span>
            Sophia Intel AI
          </h1>
          <p className="text-xs text-gray-400 mt-1">Business Intelligence Suite</p>
        </div>
        
        <nav className="flex-1 p-4">
          <ul className="space-y-1">
            {navItems.map((item) => {
              const isActive = pathname === item.href;
              return (
                <li key={item.href}>
                  <Link
                    href={item.href}
                    className={`flex items-center gap-3 px-3 py-2 rounded-lg transition-colors ${
                      isActive
                        ? "bg-blue-600 text-white"
                        : "hover:bg-gray-800 text-gray-300"
                    }`}
                  >
                    <span className="text-lg">{item.icon}</span>
                    <span className="text-sm font-medium">{item.label}</span>
                  </Link>
                </li>
              );
            })}
          </ul>
        </nav>

        <div className="p-4 border-t border-gray-800">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 bg-blue-500 rounded-full flex items-center justify-center text-sm">
              LM
            </div>
            <div className="flex-1">
              <p className="text-sm font-medium">Lynn Musil</p>
              <p className="text-xs text-gray-400">PayReady</p>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 bg-gray-50 overflow-auto">
        {children}
      </div>
    </div>
  );
}
