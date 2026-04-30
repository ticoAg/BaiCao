// 通知铃铛组件 - 显示未读通知数 + 下拉面板
import { BellOutlined } from "./ui/icons";
import { useNavigate } from "react-router-dom";
import { useNotifications } from "../hooks/useNotifications";
import type { Notification } from "../services/api";
import AppPopover from "./ui/Popover";
import { AppBadge, EmptyState, Spinner } from "./ui/Status";

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
    <button
      type="button"
      className="notification-item"
      onClick={handleClick}
      data-unread={!item.read}
    >
      <span className="notification-item-main">
        <span className="notification-item-title">{item.title}</span>
        {item.content?.message ? (
          <span className="notification-item-message">{item.content.message}</span>
        ) : null}
        <span className="notification-item-meta">
          {new Date(item.created_at).toLocaleString("zh-CN")}
          {item.content?.verdict ? (
            <AppBadge tone={item.content.verdict === "verified" ? "success" : "danger"}>
              {item.content.verdict === "verified" ? "已通过" : "已拒绝"}
            </AppBadge>
          ) : null}
        </span>
      </span>
      {!item.read ? <span className="notification-unread-dot" aria-hidden="true" /> : null}
    </button>
  );
};

const NotificationPanel = () => {
  const { notifications, loading, markAsRead } = useNotifications();

  if (loading) {
    return (
      <div className="notification-loading">
        <Spinner />
      </div>
    );
  }

  if (notifications.length === 0) {
    return <EmptyState description="暂无通知" />;
  }

  return (
    <div className="notification-list">
      {notifications.map((item) => (
        <NotificationItem key={item.id} item={item} onRead={markAsRead} />
      ))}
    </div>
  );
};

const NotificationBell = () => {
  const { unreadCount } = useNotifications();

  return (
    <AppPopover
      title="通知"
      trigger={
        <button className="notification-trigger" type="button" aria-label="打开通知">
          <BellOutlined style={{ fontSize: 18, color: "#fff" }} />
          {unreadCount > 0 ? (
            <span className="notification-count" aria-label={`${unreadCount} 条未读通知`}>
              {unreadCount > 99 ? "99+" : unreadCount}
            </span>
          ) : null}
        </button>
      }
    >
      <NotificationPanel />
    </AppPopover>
  );
};

export default NotificationBell;
