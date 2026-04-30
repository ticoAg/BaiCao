import { Link, useLocation } from "react-router-dom";
import { Layout } from "./ui/index";
import { NavigationMenu } from "radix-ui";
import {
  HomeOutlined,
  SearchOutlined,
  NodeIndexOutlined,
  CheckCircleOutlined,
  MessageOutlined,
  DatabaseOutlined,
} from "./ui/icons";
import NotificationBell from "./NotificationBell";

const { Header: AntHeader } = Layout;

const navItems = [
  {
    key: "home",
    path: "/",
    icon: <HomeOutlined />,
    label: "首页",
  },
  {
    key: "search",
    path: "/search",
    icon: <SearchOutlined />,
    label: "知识搜索",
  },
  {
    key: "graph",
    path: "/graph/人参",
    icon: <NodeIndexOutlined />,
    label: "图谱浏览",
  },
  {
    key: "verification",
    path: "/verification",
    icon: <CheckCircleOutlined />,
    label: "验证管理",
  },
  {
    key: "chat",
    path: "/chat",
    icon: <MessageOutlined />,
    label: "智能问答",
  },
  {
    key: "pipeline",
    path: "/data/pipeline",
    icon: <DatabaseOutlined />,
    label: "数据处理",
  },
];

const HeaderComponent = () => {
  const location = useLocation();

  const selectedKey = location.pathname.startsWith("/graph")
    ? "graph"
    : navItems.find((item) => item.path === location.pathname)?.key ?? "home";

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
      <Link to="/" className="site-brand">
        <span className="site-brand-mark">🌿</span>
        <span className="site-brand-text">白草药坛</span>
      </Link>
      <NavigationMenu.Root className="site-header-nav" value={selectedKey}>
        <NavigationMenu.List className="site-header-nav-list">
          {navItems.map((item) => {
            const active = selectedKey === item.key;

            return (
              <NavigationMenu.Item key={item.key} value={item.key}>
                <NavigationMenu.Link asChild active={active}>
                  <Link
                    to={item.path}
                    className="site-header-nav-link"
                    data-active={active}
                    aria-current={active ? "page" : undefined}
                  >
                    <span aria-hidden="true">{item.icon}</span>
                    <span>{item.label}</span>
                  </Link>
                </NavigationMenu.Link>
              </NavigationMenu.Item>
            );
          })}
        </NavigationMenu.List>
      </NavigationMenu.Root>
      <NotificationBell />
    </AntHeader>
  );
};

export default HeaderComponent;
