import React from 'react';
import { Skeleton } from '../ui/skeleton';

export default function PostSkeleton({ count = 3 }) {
  return (
    <div className="space-y-4" data-testid="feed-skeleton">
      {Array.from({ length: count }).map((_, i) => (
        <div key={i} className="feed-card p-5">
          <div className="flex items-center gap-3">
            <Skeleton className="h-10 w-10 rounded-full bg-[#F1EBE1]" />
            <div className="flex-1 space-y-2">
              <Skeleton className="h-3.5 w-1/3 bg-[#F1EBE1]" />
              <Skeleton className="h-3 w-1/5 bg-[#F1EBE1]" />
            </div>
          </div>
          <Skeleton className="mt-4 h-4 w-2/3 bg-[#F1EBE1]" />
          <Skeleton className="mt-2 h-3 w-full bg-[#F1EBE1]" />
          <Skeleton className="mt-2 h-3 w-5/6 bg-[#F1EBE1]" />
        </div>
      ))}
    </div>
  );
}
