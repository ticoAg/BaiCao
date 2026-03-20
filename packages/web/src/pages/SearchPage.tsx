import { useState } from "react";
import { Input, List, Card, Tag, Spin, Typography, Space, message } from "antd";
import { useNavigate } from "react-router-dom";
import { graphApi, SearchResult } from "../services/api";

const { Title, Text } = Typography;

const labelColors: Record<string, string> = {
  Herb: "blue",
  Efficacy: "green",
  Flavor: "orange",
  Meridian: "purple",
  Disease: "red",
  Component: "cyan",
};

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
    <div>
      <Title level={2}>搜索</Title>

      <Card style={{ marginBottom: 24 }}>
        <Input.Search
          placeholder="输入药材名称搜索..."
          size="large"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onSearch={handleSearch}
          loading={loading}
          enterButton="搜索"
        />
      </Card>

      {loading && (
        <div style={{ textAlign: "center", padding: 24 }}>
          <Space direction="vertical" size="small">
            <Spin />
            <Text type="secondary">搜索中...</Text>
          </Space>
        </div>
      )}

      {searched && !loading && (
        <Card title={`搜索结果 (${results.length})`}>
          {results.length === 0 ? (
            <Text type="secondary">未找到相关结果</Text>
          ) : (
            <List
              dataSource={results}
              renderItem={(item) => (
                <List.Item
                  style={{ cursor: "pointer" }}
                  onClick={() => {
                    if (item.labels?.[0] === "Herb") {
                      navigate(`/graph/${encodeURIComponent(item.node.name)}`);
                    }
                  }}
                >
                  <List.Item.Meta
                    title={
                      <Space>
                        <Text strong>{item.node.name}</Text>
                        <Tag color={labelColors[item.labels?.[0] || ""]}>
                          {item.labels?.[0] || "Unknown"}
                        </Tag>
                        <Tag>
                          {item.node.status === "pending"
                            ? "待验证"
                            : item.node.status === "verified"
                              ? "已验证"
                              : "已拒绝"}
                        </Tag>
                      </Space>
                    }
                    description={item.node.source ? `来源: ${item.node.source}` : undefined}
                  />
                </List.Item>
              )}
            />
          )}
        </Card>
      )}
    </div>
  );
};

export default SearchPage;
