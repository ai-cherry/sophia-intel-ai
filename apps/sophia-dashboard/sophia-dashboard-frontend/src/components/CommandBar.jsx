import { useState } from "react";

export default function CommandBar({ onSubmit }) {
  const [goal, setGoal] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async () => {
    if (!goal.trim() || isLoading) return;
    
    setIsLoading(true);
    try {
      await onSubmit(goal.trim());
      setGoal(""); // Clear after successful submission
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  return (
    <div className="w-full max-w-4xl mx-auto backdrop-blur-sm bg-white/5 border border-white/10 rounded-2xl p-4 shadow-2xl">
      <div className="flex items-center gap-3">
        <div className="flex-1">
          <input
            value={goal}
            onChange={(e) => setGoal(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder='Type a mission… e.g., "Build the Sales Coach MVP" or "Add user authentication"'
            className="w-full bg-transparent outline-none text-base md:text-lg placeholder:text-white/40 px-3 py-3 text-white"
            disabled={isLoading}
          />
        </div>
        <button
          onClick={handleSubmit}
          disabled={!goal.trim() || isLoading}
          className="px-6 py-3 rounded-xl bg-gradient-to-r from-indigo-500 to-purple-600 hover:from-indigo-600 hover:to-purple-700 disabled:from-gray-600 disabled:to-gray-700 disabled:cursor-not-allowed text-white font-medium transition-all duration-200 shadow-lg"
        >
          {isLoading ? (
            <div className="flex items-center gap-2">
              <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
              Planning...
            </div>
          ) : (
            "Plan Mission"
          )}
        </button>
      </div>
      <div className="text-xs text-white/40 px-3 pt-2">
        Press Enter to plan → then run • Powered by MCP Code Server & LangGraph
      </div>
    </div>
  );
}

