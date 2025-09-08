"use client";
import { useState } from "react";

type Notification = {
  id: string;
  type: "alert" | "success" | "info" | "warning";
  title: string;
  message: string;
  source: string;
  timestamp: string;
  read: boolean;
  actionable?: {
    label: string;
    action: string;
  };
};

const NOTIFICATIONS: Notification[] = [
  {
    id: "1",
    type: "alert",
    title: "Deal at Risk: TechCo",
    message: "No activity for 10 days on $180K opportunity. Immediate action recommended.",
    source: "Pipeline Monitor",
    timestamp: "5 minutes ago",
    read: false,
    actionable: { label: "View Deal", action: "view-deal" }
  },
  {
    id: "2",
    type: "success",
    title: "Deal Closed: Acme Corp",
    message: "Sarah Chen successfully closed the Acme Corp deal for $250K!",
    source: "Salesforce",
    timestamp: "2 hours ago",
    read: false,
    actionable: { label: "Celebrate", action: "celebrate" }
  },
  {
    id: "3",
    type: "info",
    title: "New Gong Recording Available",
    message: "Call with FinanceApp CFO has been processed. Key insights available.",
    source: "Gong",
    timestamp: "3 hours ago",
    read: true,
    actionable: { label: "View Insights", action: "view-call" }
  },
  {
    id: "4",
    type: "warning",
    title: "Integration Warning: HubSpot",
    message: "API rate limit approaching. 85% of daily quota used.",
    source: "System",
    timestamp: "5 hours ago",
    read: true
  },
  {
    id: "5",
    type: "info",
    title: "Weekly Report Ready",
    message: "Your sales performance report for week 45 is ready to view.",
    source: "Analytics",
    timestamp: "1 day ago",
    read: true,
    actionable: { label: "View Report", action: "view-report" }
  },
  {
    id: "6",
    type: "success",
    title: "Task Completed",
    message: "Contract review for DataSoft completed by Legal team.",
    source: "Asana",
    timestamp: "1 day ago",
    read: true
  }
];

export default function NotificationsPage() {
  const [notifications, setNotifications] = useState(NOTIFICATIONS);
  const [filter, setFilter] = useState<"all" | "unread">("all");

  const filteredNotifications = filter === "unread" 
    ? notifications.filter(n => !n.read)
    : notifications;

  const getTypeIcon = (type: string) => {
    switch (type) {
      case "alert": return "🚨";
      case "success": return "✅";
      case "warning": return "⚠️";
      case "info": return "ℹ️";
      default: return "📢";
    }
  };

  const getTypeColor = (type: string) => {
    switch (type) {
      case "alert": return "border-red-200 bg-red-50";
      case "success": return "border-green-200 bg-green-50";
      case "warning": return "border-amber-200 bg-amber-50";
      case "info": return "border-blue-200 bg-blue-50";
      default: return "border-gray-200 bg-gray-50";
    }
  };

  const markAsRead = (id: string) => {
    setNotifications(prev => 
      prev.map(n => n.id === id ? { ...n, read: true } : n)
    );
  };

  const markAllAsRead = () => {
    setNotifications(prev => prev.map(n => ({ ...n, read: true })));
  };

  const clearAll = () => {
    setNotifications([]);
  };

  const unreadCount = notifications.filter(n => !n.read).length;

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold flex items-center gap-2">
            Notifications
            {unreadCount > 0 && (
              <span className="text-sm px-2 py-1 bg-red-500 text-white rounded-full">
                {unreadCount}
              </span>
            )}
          </h1>
          <p className="text-gray-500 mt-1">Stay updated with important alerts and updates</p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={markAllAsRead}
            className="px-4 py-2 bg-white border rounded-lg hover:bg-gray-50"
          >
            Mark All Read
          </button>
          <button
            onClick={clearAll}
            className="px-4 py-2 bg-white border rounded-lg hover:bg-gray-50 text-red-600"
          >
            Clear All
          </button>
        </div>
      </div>

      {/* Filter Tabs */}
      <div className="flex gap-4 border-b">
        <button
          onClick={() => setFilter("all")}
          className={`pb-2 px-1 font-medium transition-colors ${
            filter === "all"
              ? "border-b-2 border-blue-600 text-blue-600"
              : "text-gray-600 hover:text-gray-900"
          }`}
        >
          All Notifications ({notifications.length})
        </button>
        <button
          onClick={() => setFilter("unread")}
          className={`pb-2 px-1 font-medium transition-colors ${
            filter === "unread"
              ? "border-b-2 border-blue-600 text-blue-600"
              : "text-gray-600 hover:text-gray-900"
          }`}
        >
          Unread ({unreadCount})
        </button>
      </div>

      {/* Notifications List */}
      <div className="space-y-3">
        {filteredNotifications.length === 0 ? (
          <div className="text-center py-12 text-gray-500">
            <p className="text-lg mb-2">No notifications</p>
            <p className="text-sm">You're all caught up!</p>
          </div>
        ) : (
          filteredNotifications.map((notification) => (
            <div
              key={notification.id}
              className={`border rounded-lg p-4 transition-all ${
                notification.read ? "opacity-75" : ""
              } ${getTypeColor(notification.type)}`}
            >
              <div className="flex items-start gap-3">
                <span className="text-2xl mt-0.5">{getTypeIcon(notification.type)}</span>
                <div className="flex-1">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <h3 className="font-semibold flex items-center gap-2">
                        {notification.title}
                        {!notification.read && (
                          <span className="w-2 h-2 bg-blue-500 rounded-full"></span>
                        )}
                      </h3>
                      <p className="text-sm text-gray-700 mt-1">{notification.message}</p>
                      <div className="flex items-center gap-3 mt-2 text-xs text-gray-500">
                        <span>{notification.source}</span>
                        <span>•</span>
                        <span>{notification.timestamp}</span>
                      </div>
                    </div>
                    {!notification.read && (
                      <button
                        onClick={() => markAsRead(notification.id)}
                        className="text-sm text-blue-600 hover:text-blue-700"
                      >
                        Mark as read
                      </button>
                    )}
                  </div>
                  {notification.actionable && (
                    <button className="mt-3 px-3 py-1.5 bg-white border rounded text-sm hover:bg-gray-50">
                      {notification.actionable.label} →
                    </button>
                  )}
                </div>
              </div>
            </div>
          ))
        )}
      </div>

      {/* Notification Settings */}
      <div className="bg-gray-50 rounded-lg p-6">
        <h2 className="font-semibold mb-4">Notification Preferences</h2>
        <div className="space-y-3">
          <label className="flex items-center gap-3">
            <input type="checkbox" defaultChecked className="w-4 h-4" />
            <div>
              <p className="font-medium">Deal Alerts</p>
              <p className="text-sm text-gray-600">Get notified about at-risk deals and opportunities</p>
            </div>
          </label>
          <label className="flex items-center gap-3">
            <input type="checkbox" defaultChecked className="w-4 h-4" />
            <div>
              <p className="font-medium">Team Updates</p>
              <p className="text-sm text-gray-600">Notifications about team performance and achievements</p>
            </div>
          </label>
          <label className="flex items-center gap-3">
            <input type="checkbox" defaultChecked className="w-4 h-4" />
            <div>
              <p className="font-medium">Integration Status</p>
              <p className="text-sm text-gray-600">Alerts about integration health and sync status</p>
            </div>
          </label>
          <label className="flex items-center gap-3">
            <input type="checkbox" className="w-4 h-4" />
            <div>
              <p className="font-medium">Daily Digest</p>
              <p className="text-sm text-gray-600">Receive a daily summary of all activities</p>
            </div>
          </label>
        </div>
      </div>
    </div>
  );
}