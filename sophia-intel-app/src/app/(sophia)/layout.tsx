"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { ReactNode } from "react";
import ModeSwitcher from "@/components/ModeSwitcher";

const navItems = [
  { href: "/unified", label: "Unified", icon: "🧭" },
  { href: "/chat", label: "Chat", icon: "💬" },
  { href: "/projects", label: "Projects", icon: "🛠️" },
  { href: "/swarms", label: "Swarms", icon: "🤖" },
  { href: "/router", label: "Router", icon: "🔀" },
  { href: "/index", label: "Index", icon: "📚" },
  { href: "/brain", label: "Brain Training", icon: "🧩" },
];

export default function SophiaLayout({ children }: { children: ReactNode }) {
  const pathname = usePathname();

  return (
    <div className="h-screen flex">
      {/* Skip to content for accessibility */}
      <a
        href="#main-content"
        className="sr-only focus:not-sr-only focus:absolute focus:top-2 focus:left-2 focus:z-50 rounded bg-blue-600 px-3 py-2 text-white"
      >
        Skip to content
      </a>
      {/* Sidebar */}
      <div className="w-64 bg-gray-900 text-white flex flex-col">
        <div className="p-4 border-b border-gray-800">
          <h1 className="text-xl font-bold flex items-center gap-2">
            <span className="text-2xl">🧠</span>
            Sophia Intel AI
          </h1>
          <p className="text-xs text-gray-400 mt-1">Business Intelligence Suite</p>
        </div>
        <nav className="flex-1 p-4" aria-label="Sophia navigation">
          <ul className="space-y-1">
            {navItems.map((item) => {
              const isActive = pathname === item.href;
              return (
                <li key={item.href}>
                  <Link
                    href={item.href}
                    aria-current={isActive ? 'page' : undefined}
                    className={`flex items-center gap-3 px-3 py-2 rounded-lg transition-colors outline-none focus-visible:ring-2 focus-visible:ring-blue-400 ${
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
      <div id="main-content" role="main" className="flex-1 bg-gray-50 dark:bg-gray-950 overflow-auto">
        {/* Top utility bar (placeholder for search / actions) */}
        <div className="sticky top-0 z-10 border-b bg-white/80 dark:bg-gray-900/80 backdrop-blur px-4 py-2 flex items-center justify-between">
          <div className="text-sm font-medium text-gray-700 dark:text-gray-200">Command Center</div>
          <div className="flex items-center gap-2">
            <ModeSwitcher />
            <input
              type="search"
              placeholder="Quick search…"
              className="hidden md:block text-sm rounded-md border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 px-2 py-1 outline-none focus-visible:ring-2 focus-visible:ring-blue-400"
              aria-label="Quick search"
            />
          </div>
        </div>
        {children}
      </div>
    </div>
  );
}
