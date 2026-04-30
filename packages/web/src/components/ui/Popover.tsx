import type { ReactNode } from "react";
import { Popover } from "radix-ui";
import { cx } from "./radix";

type AppPopoverProps = {
  trigger: ReactNode;
  title?: ReactNode;
  children: ReactNode;
  className?: string;
  align?: "start" | "center" | "end";
  side?: "top" | "right" | "bottom" | "left";
};

const AppPopover = ({
  trigger,
  title,
  children,
  className,
  align = "end",
  side = "bottom",
}: AppPopoverProps) => (
  <Popover.Root>
    <Popover.Trigger asChild>{trigger}</Popover.Trigger>
    <Popover.Portal>
      <Popover.Content
        className={cx("bc-popover-content", className)}
        align={align}
        side={side}
        sideOffset={10}
      >
        {title ? <div className="bc-popover-title">{title}</div> : null}
        {children}
        <Popover.Arrow className="bc-popover-arrow" />
      </Popover.Content>
    </Popover.Portal>
  </Popover.Root>
);

export default AppPopover;
