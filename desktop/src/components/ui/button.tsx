import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

const buttonVariants = cva(
  "inline-flex items-center justify-center gap-2 rounded-btn text-[13px] font-semibold transition-colors disabled:opacity-50",
  {
    variants: {
      variant: {
        primary:
          "bg-gradient-to-l from-accent to-accent2 text-level0 hover:opacity-90",
        ghost:
          "border border-border text-fdim hover:text-ftext hover:border-accent",
        danger:
          "border border-danger text-danger hover:bg-danger hover:text-ftext",
      },
      size: { md: "h-10 px-4", sm: "h-8 px-3" },
    },
    defaultVariants: { variant: "ghost", size: "md" },
  }
);

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {}

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, ...props }, ref) => (
    <button ref={ref} className={cn(buttonVariants({ variant, size }), className)} {...props} />
  )
);
Button.displayName = "Button";
