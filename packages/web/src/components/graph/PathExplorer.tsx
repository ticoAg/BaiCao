import { useState } from "react";
import {
  Alert,
  AutoComplete,
  Button,
  Divider,
  Space,
  Steps,
  Tag,
  Typography,
  message,
} from "../ui/index";
import { BranchesOutlined } from "../ui/icons";
import { graphApi } from "../../services/api";
import { relTypeLabels } from "../../types/graph";
import type { PathItem, SearchResult } from "../../types/graph";

const { Text } = Typography;

// 最多展示前 5 条路径
const MAX_DISPLAY_PATHS = 5;

type PathExplorerProps = {
  loading?: boolean;
};

// 从路径节点列表中提取展示步骤
// 后端返回的 path 数组是 Neo4j Path 序列化后的节点+关系元素混排，
// 奇数索引为关系，偶数索引为节点（0, 2, 4...），当长度不足时降级为纯节点展示。
function extractSteps(pathItem: PathItem): { node: string; rel?: string }[] {
  const elems = pathItem.path;
  if (!elems || elems.length === 0) return [];

  const steps: { node: string; rel?: string }[] = [];

  for (let i = 0; i < elems.length; i++) {
    const elem = elems[i];
    const name = typeof elem["name"] === "string" ? elem["name"] : String(elem["name"] ?? "?");
    const relType = typeof elem["rel_type"] === "string" ? elem["rel_type"] : undefined;
    const elemType = typeof elem["type"] === "string" ? elem["type"] : undefined;

    // 若元素有 rel_type 或 type 字段且无 name，视为关系元素；否则视为节点
    if (!elem["name"] && (relType || elemType)) {
      // 关系元素：更新上一个步骤的 rel 标注
      if (steps.length > 0) {
        steps[steps.length - 1].rel = relType || elemType;
      }
    } else {
      steps.push({ node: name, rel: undefined });
    }
  }

  return steps;
}

const PathExplorer = ({ loading: externalLoading }: PathExplorerProps) => {
  const [fromName, setFromName] = useState("");
  const [toName, setToName] = useState("");
  const [fromOptions, setFromOptions] = useState<{ value: string; label: string }[]>([]);
  const [toOptions, setToOptions] = useState<{ value: string; label: string }[]>([]);
  const [paths, setPaths] = useState<PathItem[]>([]);
  const [searching, setSearching] = useState(false);
  const [searched, setSearched] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const loading = externalLoading || searching;

  const buildOptions = (results: SearchResult[]) =>
    results.map((r) => ({ value: r.node.name, label: r.node.name }));

  const handleNodeSearch = async (
    q: string,
    setOptions: (opts: { value: string; label: string }[]) => void,
  ) => {
    if (!q || q.length < 1) {
      setOptions([]);
      return;
    }
    try {
      const results = await graphApi.search(q, undefined, 10);
      setOptions(buildOptions(results));
    } catch {
      setOptions([]);
    }
  };

  const handleFromSearch = (q: string) => handleNodeSearch(q, setFromOptions);
  const handleToSearch = (q: string) => handleNodeSearch(q, setToOptions);

  const handleFindPath = async () => {
    if (!fromName.trim() || !toName.trim()) {
      message.warning("请输入起点和终点节点名称");
      return;
    }
    if (fromName.trim() === toName.trim()) {
      message.warning("起点和终点不能相同");
      return;
    }

    setSearching(true);
    setErrorMsg(null);
    setPaths([]);
    setSearched(false);

    try {
      const result = await graphApi.getPath(fromName.trim(), toName.trim());
      setSearched(true);
      if (!result.paths || result.paths.length === 0) {
        setErrorMsg(`未找到从「${fromName}」到「${toName}」的路径，请尝试增大探索深度或检查名称。`);
        setPaths([]);
      } else {
        setPaths(result.paths.slice(0, MAX_DISPLAY_PATHS));
      }
    } catch (err: unknown) {
      setSearched(true);
      const errMessage = err instanceof Error ? err.message : "请求失败";
      setErrorMsg(`查询失败：${errMessage}`);
    } finally {
      setSearching(false);
    }
  };

  return (
    <div>
      <Space direction="vertical" size={12} style={{ width: "100%" }}>
        <div>
          <Text style={{ fontSize: 12, color: "#5F6B62" }}>起点节点</Text>
          <AutoComplete
            value={fromName}
            options={fromOptions}
            onSearch={handleFromSearch}
            onChange={setFromName}
            onSelect={setFromName}
            placeholder="输入起点名称搜索"
            style={{ width: "100%", marginTop: 4 }}
            allowClear
          />
        </div>

        <div>
          <Text style={{ fontSize: 12, color: "#5F6B62" }}>终点节点</Text>
          <AutoComplete
            value={toName}
            options={toOptions}
            onSearch={handleToSearch}
            onChange={setToName}
            onSelect={setToName}
            placeholder="输入终点名称搜索"
            style={{ width: "100%", marginTop: 4 }}
            allowClear
          />
        </div>

        <Button
          type="primary"
          icon={<BranchesOutlined />}
          loading={loading}
          onClick={handleFindPath}
          block
          style={{
            height: 38,
            borderRadius: 12,
            background: "linear-gradient(135deg, #456B57 0%, #2F5A46 100%)",
            boxShadow: "0 8px 20px rgba(47, 90, 70, 0.18)",
          }}
        >
          查找路径
        </Button>
      </Space>

      {searched && errorMsg && (
        <Alert
          type="warning"
          showIcon
          message={errorMsg}
          style={{ marginTop: 14, borderRadius: 10 }}
        />
      )}

      {paths.length > 0 && (
        <div style={{ marginTop: 14 }}>
          <Text type="secondary" style={{ fontSize: 12 }}>
            找到 {paths.length} 条路径{paths.length >= MAX_DISPLAY_PATHS ? "（显示前 5 条）" : ""}
          </Text>
          {paths.map((pathItem, pathIdx) => {
            const steps = extractSteps(pathItem);
            return (
              <div
                key={pathIdx}
                style={{
                  marginTop: 10,
                  padding: "12px 14px",
                  borderRadius: 12,
                  background: "rgba(246,250,247,0.96)",
                  border: "1px solid rgba(78,97,84,0.12)",
                }}
              >
                <Text
                  strong
                  style={{ fontSize: 12, color: "#456B57", display: "block", marginBottom: 8 }}
                >
                  路径 {pathIdx + 1}
                </Text>
                {steps.length > 0 ? (
                  <Steps
                    direction="vertical"
                    size="small"
                    style={{ marginLeft: -8 }}
                    items={steps.map((step, stepIdx) => ({
                      title: (
                        <Text style={{ fontSize: 13, fontWeight: 500 }}>{step.node}</Text>
                      ),
                      description:
                        step.rel ? (
                          <Tag
                            color="green"
                            style={{ marginTop: 2, fontSize: 11, borderRadius: 6 }}
                          >
                            {relTypeLabels[step.rel] ?? step.rel}
                          </Tag>
                        ) : stepIdx < steps.length - 1 ? (
                          <Tag
                            color="default"
                            style={{ marginTop: 2, fontSize: 11, borderRadius: 6 }}
                          >
                            关联
                          </Tag>
                        ) : null,
                      status: "finish" as const,
                    }))}
                  />
                ) : (
                  <Text type="secondary" style={{ fontSize: 12 }}>
                    路径数据格式暂不支持展示
                  </Text>
                )}
              </div>
            );
          })}
        </div>
      )}

      {!searched && !loading && (
        <div style={{ marginTop: 10 }}>
          <Divider style={{ margin: "8px 0" }} />
          <Text type="secondary" style={{ fontSize: 12, lineHeight: 1.6, display: "block" }}>
            输入两个节点名称，探索它们之间的知识图谱关系路径。
          </Text>
        </div>
      )}
    </div>
  );
};

export default PathExplorer;
