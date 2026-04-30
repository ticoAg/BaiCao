import type { InputHTMLAttributes, TextareaHTMLAttributes } from "react";
import { forwardRef } from "react";
import { cx } from "./radix";

type TextInputProps = Omit<InputHTMLAttributes<HTMLInputElement>, "value"> & {
  value?: InputHTMLAttributes<HTMLInputElement>["value"] | null;
  allowClear?: boolean;
};
type TextAreaProps = Omit<TextareaHTMLAttributes<HTMLTextAreaElement>, "value"> & {
  value?: TextareaHTMLAttributes<HTMLTextAreaElement>["value"] | null;
  allowClear?: boolean;
  autoSize?: boolean | { minRows?: number; maxRows?: number };
  onPressEnter?: (event: React.KeyboardEvent<HTMLTextAreaElement>) => void;
  styles?: { textarea?: React.CSSProperties };
};

export const TextInput = forwardRef<HTMLInputElement, TextInputProps>(
  ({ className, value, allowClear: _allowClear, ...props }, ref) => (
    <input
      ref={ref}
      className={cx("bc-field", className)}
      value={value === null ? "" : value}
      {...props}
    />
  ),
);

TextInput.displayName = "TextInput";

export const TextArea = forwardRef<HTMLTextAreaElement, TextAreaProps>(
  ({ className, value, onPressEnter, autoSize: _autoSize, allowClear: _allowClear, styles, style, ...props }, ref) => (
    <textarea
      {...props}
      ref={ref}
      className={cx("bc-field bc-field--area", className)}
      style={{ ...styles?.textarea, ...style }}
      value={value === null ? "" : value}
      onKeyDown={(event) => {
        props.onKeyDown?.(event);
        if (event.key === "Enter") onPressEnter?.(event);
      }}
    />
  ),
);

TextArea.displayName = "TextArea";
