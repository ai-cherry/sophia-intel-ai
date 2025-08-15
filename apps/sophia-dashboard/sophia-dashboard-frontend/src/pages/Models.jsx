import { useEffect, useState } from "react";

export default function Models() {
  const [models, setModels] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [filter, setFilter] = useState("all");
  const [search, setSearch] = useState("");

  const loadModels = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch("/api/models/allowlist");
      const data = await res.json();
      
      if (data.status === "error") {
        setError(data.reason || "Failed to load models");
        setModels([]);
      } else {
        setModels(data.models || []);
      }
    } catch (err) {
      setError(err.message);
      setModels([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadModels();
  }, []);

  const filteredModels = models.filter(model => {
    const matchesSearch = model.name.toLowerCase().includes(search.toLowerCase()) ||
                         model.id.toLowerCase().includes(search.toLowerCase());
    
    if (filter === "all") return matchesSearch;
    if (filter === "available") return matchesSearch && model.status === "available";
    if (filter === "missing") return matchesSearch && model.status === "missing";
    
    return matchesSearch;
  });

  const getProviderIcon = (modelId) => {
    if (modelId.includes("anthropic") || modelId.includes("claude")) return "🤖";
    if (modelId.includes("google") || modelId.includes("gemini")) return "🔍";
    if (modelId.includes("openai") || modelId.includes("gpt")) return "⚡";
    if (modelId.includes("deepseek")) return "🧠";
    if (modelId.includes("qwen")) return "🌟";
    if (modelId.includes("mistral")) return "🌪️";
    return "🤖";
  };

  const getStatusBadge = (status) => {
    switch (status) {
      case "available":
        return "bg-emerald-500/20 text-emerald-400 border-emerald-500/30";
      case "missing":
        return "bg-red-500/20 text-red-400 border-red-500/30";
      default:
        return "bg-gray-500/20 text-gray-400 border-gray-500/30";
    }
  };

  const formatContextLength = (length) => {
    if (!length) return "N/A";
    if (length >= 1000000) return `${(length / 1000000).toFixed(1)}M`;
    if (length >= 1000) return `${(length / 1000).toFixed(0)}K`;
    return length.toString();
  };

  const formatPricing = (pricing) => {
    if (!pricing || !pricing.prompt) return "N/A";
    const prompt = parseFloat(pricing.prompt);
    const completion = parseFloat(pricing.completion || pricing.prompt);
    
    return `$${prompt.toFixed(4)}/$${completion.toFixed(4)}`;
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="flex items-center gap-3 text-white/60">
          <div className="w-6 h-6 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
          Loading approved models...
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white mb-1">Model Allowlist</h1>
          <p className="text-white/60">OpenRouter approved models for coding swarms</p>
        </div>
        <button
          onClick={loadModels}
          className="px-4 py-2 rounded-lg bg-white/10 hover:bg-white/20 text-white/70 text-sm transition-colors"
        >
          🔄 Refresh
        </button>
      </div>

      {/* Error State */}
      {error && (
        <div className="rounded-2xl border border-red-500/30 bg-red-500/10 p-6">
          <div className="flex items-center gap-3 mb-2">
            <span className="text-red-400 text-xl">⚠️</span>
            <h3 className="text-red-400 font-semibold">Failed to Load Models</h3>
          </div>
          <p className="text-red-300 text-sm">{error}</p>
          <button
            onClick={loadModels}
            className="mt-3 px-4 py-2 rounded-lg bg-red-500/20 hover:bg-red-500/30 text-red-300 text-sm transition-colors"
          >
            Try Again
          </button>
        </div>
      )}

      {/* Stats & Filters */}
      {!error && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
            <div className="text-2xl font-bold text-white">{models.length}</div>
            <div className="text-white/60 text-sm">Total Approved</div>
          </div>
          <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
            <div className="text-2xl font-bold text-emerald-400">
              {models.filter(m => m.status === "available").length}
            </div>
            <div className="text-white/60 text-sm">Available</div>
          </div>
          <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
            <div className="text-2xl font-bold text-red-400">
              {models.filter(m => m.status === "missing").length}
            </div>
            <div className="text-white/60 text-sm">Missing</div>
          </div>
          <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
            <div className="text-2xl font-bold text-blue-400">
              {Math.round((models.filter(m => m.status === "available").length / models.length) * 100) || 0}%
            </div>
            <div className="text-white/60 text-sm">Availability</div>
          </div>
        </div>
      )}

      {/* Search & Filter */}
      {!error && (
        <div className="flex flex-col md:flex-row gap-4">
          <div className="flex-1">
            <input
              type="text"
              placeholder="Search models..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full px-4 py-3 rounded-xl bg-white/5 border border-white/10 text-white placeholder:text-white/40 focus:outline-none focus:ring-2 focus:ring-indigo-500/50"
            />
          </div>
          <div className="flex gap-2">
            {["all", "available", "missing"].map((f) => (
              <button
                key={f}
                onClick={() => setFilter(f)}
                className={`px-4 py-3 rounded-xl text-sm font-medium transition-colors ${
                  filter === f
                    ? "bg-indigo-500 text-white"
                    : "bg-white/5 text-white/70 hover:bg-white/10"
                }`}
              >
                {f.charAt(0).toUpperCase() + f.slice(1)}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Models Grid */}
      {!error && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filteredModels.map((model, index) => (
            <div
              key={model.id || index}
              className="rounded-2xl border border-white/10 bg-white/5 p-6 hover:bg-white/10 transition-colors"
            >
              <div className="flex items-start justify-between mb-3">
                <div className="flex items-center gap-2">
                  <span className="text-xl">{getProviderIcon(model.id || model.name)}</span>
                  <div>
                    <h3 className="text-white/90 font-medium text-sm leading-tight">
                      {model.name}
                    </h3>
                    {model.id && model.id !== model.name && (
                      <p className="text-white/50 text-xs mt-1">{model.id}</p>
                    )}
                  </div>
                </div>
                <span className={`px-2 py-1 rounded-full text-xs font-medium border ${getStatusBadge(model.status)}`}>
                  {model.status || "unknown"}
                </span>
              </div>

              <div className="space-y-2 text-sm">
                {model.context_length && (
                  <div className="flex justify-between">
                    <span className="text-white/60">Context:</span>
                    <span className="text-white/90">{formatContextLength(model.context_length)}</span>
                  </div>
                )}
                {model.pricing && (
                  <div className="flex justify-between">
                    <span className="text-white/60">Pricing:</span>
                    <span className="text-white/90 text-xs">{formatPricing(model.pricing)}</span>
                  </div>
                )}
                <div className="flex justify-between">
                  <span className="text-white/60">Allowed:</span>
                  <span className="text-emerald-400">✅ Yes</span>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Empty State */}
      {!error && filteredModels.length === 0 && (
        <div className="rounded-2xl border border-white/10 bg-white/5 p-12 text-center">
          <div className="text-white/40 text-4xl mb-4">🔍</div>
          <h3 className="text-white/70 font-medium mb-2">No models found</h3>
          <p className="text-white/50 text-sm">
            {search ? "Try adjusting your search terms" : "No models match the current filter"}
          </p>
        </div>
      )}
    </div>
  );
}

