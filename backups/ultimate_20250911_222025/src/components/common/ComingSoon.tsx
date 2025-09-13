"use client";
import React from 'react';
import { Card, CardContent } from '@/components/ui/card';
import { AlertCircle } from 'lucide-react';

/**
 * Coming Soon placeholder component
 * Standardized across the repo to avoid inconsistent mocks/simulations.
 *
 * Search token: "Coming Soon" (case-sensitive) for easy discovery.
 */
export default function ComingSoon({ label = 'Coming Soon', children }: { label?: string; children?: React.ReactNode }) {
  return (
    <Card className="border border-dashed border-gray-300 dark:border-gray-700 bg-gray-50 dark:bg-gray-900/40">
      <CardContent className="py-8 text-center text-sm text-gray-600 dark:text-gray-300">
        <div className="flex items-center justify-center gap-2 mb-2">
          <AlertCircle className="h-4 w-4 opacity-70" />
          <span className="font-medium">{label}</span>
        </div>
        {children ? (
          <div className="text-xs opacity-80">{children}</div>
        ) : (
          <div className="text-xs opacity-80">This feature is planned. No mock data — real integration coming soon.</div>
        )}
      </CardContent>
    </Card>
  );
}

