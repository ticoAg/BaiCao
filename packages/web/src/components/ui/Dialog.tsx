import type { CSSProperties, ReactNode } from "react";
import { Dialog } from "radix-ui";
import { Cross1Icon } from "@radix-ui/react-icons";
import { cx } from "./radix";

type ModalDialogProps = {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  title: ReactNode;
  description?: ReactNode;
  children: ReactNode;
  className?: string;
  width?: number | string;
};

const ModalDialog = ({
  open,
  onOpenChange,
  title,
  description,
  children,
  className,
  width,
}: ModalDialogProps) => (
  <Dialog.Root open={open} onOpenChange={onOpenChange}>
    <Dialog.Portal>
      <Dialog.Overlay className="bc-dialog-overlay">
        <Dialog.Content
          className={cx("bc-dialog-content", className)}
          style={{ "--bc-dialog-width": typeof width === "number" ? `${width}px` : width } as CSSProperties}
          aria-describedby={description ? undefined : undefined}
        >
          <div className="bc-dialog-header">
            <div>
              <Dialog.Title className="bc-dialog-title">{title}</Dialog.Title>
              {description ? (
                <Dialog.Description className="bc-dialog-description">
                  {description}
                </Dialog.Description>
              ) : null}
            </div>
            <Dialog.Close className="bc-dialog-close" aria-label="关闭弹窗">
              <Cross1Icon />
            </Dialog.Close>
          </div>
          <div className="bc-dialog-body">{children}</div>
        </Dialog.Content>
      </Dialog.Overlay>
    </Dialog.Portal>
  </Dialog.Root>
);

export default ModalDialog;
