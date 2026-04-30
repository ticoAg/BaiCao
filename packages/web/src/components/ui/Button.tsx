import type { ButtonHTMLAttributes, ReactNode } from "react";
import { forwardRef } from "react";
import { cx } from "./radix";

type ButtonVariant = "primary" | "secondary" | "ghost" | "danger";
type ButtonSize = "sm" | "small" | "md" | "middle" | "large";

type AppButtonProps = Omit<ButtonHTMLAttributes<HTMLButtonElement>, "type"> & {
  variant?: ButtonVariant;
  type?: "primary" | "default" | "text" | "link" | "dashed" | "submit";
  htmlType?: "button" | "submit" | "reset";
  size?: ButtonSize;
  icon?: ReactNode;
  full?: boolean;
  block?: boolean;
  danger?: boolean;
  loading?: boolean;
};

const AppButton = forwardRef<HTMLButtonElement, AppButtonProps>(
  (
    {
      className,
      variant = "secondary",
      type,
      htmlType,
      size = "md",
      icon,
      full = false,
      block = false,
      danger = false,
      loading = false,
      children,
      disabled,
      ...props
    },
    ref,
  ) => {
    const visualVariant: ButtonVariant = danger
      ? "danger"
      : type === "primary"
        ? "primary"
        : type === "text" || type === "link"
          ? "ghost"
          : variant;

    return (
      <button
        ref={ref}
        type={htmlType ?? (type === "submit" ? "submit" : "button")}
        className={cx(
          "bc-button",
          `bc-button--${visualVariant}`,
          `bc-button--${size === "sm" || size === "small" ? "sm" : "md"}`,
          (full || block) && "bc-button--full",
          loading && "bc-button--loading",
          className,
        )}
        disabled={disabled || loading}
        {...props}
      >
        {loading ? <span className="bc-button-spinner" aria-hidden="true" /> : null}
        {icon ? <span className="bc-button-icon" aria-hidden="true">{icon}</span> : null}
        {children ? <span className="bc-button-label">{children}</span> : null}
      </button>
    );
  },
);

AppButton.displayName = "AppButton";

export default AppButton;
