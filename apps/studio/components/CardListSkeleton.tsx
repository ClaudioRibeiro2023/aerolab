"use client";

import React from "react";

interface CardListSkeletonProps {
  count?: number;
}

export function CardListSkeleton({ count = 3 }: CardListSkeletonProps) {
  return (
    <>
      {Array.from({ length: count }).map((_, i) => (
        <div
          key={i}
          className="bg-white dark:bg-slate-800 rounded-2xl p-6 border border-gray-100 dark:border-slate-700 animate-pulse"
        >
          <div className="flex items-start gap-4">
            <div className="h-12 w-12 rounded-xl skeleton dark:bg-slate-700" />
            <div className="flex-1 space-y-2">
              <div className="h-5 w-3/4 skeleton dark:bg-slate-700" />
              <div className="h-4 w-1/2 skeleton dark:bg-slate-700" />
            </div>
          </div>
        </div>
      ))}
    </>
  );
}
