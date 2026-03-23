import { Table } from "antd";
import type { ColumnsType } from "antd/es/table";
import type { WorkbenchFrame } from "../../../types/workbench";
import FrameChrome from "./FrameChrome";

type TableResultFrameProps = {
  frame: WorkbenchFrame;
  onDismiss?: () => void;
  onRerun?: () => void;
};

const TableResultFrame = ({ frame, onDismiss, onRerun }: TableResultFrameProps) => {
  const columnsSource = Array.isArray(frame.payload.columns)
    ? frame.payload.columns.map((column) => String(column))
    : [];
  const rows = Array.isArray(frame.payload.rows)
    ? frame.payload.rows.map((row, index) => ({ key: `row-${index}`, ...(row as Record<string, unknown>) }))
    : [];

  const columns: ColumnsType<Record<string, unknown>> = columnsSource.map((column) => ({
    title: column,
    dataIndex: column,
    key: column,
    render: (value) => {
      if (value == null) return "—";
      if (typeof value === "object") return JSON.stringify(value);
      return String(value);
    },
  }));

  return (
    <FrameChrome frame={frame} onDismiss={onDismiss} onRerun={onRerun}>
      <Table
        size="small"
        pagination={false}
        columns={columns}
        dataSource={rows}
        scroll={{ x: true }}
      />
    </FrameChrome>
  );
};

export default TableResultFrame;
