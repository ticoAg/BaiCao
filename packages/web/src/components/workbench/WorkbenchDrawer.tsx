import { Empty, List, Space, Tag, Typography } from "../ui/index";
import type { WorkbenchHistoryItem } from "../../types/workbench";
import AppSwitch from "../ui/Switch";
import AppButton from "../ui/Button";

type DrawerName = "guides" | "history" | "favorites" | "settings" | null;

const drawerTitles: Record<Exclude<DrawerName, null>, string> = {
  guides: "使用指南",
  history: "命令历史",
  favorites: "收藏命令",
  settings: "工作台设置",
};

type WorkbenchDrawerProps = {
  selectedDrawer: DrawerName;
  history: WorkbenchHistoryItem[];
  favorites: WorkbenchHistoryItem[];
  showStarterCommands: boolean;
  onClose: () => void;
  onPickCommand: (command: string) => void;
  onToggleStarterCommands: (show: boolean) => void;
};

const { Paragraph, Text } = Typography;

const guideItems = [
  { title: "帮助命令", command: ":help", note: "查看当前工作台支持的命令和输入方式" },
  { title: "清空结果", command: ":clear", note: "清掉当前 stream，保留编辑器内容" },
  { title: "自然语言查询", command: "查人参的功效", note: "让工作台走语义查询而不是手写 Cypher" },
];

const WorkbenchDrawer = ({
  selectedDrawer,
  history,
  favorites,
  showStarterCommands,
  onClose,
  onPickCommand,
  onToggleStarterCommands,
}: WorkbenchDrawerProps) => {
  if (!selectedDrawer) return null;

  return (
    <div
      data-testid="workbench-drawer"
      className="workbench-drawer"
      style={{
        width: 260,
        borderRadius: 20,
        background: "#f7faf8",
        border: "1px solid rgba(20, 42, 30, 0.08)",
        padding: 18,
      }}
    >
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <Text strong style={{ fontSize: 16, color: "#203127" }}>
          {drawerTitles[selectedDrawer]}
        </Text>
        <AppButton variant="ghost" size="sm" onClick={onClose} aria-label="关闭抽屉">
          关闭
        </AppButton>
      </div>

      <Text type="secondary" style={{ display: "block", marginTop: 12 }}>
        {selectedDrawer === "history"
          ? "最近运行过的命令会出现在这里，点击即可回填到编辑器。"
          : selectedDrawer === "guides"
            ? "Browser 风格工作台会把常用命令和查询入口集中在这里。"
            : selectedDrawer === "favorites"
              ? "把常用命令固定在这里，随时回填到编辑器。"
              : "内容稍后接入。"}
      </Text>

      {selectedDrawer === "history" ? (
        history.length ? (
          <List
            style={{ marginTop: 16 }}
            dataSource={history}
            renderItem={(item) => (
              <List.Item style={{ paddingInline: 0 }}>
                <AppButton
                  full
                  onClick={() => onPickCommand(item.command)}
                  aria-label={`回填命令 ${item.command}`}
                  style={{ height: "auto", padding: "10px 12px", textAlign: "left" }}
                >
                  <Space direction="vertical" size={4} style={{ width: "100%", alignItems: "flex-start" }}>
                    <Text strong style={{ color: "#203127" }}>
                      {item.command}
                    </Text>
                    <Text type="secondary" style={{ fontSize: 12 }}>
                      {item.executedAt
                        ? new Date(item.executedAt).toLocaleString("zh-CN")
                        : "刚刚执行"}
                    </Text>
                  </Space>
                </AppButton>
              </List.Item>
            )}
          />
        ) : (
          <div style={{ marginTop: 20 }}>
            <Empty
              image={Empty.PRESENTED_IMAGE_SIMPLE}
              description="还没有命令历史。先运行 :help 或自然语言查询。"
            />
          </div>
        )
      ) : null}

      {selectedDrawer === "guides" ? (
        <div className="workbench-guide-sections" style={{ marginTop: 16 }}>
          <div className="workbench-guide-panel">
            <Text strong style={{ color: "#203127", display: "block" }}>
              开始探索
            </Text>
            <Paragraph type="secondary" style={{ margin: "8px 0 12px", fontSize: 12 }}>
              从一条命令开始，让工作台返回图谱、文本或错误结果帧。
            </Paragraph>
            <Space direction="vertical" size={10} style={{ width: "100%" }}>
              <AppButton
                full
                onClick={() => onPickCommand("查人参的功效")}
                aria-label="插入命令 查人参的功效"
                style={{ height: "auto", padding: "12px", textAlign: "left" }}
              >
                <Space direction="vertical" size={4} style={{ width: "100%", alignItems: "flex-start" }}>
                  <Text strong style={{ color: "#203127" }}>
                    语义查询起步
                  </Text>
                  <Text type="secondary" style={{ fontSize: 12 }}>
                    先用自然语言试一条真实查询，再逐步切到 Cypher。
                  </Text>
                </Space>
              </AppButton>
            </Space>
          </div>

          <div className="workbench-guide-panel">
            <Text strong style={{ color: "#203127", display: "block" }}>
              常用命令
            </Text>
            <List
              style={{ marginTop: 8 }}
              dataSource={guideItems}
              renderItem={(item) => (
                <List.Item style={{ paddingInline: 0 }}>
                  <AppButton
                    full
                    onClick={() => onPickCommand(item.command)}
                    aria-label={`插入命令 ${item.command}`}
                    style={{ height: "auto", padding: "12px", textAlign: "left" }}
                  >
                    <Space direction="vertical" size={6} style={{ width: "100%", alignItems: "flex-start" }}>
                      <Space size={8} wrap>
                        <Text strong style={{ color: "#203127" }}>
                          {item.title}
                        </Text>
                        <Tag style={{ borderRadius: 999, marginInlineEnd: 0 }}>{item.command}</Tag>
                      </Space>
                      <Paragraph type="secondary" style={{ marginBottom: 0, fontSize: 12 }}>
                        {item.note}
                      </Paragraph>
                    </Space>
                  </AppButton>
                </List.Item>
              )}
            />
          </div>
        </div>
      ) : null}

      {selectedDrawer === "favorites" ? (
        favorites.length ? (
          <List
            style={{ marginTop: 16 }}
            dataSource={favorites}
            renderItem={(item) => (
              <List.Item style={{ paddingInline: 0 }}>
                <AppButton
                  full
                  onClick={() => onPickCommand(item.command)}
                  aria-label={`回填收藏命令 ${item.command}`}
                  style={{ height: "auto", padding: "10px 12px", textAlign: "left" }}
                >
                  <Space direction="vertical" size={4} style={{ width: "100%", alignItems: "flex-start" }}>
                    <Text strong style={{ color: "#203127" }}>
                      {item.command}
                    </Text>
                    <Text type="secondary" style={{ fontSize: 12 }}>
                      {item.executedAt
                        ? new Date(item.executedAt).toLocaleString("zh-CN")
                        : "刚刚收藏"}
                    </Text>
                  </Space>
                </AppButton>
              </List.Item>
            )}
          />
        ) : (
          <div style={{ marginTop: 20 }}>
            <Empty
              image={Empty.PRESENTED_IMAGE_SIMPLE}
              description="还没有收藏命令。先在编辑器里收藏一条常用查询。"
            />
          </div>
        )
      ) : null}

      {selectedDrawer === "settings" ? (
        <Space direction="vertical" size={16} style={{ marginTop: 18, width: "100%" }}>
          <div
            style={{
              padding: 14,
              borderRadius: 16,
              background: "#ffffff",
              border: "1px solid rgba(20, 42, 30, 0.08)",
            }}
          >
            <Space style={{ width: "100%", justifyContent: "space-between" }} align="start">
              <div>
                <Text strong style={{ color: "#203127" }}>
                  显示起手命令
                </Text>
                <Paragraph type="secondary" style={{ margin: "6px 0 0", fontSize: 12 }}>
                  在编辑器顶部显示 `:help`、`:clear` 和自然语言起手查询。
                </Paragraph>
              </div>
              <AppSwitch
                aria-label="显示起手命令"
                checked={showStarterCommands}
                onCheckedChange={onToggleStarterCommands}
              />
            </Space>
          </div>
          <div
            style={{
              padding: 14,
              borderRadius: 16,
              background: "#ffffff",
              border: "1px solid rgba(20, 42, 30, 0.08)",
            }}
          >
            <Text strong style={{ color: "#203127" }}>
              当前模式
            </Text>
            <Paragraph type="secondary" style={{ margin: "8px 0 0", fontSize: 12 }}>
              Workbench 目前默认使用 Browser 风格的命令编辑器、frame stream 和右侧结果检查器。
            </Paragraph>
          </div>
        </Space>
      ) : null}
    </div>
  );
};

export default WorkbenchDrawer;
