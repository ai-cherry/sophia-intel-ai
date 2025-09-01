import { useState } from 'react';
import Link from 'next/link';

interface FormState {
  poolType: string;
  maxGenerators: number;
  maxCritics: number;
  useMemory: boolean;
  accuracyThreshold: number;
  consensusThreshold: number;
}

export default function SwarmConfigurator() {
  const [form, setForm] = useState<FormState>({
    poolType: 'balanced',
    maxGenerators: 3,
    maxCritics: 2,
    useMemory: true,
    accuracyThreshold: 0.8,
    consensusThreshold: 2,
  });

  const handleChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>
  ) => {
    const { name, value, type, checked } = e.target;
    setForm((prev) => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value,
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    await fetch('/api/swarms/configure', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        poolType: form.poolType,
        maxGenerators: Number(form.maxGenerators),
        maxCritics: Number(form.maxCritics),
        useMemory: form.useMemory,
        accuracyThreshold: Number(form.accuracyThreshold),
        consensusThreshold: Number(form.consensusThreshold),
      }),
    });
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex items-center gap-4">
          <Link href="/" className="text-blue-600 hover:text-blue-700">
            ← Back
          </Link>
          <h1 className="text-2xl font-bold text-gray-900">
            Swarm Configurator
          </h1>
        </div>
      </header>
      <main className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <form onSubmit={handleSubmit} className="space-y-6">
          <div>
            <label className="block text-sm font-medium text-gray-700">
              Pool Type
            </label>
            <select
              name="poolType"
              value={form.poolType}
              onChange={handleChange}
              className="mt-1 block w-full border-gray-300 rounded-md shadow-sm"
            >
              <option value="balanced">Balanced</option>
              <option value="cheap">Cheap</option>
              <option value="premium">Premium</option>
            </select>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700">
                Max Generators
              </label>
              <input
                type="number"
                name="maxGenerators"
                value={form.maxGenerators}
                onChange={handleChange}
                className="mt-1 block w-full border-gray-300 rounded-md shadow-sm"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">
                Max Critics
              </label>
              <input
                type="number"
                name="maxCritics"
                value={form.maxCritics}
                onChange={handleChange}
                className="mt-1 block w-full border-gray-300 rounded-md shadow-sm"
              />
            </div>
          </div>
          <div className="flex items-center gap-2">
            <input
              type="checkbox"
              name="useMemory"
              checked={form.useMemory}
              onChange={handleChange}
            />
            <span className="text-sm text-gray-700">Use Memory</span>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700">
                Accuracy Threshold
              </label>
              <input
                type="number"
                step="0.01"
                name="accuracyThreshold"
                value={form.accuracyThreshold}
                onChange={handleChange}
                className="mt-1 block w-full border-gray-300 rounded-md shadow-sm"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">
                Consensus Threshold
              </label>
              <input
                type="number"
                name="consensusThreshold"
                value={form.consensusThreshold}
                onChange={handleChange}
                className="mt-1 block w-full border-gray-300 rounded-md shadow-sm"
              />
            </div>
          </div>
          <button
            type="submit"
            className="px-4 py-2 bg-blue-600 text-white rounded-md"
          >
            Save Configuration
          </button>
        </form>
      </main>
    </div>
  );
}
