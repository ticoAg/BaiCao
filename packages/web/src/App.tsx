import { Routes, Route, useLocation } from "react-router-dom";
import { Layout } from "antd";
import Header from "./components/Header";
import HomePage from "./pages/HomePage";
import SearchPage from "./pages/SearchPage";
import GraphPage from "./pages/GraphPage";
import VerificationPage from "./pages/VerificationPage";
import ChatPage from "./pages/ChatPage";
import HerbDetailPage from "./pages/HerbDetailPage";

const { Content, Footer } = Layout;

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
          <Routes>
            <Route path="/" element={<HomePage />} />
            <Route path="/search" element={<SearchPage />} />
            <Route path="/graph/:name?" element={<GraphPage />} />
            <Route path="/verification" element={<VerificationPage />} />
            <Route path="/chat" element={<ChatPage />} />
            <Route path="/herb/:id" element={<HerbDetailPage />} />
          </Routes>
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
