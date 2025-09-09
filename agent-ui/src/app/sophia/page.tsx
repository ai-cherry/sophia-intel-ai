"use client";
import { useEffect } from 'react';
import { useRouter } from 'next/navigation';

export default function SophiaRedirect() {
  const router = useRouter();
  useEffect(() => {
    router.replace('/unified');
  }, [router]);
  return null;
}

