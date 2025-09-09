'use client';
import { useEffect } from 'react';
import { useRouter } from 'next/navigation';

export default function Home() {
  const router = useRouter();
  
  useEffect(() => {
    router.push('/sophia');
  }, [router]);
  
  return (
    <div className="flex items-center justify-center h-screen bg-gray-900 text-white">
      <div className="text-center">
        <h1 className="text-3xl font-bold mb-4">Welcome to Sophia AI</h1>
        <p className="text-gray-400">Redirecting...</p>
      </div>
    </div>
  );
}
