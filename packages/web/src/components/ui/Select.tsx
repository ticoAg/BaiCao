import { CheckIcon, ChevronDownIcon } from "@radix-ui/react-icons";
import { Select } from "radix-ui";
import { cx } from "./radix";

export type SelectOption = {
  value: string;
  label: string;
};

type AppSelectProps = {
  value?: string | null;
  onChange?: (value: any) => void;
  onValueChange?: (value: any) => void;
  options: SelectOption[];
  placeholder?: string;
  className?: string;
  "aria-label"?: string;
  allowClear?: boolean;
  disabled?: boolean;
};

const AppSelect = ({
  value,
  onChange,
  onValueChange,
  options,
  placeholder,
  className,
  "aria-label": ariaLabel,
  disabled,
}: AppSelectProps) => (
  <Select.Root value={value ?? ""} onValueChange={onChange ?? onValueChange} disabled={disabled}>
    <Select.Trigger className={cx("bc-select-trigger", className)} aria-label={ariaLabel} disabled={disabled}>
      <Select.Value placeholder={placeholder} />
      <Select.Icon className="bc-select-icon">
        <ChevronDownIcon />
      </Select.Icon>
    </Select.Trigger>
    <Select.Portal>
      <Select.Content className="bc-select-content" position="popper" sideOffset={6}>
        <Select.Viewport className="bc-select-viewport">
          {options.map((option) => (
            <Select.Item className="bc-select-item" key={option.value} value={option.value}>
              <Select.ItemText>{option.label}</Select.ItemText>
              <Select.ItemIndicator className="bc-select-item-indicator">
                <CheckIcon />
              </Select.ItemIndicator>
            </Select.Item>
          ))}
        </Select.Viewport>
      </Select.Content>
    </Select.Portal>
  </Select.Root>
);

export default AppSelect;
