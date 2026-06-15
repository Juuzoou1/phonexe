import * as React from "react";
import { cn } from "@/lib/utils";

/** shadcn-style Card on the level-1 surface with a subtle cyan glow. */
export const Card = React.forwardRef<HTMLDivElement, React.HTMLAttributes<HTMLDivElement>>(
  ({ className, ...props }, ref) => (
    <div
      ref={ref}
      className={cn(
        // translucent FUI panel: the hero cluster glows through; HUD corner
        // brackets via .hud (violet --hud-accent from :root).
        "hud rounded-card border border-border bg-level1/70 shadow-glow backdrop-blur-md",
        className
      )}
      {...props}
    />
  )
);
Card.displayName = "Card";

export function CardHeader({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return <div className={cn("flex items-center gap-2 px-4 pt-3 pb-2", className)} {...props} />;
}

export function CardTitle({ className, ...props }: React.HTMLAttributes<HTMLHeadingElement>) {
  return (
    <h3
      className={cn(
        "border-r-2 border-accent pr-2.5 text-[15px] font-bold text-ftext",
        className
      )}
      {...props}
    />
  );
}

export function CardContent({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return <div className={cn("px-4 pb-4", className)} {...props} />;
}
