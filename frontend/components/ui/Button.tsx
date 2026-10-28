import type { ComponentPropsWithoutRef, ReactNode } from "react";
import Link from "next/link";

type Variant = "primary" | "secondary" | "ghost" | "onNavy" | "onNavyOutline";
type Size = "sm" | "md" | "lg";

const variants: Record<Variant, string> = {
  primary:
    "bg-[var(--accent)] text-[var(--on-accent)] hover:bg-[var(--accent-hover)] shadow-[var(--shadow-sm)]",
  secondary:
    "border border-[var(--line)] bg-[var(--panel)] text-[var(--ink)] hover:bg-[var(--surface)]",
  ghost: "text-[var(--muted)] hover:text-[var(--ink)] hover:bg-[var(--surface)]",
  onNavy:
    "bg-[var(--accent)] text-[var(--on-accent)] hover:bg-[var(--accent-hover)] shadow-[var(--shadow-sm)]",
  onNavyOutline:
    "border border-[var(--on-navy-border)] text-[var(--on-navy)] hover:bg-[var(--on-navy-faint)]",
};

const sizes: Record<Size, string> = {
  sm: "rounded-full px-4 py-2 text-[length:var(--text-sm)] font-[number:var(--weight-semibold)]",
  md: "rounded-full px-5 py-2.5 text-[length:var(--text-sm)] font-[number:var(--weight-semibold)]",
  lg: "rounded-full px-6 py-3.5 text-[length:var(--text-sm)] sm:text-[length:var(--text-md)] font-[number:var(--weight-semibold)]",
};

type Common = {
  variant?: Variant;
  size?: Size;
  leftIcon?: ReactNode;
  rightIcon?: ReactNode;
  className?: string;
  children: ReactNode;
};

type ButtonAsButton = Common &
  Omit<ComponentPropsWithoutRef<"button">, "className" | "children"> & { href?: undefined };

type ButtonAsLink = Common & { href: string } & Omit<
  ComponentPropsWithoutRef<typeof Link>,
  "className" | "children" | "href"
>;

export type ButtonProps = ButtonAsButton | ButtonAsLink;

export function Button({
  variant = "primary",
  size = "md",
  leftIcon,
  rightIcon,
  className = "",
  children,
  ...rest
}: ButtonProps) {
  const classes = `inline-flex items-center justify-center gap-2 transition active:scale-[0.98] focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--focus-ring)] disabled:opacity-50 ${variants[variant]} ${sizes[size]} ${className}`;

  if ("href" in rest && rest.href) {
    const { href, ...linkRest } = rest;
    const external = /^(mailto:|https?:|tel:)/i.test(href);
    if (external) {
      return (
        <a href={href} className={classes}>
          {leftIcon}
          {children}
          {rightIcon}
        </a>
      );
    }
    return (
      <Link href={href} className={classes} {...linkRest}>
        {leftIcon}
        {children}
        {rightIcon}
      </Link>
    );
  }

  const buttonRest = rest as ButtonAsButton;
  return (
    <button type={buttonRest.type ?? "button"} className={classes} {...buttonRest}>
      {leftIcon}
      {children}
      {rightIcon}
    </button>
  );
}
