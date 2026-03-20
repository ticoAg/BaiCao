import { Link } from "react-router-dom";
import { Layout, Menu } from "antd";
import {
  HomeOutlined,
  SearchOutlined,
  NodeIndexOutlined,
  CheckCircleOutlined,
  MessageOutlined,
} from "@ant-design/icons";

const { Header: AntHeader } = Layout;

const HeaderComponent = () => {
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
  ];

  return (
    <AntHeader
      style={{
        position: "fixed",
        top: 0,
        zIndex: 1,
        width: "100%",
        display: "flex",
        alignItems: "center",
      }}
    >
      <div style={{ color: "white", fontSize: 20, fontWeight: "bold", marginRight: 48 }}>
        🌿 白草药坛
      </div>
      <Menu
        theme="dark"
        mode="horizontal"
        defaultSelectedKeys={["home"]}
        items={menuItems}
        style={{ flex: 1 }}
      />
    </AntHeader>
  );
};

export default HeaderComponent;
