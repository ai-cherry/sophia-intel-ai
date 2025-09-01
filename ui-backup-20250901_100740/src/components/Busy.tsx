'use client';

interface BusyProps {
  message?: string;
}

export function Busy({ message = 'Loading...' }: BusyProps) {
  return (
    <div className="flex items-center justify-center p-8">
      <div className="flex items-center gap-3">
        <div className="relative w-8 h-8">
          <div className="absolute inset-0 border-4 border-gray-200 rounded-full" />
          <div className="absolute inset-0 border-4 border-blue-600 rounded-full border-t-transparent animate-spin" />
        </div>
        <span className="text-gray-600">{message}</span>
      </div>
    </div>
  );
}