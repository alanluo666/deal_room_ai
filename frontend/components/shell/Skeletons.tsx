import { Card } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";

export function DealRoomGridSkeleton({ count = 4 }: { count?: number }) {
  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-3">
      {Array.from({ length: count }).map((_, idx) => (
        <Card key={idx} className="flex flex-col gap-4">
          <div className="flex items-start gap-3">
            <Skeleton className="h-9 w-9 rounded-md" />
            <div className="flex-1 space-y-2">
              <Skeleton className="h-4 w-2/3" />
              <Skeleton className="h-3 w-1/2" />
            </div>
          </div>
          <div className="flex items-center justify-between">
            <Skeleton className="h-3 w-24" />
            <Skeleton className="h-8 w-20 rounded-md" />
          </div>
        </Card>
      ))}
    </div>
  );
}

export function DealRoomHeaderSkeleton() {
  return (
    <Card className="flex flex-col gap-3">
      <Skeleton className="h-6 w-1/2" />
      <Skeleton className="h-4 w-1/3" />
      <div className="flex gap-2 pt-1">
        <Skeleton className="h-5 w-20 rounded-full" />
        <Skeleton className="h-5 w-28 rounded-full" />
      </div>
    </Card>
  );
}

export function DocumentListSkeleton({ rows = 3 }: { rows?: number }) {
  return (
    <Card className="p-0">
      <ul className="divide-y divide-border">
        {Array.from({ length: rows }).map((_, idx) => (
          <li
            key={idx}
            className="flex items-center justify-between gap-4 p-4"
          >
            <div className="flex min-w-0 flex-1 items-center gap-3">
              <Skeleton className="h-8 w-8 rounded-md" />
              <div className="flex-1 space-y-2">
                <Skeleton className="h-4 w-2/3" />
                <Skeleton className="h-3 w-1/3" />
              </div>
            </div>
            <Skeleton className="h-5 w-16 rounded-full" />
          </li>
        ))}
      </ul>
    </Card>
  );
}

export function AnswerCardSkeleton() {
  return (
    <Card className="flex flex-col gap-3">
      <Skeleton className="h-4 w-24" />
      <Skeleton className="h-3 w-full" />
      <Skeleton className="h-3 w-11/12" />
      <Skeleton className="h-3 w-8/12" />
    </Card>
  );
}
