import type { ButtonHTMLAttributes, ReactNode } from "react";

type ButtonVariant = "primary" | "secondary" | "ghost";
type ButtonSize = "small" | "medium" | "large";

type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  children: ReactNode;
  size?: ButtonSize;
  variant?: ButtonVariant;
};

const variantClass: Record<ButtonVariant, string> = {
  primary: "buttonPrimary",
  secondary: "buttonSecondary",
  ghost: "buttonGhost"
};

const sizeClass: Record<ButtonSize, string> = {
  small: "buttonSmall",
  medium: "",
  large: "buttonLarge"
};

export function Button({
  children,
  className = "",
  size = "medium",
  variant = "secondary",
  ...props
}: ButtonProps) {
  const classes = ["button", variantClass[variant], sizeClass[size], className]
    .filter(Boolean)
    .join(" ");

  return (
    <button className={classes} {...props}>
      {children}
    </button>
  );
}
