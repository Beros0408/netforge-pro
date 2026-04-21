import * as React from 'react';
import { cva, type VariantProps } from 'class-variance-authority';
import { cn } from '@/lib/utils';

const buttonVariants = cva(
  'inline-flex items-center justify-center rounded-md text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-[var(--border-strong)] disabled:pointer-events-none disabled:opacity-50',
  {
    variants: {
      variant: {
        default:  'bg-[var(--bg-interactive)] text-[var(--text-primary)] border border-[var(--border-strong)] hover:bg-[var(--bg-elevated)]',
        primary:  'bg-[var(--accent-cisco)] text-white hover:opacity-90',
        ghost:    'hover:bg-[var(--bg-interactive)] text-[var(--text-secondary)]',
        danger:   'bg-[var(--accent-red)] text-white hover:opacity-90',
      },
      size: {
        default: 'h-8 px-3 py-1.5',
        sm:      'h-7 px-2 text-xs',
        lg:      'h-10 px-4',
        icon:    'h-8 w-8',
      },
    },
    defaultVariants: { variant: 'default', size: 'default' },
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
Button.displayName = 'Button';
