import { Suspense, lazy } from "react";
import { Routes, Route, useLocation } from "react-router-dom";
import { Layout, Skeleton, Space, Typography } from "antd";
import Header from "./components/Header";
const HomePage = lazy(() => import("./pages/HomePage"));
const SearchPage = lazy(() => import("./pages/SearchPage"));
const GraphPage = lazy(() => import("./pages/GraphPage"));
const GraphWorkbenchPage = lazy(() => import("./pages/GraphWorkbenchPage"));
const VerificationPage = lazy(() => import("./pages/VerificationPage"));
const ChatPage = lazy(() => import("./pages/ChatPage"));
const HerbDetailPage = lazy(() => import("./pages/HerbDetailPage"));

const { Content, Footer } = Layout;
const { Text } = Typography;

const RouteFallback = () => (
  <div
    style={{
      minHeight: "calc(100vh - 180px)",
      display: "grid",
      placeItems: "center",
      padding: "40px 24px",
    }}
  >
    <Space direction="vertical" size={14} align="center" style={{ width: "min(420px, 100%)" }}>
      <Text strong style={{ color: "#203127", fontSize: 16 }}>
        页面加载中...
      </Text>
      <Skeleton active title={{ width: "46%" }} paragraph={{ rows: 4 }} style={{ width: "100%" }} />
    </Space>
  </div>
);

function App() {
  const location = useLocation();
  const isGraphRoute =
    location.pathname === "/graph" || location.pathname.startsWith("/graph/");

  return (
    <Layout style={{ minHeight: "100vh", background: "#f5f7f5" }}>
      <Header />
      <Content
        style={{
          padding: isGraphRoute ? "16px 20px 20px" : "24px 48px",
          marginTop: 56,
        }}
      >
        <div className="site-layout-content page-fade-in">
          <Suspense fallback={<RouteFallback />}>
            <Routes>
              <Route path="/" element={<HomePage />} />
              <Route path="/search" element={<SearchPage />} />
              <Route path="/graph/:name?" element={<GraphPage />} />
              <Route path="/graph/workbench" element={<GraphWorkbenchPage />} />
              <Route path="/verification" element={<VerificationPage />} />
              <Route path="/chat" element={<ChatPage />} />
              <Route path="/herb/:id" element={<HerbDetailPage />} />
            </Routes>
          </Suspense>
        </div>
      </Content>
      <Footer
        style={{
          textAlign: "center",
          background: "transparent",
          color: "#8c8c8c",
          fontSize: 13,
          padding: "16px 50px",
        }}
      >
        白草药坛 ©2026 - 可溯源的中药材知识图谱智能问答系统
      </Footer>
    </Layout>
  );
}

export default App;
