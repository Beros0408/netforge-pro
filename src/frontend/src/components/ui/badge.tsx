import * as React from 'react';
import { cva, type VariantProps } from 'class-variance-authority';
import { cn } from '@/lib/utils';

const badgeVariants = cva(
  'inline-flex items-center rounded px-1.5 py-0.5 text-xs font-medium border',
  {
    variants: {
      variant: {
        default:  'bg-[var(--bg-elevated)] text-[var(--text-secondary)] border-[var(--border-default)]',
        cisco:    'bg-[var(--accent-cisco)]/10 text-[var(--accent-cisco)] border-[var(--accent-cisco)]/30',
        fortinet: 'bg-[var(--accent-fortinet)]/10 text-[var(--accent-fortinet)] border-[var(--accent-fortinet)]/30',
        huawei:   'bg-[var(--accent-huawei)]/10 text-[var(--accent-huawei)] border-[var(--accent-huawei)]/30',
        green:    'bg-[var(--accent-green)]/10 text-[var(--accent-green)] border-[var(--accent-green)]/30',
        amber:    'bg-[var(--accent-amber)]/10 text-[var(--accent-amber)] border-[var(--accent-amber)]/30',
        red:      'bg-[var(--accent-red)]/10 text-[var(--accent-red)] border-[var(--accent-red)]/30',
      },
    },
    defaultVariants: { variant: 'default' },
  }
);

export interface BadgeProps
  extends React.HTMLAttributes<HTMLSpanElement>,
    VariantProps<typeof badgeVariants> {}

export function Badge({ className, variant, ...props }: BadgeProps) {
  return <span className={cn(badgeVariants({ variant }), className)} {...props} />;
}
