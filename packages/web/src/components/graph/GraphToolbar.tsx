import { memo } from "react"
import { Button, Space, Tooltip } from "antd"
import {
  ZoomInOutlined,
  ZoomOutOutlined,
  CompressOutlined,
} from "@ant-design/icons"

interface GraphToolbarProps {
  onZoomIn: () => void
  onZoomOut: () => void
  onZoomToFit: () => void
}

const GraphToolbar = ({ onZoomIn, onZoomOut, onZoomToFit }: GraphToolbarProps) => {
  return (
    <div
      style={{
        position: "absolute",
        bottom: 16,
        right: 16,
        zIndex: 3,
      }}
    >
      <Space direction="vertical" size={4}>
        <Tooltip title="放大" placement="left">
          <Button
            size="small"
            icon={<ZoomInOutlined />}
            onClick={onZoomIn}
            style={{ background: "rgba(255,255,255,0.92)", border: "1px solid #d9d9d9" }}
          />
        </Tooltip>
        <Tooltip title="缩小" placement="left">
          <Button
            size="small"
            icon={<ZoomOutOutlined />}
            onClick={onZoomOut}
            style={{ background: "rgba(255,255,255,0.92)", border: "1px solid #d9d9d9" }}
          />
        </Tooltip>
        <Tooltip title="适应画布" placement="left">
          <Button
            size="small"
            icon={<CompressOutlined />}
            onClick={onZoomToFit}
            style={{ background: "rgba(255,255,255,0.92)", border: "1px solid #d9d9d9" }}
          />
        </Tooltip>
      </Space>
    </div>
  )
}

export default memo(GraphToolbar)
