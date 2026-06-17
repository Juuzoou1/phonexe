import * as React from "react";
import { cn } from "@/lib/utils";

/** FUI frame panel: hard (non-rounded) translucent surface with bold L-shaped
 *  corner brackets and a top accent tab — the dossier/HUD look, not a soft card. */
export const Card = React.forwardRef<HTMLDivElement, React.HTMLAttributes<HTMLDivElement>>(
  ({ className, children, ...props }, ref) => (
    <div
      ref={ref}
      className={cn(
        "fui-frame relative border border-border/70 bg-level1/60 shadow-glow backdrop-blur-md",
        className,
      )}
      {...props}
    >
      {/* top accent tab */}
      <span className="pointer-events-none absolute right-3 -top-px h-[2px] w-10 bg-accent/70" />
      {/* four L-shaped corner brackets */}
      <span className="pointer-events-none absolute -left-px -top-px h-4 w-4 border-l-2 border-t-2 border-accent/80" />
      <span className="pointer-events-none absolute -right-px -top-px h-4 w-4 border-r-2 border-t-2 border-accent/80" />
      <span className="pointer-events-none absolute -bottom-px -left-px h-4 w-4 border-b-2 border-l-2 border-accent/80" />
      <span className="pointer-events-none absolute -bottom-px -right-px h-4 w-4 border-b-2 border-r-2 border-accent/80" />
      {children}
    </div>
  ),
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
        className,
      )}
      {...props}
    />
  );
}

export function CardContent({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return <div className={cn("px-4 pb-4", className)} {...props} />;
}
