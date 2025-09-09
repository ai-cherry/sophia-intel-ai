"use client";
import React from 'react';

type Props = {
  title?: string;
  subtitle?: string;
  children: React.ReactNode;
  className?: string;
};

export default function Section({ title, subtitle, children, className }: Props) {
  return (
    <section className={`rounded-lg border border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900 ${className || ''}`}>
      {(title || subtitle) && (
        <header className="px-3 md:px-4 py-2 md:py-3 border-b border-gray-200 dark:border-gray-800">
          {title && <h2 className="text-sm md:text-base font-semibold">{title}</h2>}
          {subtitle && <p className="text-xs text-gray-500 dark:text-gray-400">{subtitle}</p>}
        </header>
      )}
      <div className="p-2 md:p-3">
        {children}
      </div>
    </section>
  );
}

