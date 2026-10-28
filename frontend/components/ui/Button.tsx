import type { ComponentPropsWithoutRef, ReactNode } from "react";
import Link from "next/link";

type Variant = "primary" | "secondary" | "ghost" | "onNavy" | "onNavyOutline";
type Size = "sm" | "md" | "lg";

const variants: Record<Variant, string> = {
  primary:
    "bg-[var(--teal)] text-[var(--navy)] hover:brightness-110 shadow-[var(--shadow-sm)]",
  secondary:
    "border border-[var(--line)] bg-[var(--panel)] text-[var(--ink)] hover:bg-[var(--surface)]",
  ghost: "text-[var(--muted)] hover:text-[var(--ink)] hover:bg-[var(--surface)]",
  onNavy:
    "bg-[var(--teal)] text-[var(--navy)] hover:brightness-110 shadow-[var(--shadow-sm)]",
  onNavyOutline:
    "border border-white/20 text-[var(--on-navy)] hover:border-white/50 hover:bg-white/5",
};

const sizes: Record<Size, string> = {
  sm: "rounded-full px-4 py-2 text-sm font-semibold",
  md: "rounded-full px-5 py-2.5 text-sm font-semibold",
  lg: "rounded-full px-6 py-3.5 text-sm font-semibold sm:text-base",
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
  const classes = `inline-flex items-center justify-center gap-2 transition active:scale-[0.98] focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--focus-ring)] ${variants[variant]} ${sizes[size]} ${className}`;

  if ("href" in rest && rest.href) {
    const { href, ...linkRest } = rest;
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
