import * as React from "react";
import { Slot } from "@radix-ui/react-slot";
import { cva, type VariantProps } from "class-variance-authority";
import { Loader2 } from "lucide-react";

import { cn } from "@/lib/utils";

const buttonVariants = cva(
  "inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-md text-sm font-medium transition-colors duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[hsl(var(--ring))] focus-visible:ring-offset-2 focus-visible:ring-offset-background disabled:pointer-events-none [&_svg]:pointer-events-none [&_svg]:size-4 [&_svg]:shrink-0",
  {
    variants: {
      variant: {
        // Primary Button - Du Bois primary action
        primary: "bg-[hsl(var(--btn-primary-bg))] text-[hsl(var(--btn-primary-text))] border border-transparent hover:bg-[hsl(var(--btn-primary-bg-hover))] active:bg-[hsl(var(--btn-primary-bg-press))] disabled:bg-[hsl(var(--btn-disabled-bg))] disabled:text-[hsl(var(--btn-disabled-text))] disabled:border-[hsl(var(--btn-disabled-border))] disabled:opacity-100",
        // Default/Secondary Button - Du Bois default action with border
        default: "bg-[hsl(var(--btn-default-bg))] text-[hsl(var(--btn-default-text))] border border-[hsl(var(--btn-default-border))] hover:bg-[hsl(var(--btn-default-bg-hover))] hover:text-[hsl(var(--btn-default-text-hover))] hover:border-[hsl(var(--btn-default-border-hover))] active:bg-[hsl(var(--btn-default-bg-press))] active:text-[hsl(var(--btn-default-text-press))] active:border-[hsl(var(--btn-default-border-press))] disabled:bg-[hsl(var(--btn-disabled-bg))] disabled:text-[hsl(var(--btn-disabled-text))] disabled:border-[hsl(var(--btn-disabled-border))] disabled:opacity-100",
        // Tertiary Button - Du Bois tertiary action (no border)
        tertiary: "bg-[hsl(var(--btn-tertiary-bg))] text-[hsl(var(--btn-tertiary-text))] border border-transparent hover:bg-[hsl(var(--btn-tertiary-bg-hover))] hover:text-[hsl(var(--btn-tertiary-text-hover))] active:bg-[hsl(var(--btn-tertiary-bg-press))] active:text-[hsl(var(--btn-tertiary-text-press))] disabled:bg-[hsl(var(--btn-disabled-bg))] disabled:text-[hsl(var(--btn-disabled-text))] disabled:border-[hsl(var(--btn-disabled-border))] disabled:opacity-100",
        // Danger Button - Du Bois danger action with border
        danger: "bg-[hsl(var(--btn-danger-bg))] text-[hsl(var(--btn-danger-text))] border border-[hsl(var(--btn-danger-border))] hover:bg-[hsl(var(--btn-danger-bg-hover))] hover:text-[hsl(var(--btn-danger-text-hover))] hover:border-[hsl(var(--btn-danger-border-hover))] active:bg-[hsl(var(--btn-danger-bg-press))] active:text-[hsl(var(--btn-danger-text-press))] active:border-[hsl(var(--btn-danger-border-press))] disabled:bg-[hsl(var(--btn-disabled-bg))] disabled:text-[hsl(var(--btn-disabled-text))] disabled:border-[hsl(var(--btn-disabled-border))] disabled:opacity-100",
        // Danger Primary Button - Du Bois filled danger action
        dangerPrimary: "bg-[hsl(var(--btn-danger-primary-bg))] text-[hsl(var(--btn-danger-primary-text))] border border-transparent hover:bg-[hsl(var(--btn-danger-primary-bg-hover))] active:bg-[hsl(var(--btn-danger-primary-bg-press))] disabled:bg-[hsl(var(--btn-disabled-bg))] disabled:text-[hsl(var(--btn-disabled-text))] disabled:border-[hsl(var(--btn-disabled-border))] disabled:opacity-100",
        // Link Button - Du Bois link styling
        link: "bg-transparent text-[hsl(var(--link-default))] border-none underline-offset-4 hover:underline hover:text-[hsl(var(--link-hover))] active:text-[hsl(var(--link-press))] disabled:text-[hsl(var(--btn-disabled-text))] disabled:no-underline disabled:opacity-100 p-0 h-auto",
        // Legacy variants for backward compatibility
        destructive: "bg-[hsl(var(--btn-danger-primary-bg))] text-[hsl(var(--btn-danger-primary-text))] border border-transparent hover:bg-[hsl(var(--btn-danger-primary-bg-hover))] active:bg-[hsl(var(--btn-danger-primary-bg-press))] disabled:bg-[hsl(var(--btn-disabled-bg))] disabled:text-[hsl(var(--btn-disabled-text))] disabled:border-[hsl(var(--btn-disabled-border))] disabled:opacity-100",
        outline: "bg-[hsl(var(--btn-default-bg))] text-[hsl(var(--btn-default-text))] border border-[hsl(var(--btn-default-border))] hover:bg-[hsl(var(--btn-default-bg-hover))] hover:text-[hsl(var(--btn-default-text-hover))] hover:border-[hsl(var(--btn-default-border-hover))] active:bg-[hsl(var(--btn-default-bg-press))] active:text-[hsl(var(--btn-default-text-press))] active:border-[hsl(var(--btn-default-border-press))] disabled:bg-[hsl(var(--btn-disabled-bg))] disabled:text-[hsl(var(--btn-disabled-text))] disabled:border-[hsl(var(--btn-disabled-border))] disabled:opacity-100",
        secondary: "bg-[hsl(var(--secondary))] text-[hsl(var(--secondary-foreground))] border border-transparent hover:bg-[hsl(var(--secondary))]/80 disabled:bg-[hsl(var(--btn-disabled-bg))] disabled:text-[hsl(var(--btn-disabled-text))] disabled:opacity-100",
        ghost: "bg-[hsl(var(--btn-tertiary-bg))] text-[hsl(var(--btn-tertiary-text))] border border-transparent hover:bg-[hsl(var(--btn-tertiary-bg-hover))] hover:text-[hsl(var(--btn-tertiary-text-hover))] disabled:bg-[hsl(var(--btn-disabled-bg))] disabled:text-[hsl(var(--btn-disabled-text))] disabled:opacity-100",
      },
      size: {
        // Du Bois size variations
        sm: "h-8 px-3 py-1 text-xs rounded-md min-w-8",
        default: "h-10 px-4 py-2 text-sm rounded-md min-w-10",
        lg: "h-12 px-6 py-3 text-base rounded-md min-w-12",
        icon: "h-10 w-10 p-0 rounded-md",
      }
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  },
);

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  asChild?: boolean;
  loading?: boolean;
  loadingText?: string;
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ 
    className, 
    variant, 
    size, 
    asChild = false, 
    loading = false,
    loadingText,
    children,
    disabled,
    ...props 
  }, ref) => {
    const Comp = asChild ? Slot : "button";
    const isDisabled = disabled || loading;
    
    const content = loading 
      ? (
          <>
            <Loader2 className="animate-spin" />
            {loadingText || children}
          </>
        )
      : children;
    
    return (
      <Comp
        className={cn(buttonVariants({ variant, size, className }))}
        ref={ref}
        disabled={isDisabled}
        {...props}
      >
        {content}
      </Comp>
    );
  },
);
Button.displayName = "Button";

export { Button, buttonVariants };
