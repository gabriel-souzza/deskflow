import * as React from "react";
import { Slot } from "@radix-ui/react-slot";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

const buttonVariants = cva(
  "inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-md text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring disabled:pointer-events-none disabled:opacity-50 [&_svg]:pointer-events-none [&_svg]:size-4 [&_svg]:shrink-0 cursor-pointer",
  {
    variants: {
      variant: {
        default:
          "bg-primary text-primary-foreground shadow hover:bg-primary/90 bg-blue-600 text-white hover:bg-blue-700",
        destructive:
          "bg-destructive text-destructive-foreground shadow-sm hover:bg-destructive/90 bg-red-600 text-white hover:bg-red-700",
        outline:
          "border border-input bg-background shadow-sm hover:bg-accent hover:text-accent-foreground border-slate-300 dark:border-slate-700 hover:bg-slate-100 dark:hover:bg-slate-800",
        secondary:
          "bg-secondary text-secondary-foreground shadow-sm hover:bg-secondary/80 bg-slate-100 text-slate-900 hover:bg-slate-200 dark:bg-slate-800 dark:text-slate-100",
        ghost:
          "hover:bg-accent hover:text-accent-foreground hover:bg-slate-100 dark:hover:bg-slate-800",
        link: "text-primary underline-offset-4 hover:underline text-blue-600 dark:text-blue-400",
      },
      size: {
        default: "h-9 px-4 py-2",
        sm: "h-8 rounded-md px-3 text-xs",
        lg: "h-10 rounded-md px-8 text-base",
        icon: "h-9 w-9",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  }
);

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  asChild?: boolean;
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, asChild = false, ...props }, ref) => {
    const Comp = asChild ? Slot : "button";
    return (
      <Comp
        className={cn(buttonVariants({ variant, size, className }))}
        ref={ref}
        {...props}
      />
    );
  }
);
Button.displayName = "Button";

export { Button, buttonVariants };

