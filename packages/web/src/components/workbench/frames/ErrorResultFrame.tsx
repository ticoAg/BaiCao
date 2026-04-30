import { Alert } from "../../ui/index";
import type { WorkbenchFrame } from "../../../types/workbench";
import FrameChrome from "./FrameChrome";

type ErrorResultFrameProps = {
  frame: WorkbenchFrame;
  onDismiss?: () => void;
  onRerun?: () => void;
};

const ErrorResultFrame = ({ frame, onDismiss, onRerun }: ErrorResultFrameProps) => {
  const message = String(frame.payload.message ?? "Unknown error");
  const details = Array.isArray(frame.payload.details)
    ? frame.payload.details.map((item) => String(item))
    : [];

  return (
    <FrameChrome frame={frame} onDismiss={onDismiss} onRerun={onRerun}>
      <div style={{ padding: 18 }}>
        <Alert
          message={message}
          description={
            details.length ? (
              <ul style={{ margin: 0, paddingInlineStart: 18 }}>
                {details.map((detail) => (
                  <li key={detail}>{detail}</li>
                ))}
              </ul>
            ) : null
          }
          type="error"
          showIcon
        />
      </div>
    </FrameChrome>
  );
};

export default ErrorResultFrame;
