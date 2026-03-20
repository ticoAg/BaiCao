import { Routes, Route } from "react-router-dom";
import { Layout } from "antd";
import Header from "./components/Header";
import HomePage from "./pages/HomePage";
import SearchPage from "./pages/SearchPage";
import GraphPage from "./pages/GraphPage";
import VerificationPage from "./pages/VerificationPage";
import ChatPage from "./pages/ChatPage";

const { Content, Footer } = Layout;

function App() {
  return (
    <Layout className="layout" style={{ minHeight: "100vh" }}>
      <Header />
      <Content style={{ padding: "0 50px", marginTop: 64 }}>
        <div className="site-layout-content" style={{ padding: 24, minHeight: 380 }}>
          <Routes>
            <Route path="/" element={<HomePage />} />
            <Route path="/search" element={<SearchPage />} />
            <Route path="/graph/:name" element={<GraphPage />} />
            <Route path="/verification" element={<VerificationPage />} />
            <Route path="/chat" element={<ChatPage />} />
          </Routes>
        </div>
      </Content>
      <Footer style={{ textAlign: "center" }}>
        白草药坛 ©2026 - 可溯源的中药材知识图谱智能问答系统
      </Footer>
    </Layout>
  );
}

export default App;
