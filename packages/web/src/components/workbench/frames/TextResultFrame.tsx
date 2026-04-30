import { Typography } from "../../ui/index";
import type { WorkbenchFrame } from "../../../types/workbench";
import FrameChrome from "./FrameChrome";

const { Paragraph } = Typography;

type TextResultFrameProps = {
  frame: WorkbenchFrame;
  onDismiss?: () => void;
  onRerun?: () => void;
};

const TextResultFrame = ({ frame, onDismiss, onRerun }: TextResultFrameProps) => {
  const markdown = String(frame.payload.markdown ?? "");

  return (
    <FrameChrome frame={frame} onDismiss={onDismiss} onRerun={onRerun}>
      <div style={{ padding: 18 }}>
        <Paragraph style={{ marginBottom: 0, whiteSpace: "pre-wrap" }}>
          {markdown}
        </Paragraph>
      </div>
    </FrameChrome>
  );
};

export default TextResultFrame;
