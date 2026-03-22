// 通知铃铛组件 - 显示未读通知数 + 下拉面板
import { Badge, Popover, List, Typography, Tag, Empty, Spin } from "antd";
import { BellOutlined } from "@ant-design/icons";
import { useNavigate } from "react-router-dom";
import { useNotifications } from "../hooks/useNotifications";
import type { Notification } from "../services/api";

const { Text } = Typography;

const NotificationItem = ({
  item,
  onRead,
}: {
  item: Notification;
  onRead: (id: string) => void;
}) => {
  const navigate = useNavigate();

  const handleClick = () => {
    if (!item.read) onRead(item.id);
    if (item.content?.link) {
      navigate(item.content.link);
    }
  };

  return (
    <List.Item
      onClick={handleClick}
      style={{
        cursor: item.content?.link ? "pointer" : "default",
        background: item.read ? "transparent" : "#f0f9ff",
        padding: "8px 12px",
        borderRadius: 6,
        marginBottom: 4,
      }}
    >
      <List.Item.Meta
        title={
          <Text strong={!item.read} style={{ fontSize: 13 }}>
            {item.title}
          </Text>
        }
        description={
          <div>
            {item.content?.message && (
              <Text type="secondary" style={{ fontSize: 12 }}>
                {item.content.message}
              </Text>
            )}
            {item.content?.verdict && (
              <Tag
                color={item.content.verdict === "verified" ? "green" : "red"}
                style={{ marginLeft: 4, fontSize: 11 }}
              >
                {item.content.verdict === "verified" ? "已通过" : "已拒绝"}
              </Tag>
            )}
            <div>
              <Text type="secondary" style={{ fontSize: 11 }}>
                {new Date(item.created_at).toLocaleString("zh-CN")}
              </Text>
            </div>
          </div>
        }
      />
      {!item.read && (
        <Badge status="processing" style={{ marginLeft: 8 }} />
      )}
    </List.Item>
  );
};

const NotificationPanel = () => {
  const { notifications, loading, markAsRead } = useNotifications();

  if (loading) {
    return (
      <div style={{ padding: 24, textAlign: "center" }}>
        <Spin size="small" />
      </div>
    );
  }

  if (notifications.length === 0) {
    return (
      <Empty
        description="暂无通知"
        image={Empty.PRESENTED_IMAGE_SIMPLE}
        style={{ padding: "24px 0" }}
      />
    );
  }

  return (
    <List
      style={{ width: 320, maxHeight: 400, overflow: "auto" }}
      dataSource={notifications}
      renderItem={(item) => (
        <NotificationItem key={item.id} item={item} onRead={markAsRead} />
      )}
    />
  );
};

const NotificationBell = () => {
  const { unreadCount } = useNotifications();

  return (
    <Popover
      content={<NotificationPanel />}
      title="通知"
      trigger="click"
      placement="bottomRight"
    >
      <Badge count={unreadCount} size="small" offset={[-2, 2]}>
        <BellOutlined
          style={{
            fontSize: 18,
            color: "#fff",
            cursor: "pointer",
            padding: "0 8px",
          }}
        />
      </Badge>
    </Popover>
  );
};

export default NotificationBell;
