import { Button, Space } from "antd";

type WorkbenchSidebarRailProps = {
  selectedDrawer: "guides" | "history" | "favorites" | "settings" | null;
  onSelect: (drawer: "guides" | "history" | "favorites" | "settings") => void;
};

const railButtons = [
  { key: "guides", label: "指南", ariaLabel: "打开指南抽屉" },
  { key: "history", label: "历史", ariaLabel: "打开历史抽屉" },
  { key: "favorites", label: "收藏", ariaLabel: "打开收藏抽屉" },
  { key: "settings", label: "设置", ariaLabel: "打开设置抽屉" },
] as const;

const WorkbenchSidebarRail = ({ selectedDrawer, onSelect }: WorkbenchSidebarRailProps) => {
  return (
    <div
      data-testid="workbench-rail"
      style={{
        width: 64,
        borderRadius: 20,
        background: "#163123",
        padding: 12,
        color: "#fff",
      }}
    >
      <Space direction="vertical" size={12} style={{ width: "100%" }}>
        {railButtons.map((item) => {
          const isActive = selectedDrawer === item.key;

          return (
            <Button
              key={item.key}
              block
              type={isActive ? "primary" : "default"}
              aria-label={item.ariaLabel}
              aria-pressed={isActive}
              onClick={() => onSelect(item.key)}
              style={
                isActive
                  ? {
                      borderRadius: 14,
                      boxShadow: "0 8px 18px rgba(8, 15, 23, 0.24)",
                    }
                  : { borderRadius: 14 }
              }
            >
              {item.label}
            </Button>
          );
        })}
      </Space>
    </div>
  );
};

export default WorkbenchSidebarRail;
