import { useState } from "react";
import { Input, List, Card, Tag, Spin, Typography, Space, message } from "../components/ui/index";
import { useNavigate } from "react-router-dom";
import { SearchOutlined } from "../components/ui/icons";
import { graphApi, SearchResult } from "../services/api";
import { getGraphNodeLabelDisplayName, getGraphNodeTagColor, isHerbGraphLabel } from "../types/graph";

const { Title, Text, Paragraph } = Typography;

const hotSearches = ["甘草", "人参", "黄芪", "陈皮", "当归", "枸杞"];

const SearchPage = () => {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<SearchResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [searched, setSearched] = useState(false);
  const navigate = useNavigate();

  const handleSearch = async (value: string) => {
    if (!value.trim()) return;

    setLoading(true);
    setSearched(true);
    try {
      const data = await graphApi.search(value);
      setResults(data);
    } catch {
      message.error("搜索失败");
      setResults([]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ maxWidth: 900, margin: "0 auto" }}>
      {/* 搜索区域 */}
      <div
        style={{
          textAlign: "center",
          padding: searched ? "24px 0 20px" : "60px 0 40px",
          transition: "padding 0.3s ease",
        }}
      >
        {!searched && (
          <>
            <SearchOutlined
              style={{ fontSize: 40, color: "#2e7d32", marginBottom: 12 }}
            />
            <Title level={2} style={{ marginBottom: 8, color: "#1a3a2a" }}>
              知识搜索
            </Title>
            <Paragraph
              type="secondary"
              style={{ marginBottom: 24, fontSize: 15 }}
            >
              搜索药材、功效、归经、成分等中药材知识
            </Paragraph>
          </>
        )}

        <div style={{ maxWidth: 640, margin: "0 auto" }}>
          <Input.Search
            placeholder="输入药材名称搜索，如：甘草、人参、黄芪..."
            size="large"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onSearch={handleSearch}
            loading={loading}
            enterButton="搜索"
            style={{
              boxShadow: "0 2px 8px rgba(0,0,0,0.08)",
              borderRadius: 8,
            }}
          />
        </div>

        {/* 热门搜索 */}
        {!searched && (
          <div style={{ marginTop: 16 }}>
            <Text type="secondary" style={{ fontSize: 13, marginRight: 8 }}>
              热门搜索：
            </Text>
            {hotSearches.map((term) => (
              <Tag
                key={term}
                style={{
                  cursor: "pointer",
                  marginBottom: 4,
                  borderRadius: 12,
                  padding: "2px 12px",
                }}
                onClick={() => {
                  setQuery(term);
                  void handleSearch(term);
                }}
              >
                {term}
              </Tag>
            ))}
          </div>
        )}
      </div>

      {/* 加载状态 */}
      {loading && (
        <div style={{ textAlign: "center", padding: 40 }}>
          <Space direction="vertical" size="small">
            <Spin />
            <Text type="secondary">搜索中...</Text>
          </Space>
        </div>
      )}

      {/* 搜索结果 */}
      {searched && !loading && (
        <Card
          title={
            <Space>
              <Text strong>搜索结果</Text>
              <Tag color="green">{results.length} 条</Tag>
            </Space>
          }
          style={{
            borderRadius: 12,
            border: "none",
            boxShadow: "0 1px 4px rgba(0,0,0,0.06)",
          }}
        >
          {results.length === 0 ? (
            <div style={{ textAlign: "center", padding: "32px 0" }}>
              <Text type="secondary" style={{ fontSize: 15 }}>
                未找到"{query}"相关结果，试试其他关键词？
              </Text>
              <div style={{ marginTop: 16 }}>
                {hotSearches.slice(0, 3).map((term) => (
                  <Tag
                    key={term}
                    color="green"
                    style={{ cursor: "pointer", borderRadius: 12 }}
                    onClick={() => {
                      setQuery(term);
                      void handleSearch(term);
                    }}
                  >
                    {term}
                  </Tag>
                ))}
              </div>
            </div>
          ) : (
            <List
              dataSource={results}
              renderItem={(item) => {
                const primaryLabel = item.labels?.[0] || "Unknown";
                const isClickable = isHerbGraphLabel(primaryLabel);
                return (
                  <List.Item
                    style={{
                      cursor: isClickable ? "pointer" : "default",
                      borderRadius: 8,
                      padding: "12px 16px",
                      marginBottom: 4,
                      transition: "background 0.2s",
                    }}
                    onClick={() => {
                      if (isClickable) {
                        navigate(
                          `/graph/${encodeURIComponent(item.node.name)}`
                        );
                      }
                    }}
                  >
                    <List.Item.Meta
                      title={
                        <Space>
                          <Text strong style={{ fontSize: 15 }}>
                            {item.node.name}
                          </Text>
                          <Tag color={getGraphNodeTagColor(primaryLabel)}>
                            {getGraphNodeLabelDisplayName(primaryLabel)}
                          </Tag>
                          <Tag
                            color={
                              item.node.status === "verified"
                                ? "green"
                                : item.node.status === "rejected"
                                  ? "red"
                                  : "gold"
                            }
                          >
                            {item.node.status === "pending"
                              ? "待验证"
                              : item.node.status === "verified"
                                ? "已验证"
                                : "已拒绝"}
                          </Tag>
                        </Space>
                      }
                      description={
                        <Space>
                          {item.node.source && (
                            <Text type="secondary" style={{ fontSize: 12 }}>
                              来源: {item.node.source}
                            </Text>
                          )}
                          {isClickable && (
                            <Text
                              type="secondary"
                              style={{ fontSize: 12, color: "#2e7d32" }}
                            >
                              点击查看图谱 →
                            </Text>
                          )}
                        </Space>
                      }
                    />
                  </List.Item>
                );
              }}
            />
          )}
        </Card>
      )}
    </div>
  );
};

export default SearchPage;
