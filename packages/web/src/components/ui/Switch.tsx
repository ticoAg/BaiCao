import { Switch as SwitchPrimitive } from "radix-ui";
import { cx } from "./radix";

type AppSwitchProps = {
  checked: boolean;
  onCheckedChange: (checked: boolean) => void;
  "aria-label": string;
  className?: string;
};

const AppSwitch = ({ checked, onCheckedChange, className, "aria-label": ariaLabel }: AppSwitchProps) => (
  <SwitchPrimitive.Root
    className={cx("bc-switch-root", className)}
    checked={checked}
    onCheckedChange={onCheckedChange}
    aria-label={ariaLabel}
  >
    <SwitchPrimitive.Thumb className="bc-switch-thumb" />
  </SwitchPrimitive.Root>
);

export default AppSwitch;
