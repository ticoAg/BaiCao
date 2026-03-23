import { Link, useLocation } from "react-router-dom";
import { Layout, Menu } from "antd";
import {
  HomeOutlined,
  SearchOutlined,
  NodeIndexOutlined,
  CheckCircleOutlined,
  MessageOutlined,
  DatabaseOutlined,
} from "@ant-design/icons";
import NotificationBell from "./NotificationBell";

const { Header: AntHeader } = Layout;

const menuKeyMap: Record<string, string> = {
  "/": "home",
  "/search": "search",
  "/verification": "verification",
  "/chat": "chat",
  "/data/pipeline": "pipeline",
};

const HeaderComponent = () => {
  const location = useLocation();

  // 根据路径匹配当前菜单项
  let selectedKey = "home";
  if (location.pathname.startsWith("/graph")) {
    selectedKey = "graph";
  } else {
    selectedKey = menuKeyMap[location.pathname] || "home";
  }

  const menuItems = [
    {
      key: "home",
      icon: <HomeOutlined />,
      label: <Link to="/">首页</Link>,
    },
    {
      key: "search",
      icon: <SearchOutlined />,
      label: <Link to="/search">知识搜索</Link>,
    },
    {
      key: "graph",
      icon: <NodeIndexOutlined />,
      label: <Link to="/graph/人参">图谱浏览</Link>,
    },
    {
      key: "verification",
      icon: <CheckCircleOutlined />,
      label: <Link to="/verification">验证管理</Link>,
    },
    {
      key: "chat",
      icon: <MessageOutlined />,
      label: <Link to="/chat">智能问答</Link>,
    },
    {
      key: "pipeline",
      icon: <DatabaseOutlined />,
      label: <Link to="/data/pipeline">数据处理</Link>,
    },
  ];

  return (
    <AntHeader
      style={{
        position: "fixed",
        top: 0,
        zIndex: 100,
        width: "100%",
        display: "flex",
        alignItems: "center",
        background: "linear-gradient(135deg, #1a3a2a 0%, #2e5a3e 100%)",
        boxShadow: "0 2px 8px rgba(0,0,0,0.15)",
        padding: "0 24px",
      }}
    >
      <Link to="/" style={{ display: "flex", alignItems: "center", textDecoration: "none", marginRight: 40 }}>
        <span style={{ fontSize: 24, marginRight: 8 }}>🌿</span>
        <span
          style={{
            color: "#fff",
            fontSize: 18,
            fontWeight: 600,
            letterSpacing: 1,
          }}
        >
          白草药坛
        </span>
      </Link>
      <Menu
        theme="dark"
        mode="horizontal"
        selectedKeys={[selectedKey]}
        items={menuItems}
        style={{
          flex: 1,
          background: "transparent",
          borderBottom: "none",
          fontSize: 14,
        }}
      />
      <NotificationBell />
    </AntHeader>
  );
};

export default HeaderComponent;
