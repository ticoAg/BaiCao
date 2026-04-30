import { useEffect, useState } from "react";
import {
  Alert,
  Button,
  Divider,
  Form,
  Input,
  InputNumber,
  Select,
  Space,
  Typography,
  message,
} from "../ui/index";
import { SearchOutlined } from "../ui/icons";
import { statusLabels } from "../../types";
import {
  graphPropertyLabels,
  relTypeLabels,
  type GraphEdgeRelType,
  type GraphNodeLabel,
  type GraphQueryPropertyKey,
  type GraphQueryRequest,
} from "../../types/graph";

const { Text } = Typography;

type GraphQueryPanelProps = {
  depth: number;
  loading?: boolean;
  onSubmit: (request: GraphQueryRequest) => void | Promise<unknown>;
  onDepthChange?: (depth: number) => void;
  onReset?: () => void;
};

const nodeLabelOptions: GraphNodeLabel[] = [
  "药材",
  "成分",
  "品种",
  "工艺",
  "性状",
  "功效",
  "性味",
  "归经",
  "病证",
  "时间点",
];

const relationTypeOptions: GraphEdgeRelType[] = [
  "具有饮片",
  "包含成分",
  "提取自",
  "具有品种",
  "属于药材",
  "经过工艺",
  "适用于",
  "储存时间",
  "具有性状",
  "观察于",
  "具有功效",
  "具有性味",
  "归于经脉",
  "治疗病证",
  "相互作用",
  "相似于",
  "父类",
  "子类",
  "来源于",
];

const propertyKeyOptions: GraphQueryPropertyKey[] = [
  "latin_name",
  "category",
  "description",
  "chemical_formula",
  "parent_herb",
  "min_duration",
  "conditions",
  "trait_category",
  "years",
  "quality_indicator",
  "nature",
  "tcm_type",
  "type",
];

const sectionTitleStyle = {
  fontSize: 12,
  fontWeight: 600,
  letterSpacing: "0.08em",
  textTransform: "uppercase" as const,
  color: "#2e7d32",
};

function cleanText(value: unknown) {
  if (typeof value !== "string") {
    return value;
  }

  const trimmed = value.trim();
  return trimmed ? trimmed : undefined;
}

function pruneObject<T extends object>(value: T | undefined) {
  if (!value) {
    return undefined;
  }

  const entries = Object.entries(value as Record<string, unknown>)
    .map(([key, entryValue]) => [key, cleanText(entryValue)] as const)
    .filter(([, entryValue]) => entryValue !== undefined && entryValue !== null);

  return entries.length ? (Object.fromEntries(entries) as T) : undefined;
}

const GraphQueryPanel = ({
  depth,
  loading = false,
  onSubmit,
  onDepthChange,
  onReset,
}: GraphQueryPanelProps) => {
  const [form] = Form.useForm<GraphQueryRequest>();
  const [showDeveloperPreview, setShowDeveloperPreview] = useState(false);

  useEffect(() => {
    form.setFieldValue("depth", depth);
  }, [depth, form]);

  const handleValuesChange = (changedValues: GraphQueryRequest) => {
    if (typeof changedValues.depth === "number") {
      onDepthChange?.(changedValues.depth);
    }
  };

  const handleFinish = async (values: GraphQueryRequest) => {
    const nodeFilters = pruneObject(values.node);
    const edgeFilters = pruneObject(values.edge);

    if (!nodeFilters && !edgeFilters) {
      message.warning("请至少填写一个节点或关系过滤条件");
      return;
    }

    const nextRequest: GraphQueryRequest = {
      node: nodeFilters,
      edge: edgeFilters,
      depth: values.depth ?? depth,
      limit: values.limit,
    };

    await onSubmit(pruneObject(nextRequest) ?? {});
  };

  const handleReset = () => {
    form.resetFields();
    form.setFieldValue("depth", depth);
    onDepthChange?.(depth);
    onReset?.();
  };

  const rawValues = form.getFieldsValue(true);
  const nodeFilters = pruneObject(rawValues.node);
  const edgeFilters = pruneObject(rawValues.edge);
  const payload = {
    node: nodeFilters,
    edge: edgeFilters,
    depth: rawValues.depth,
    limit: rawValues.limit,
  };
  const trimmedPayload = pruneObject(payload);

  return (
    <Form<GraphQueryRequest>
      form={form}
      layout="vertical"
      initialValues={{ depth }}
      onFinish={handleFinish}
      onValuesChange={handleValuesChange}
    >
      <Alert
        type="info"
        showIcon
        message="围绕节点、关系和属性建立组合查询，结果会在中间工作区实时切换为命中子图。"
        style={{
          marginBottom: 20,
          borderRadius: 14,
          border: "none",
          background: "rgba(255, 255, 255, 0.4)",
          backdropFilter: "blur(12px)",
        }}
      />

      <Space direction="vertical" size={18} style={{ width: "100%" }}>
        <div>
          <Text style={sectionTitleStyle}>节点条件</Text>
          <Divider style={{ margin: "10px 0 16px" }} />
          <Form.Item label="节点名称包含" name={["node", "name_contains"]}>
            <Input placeholder="例如：参、补气、炙制" allowClear />
          </Form.Item>
          <Form.Item label="节点类型" name={["node", "label"]}>
            <Select
              allowClear
              placeholder="全部节点类型"
              options={nodeLabelOptions.map((value) => ({ label: value, value }))}
            />
          </Form.Item>
          <Form.Item label="节点状态" name={["node", "status"]}>
            <Select
              allowClear
              placeholder="全部状态"
              options={Object.entries(statusLabels).map(([value, label]) => ({
                label,
                value,
              }))}
            />
          </Form.Item>
          <Form.Item label="来源包含" name={["node", "source_contains"]}>
            <Input placeholder="例如：《本草纲目》、药典、实验记录" allowClear />
          </Form.Item>
          <Form.Item label="属性键" name={["node", "property_key"]}>
            <Select
              allowClear
              placeholder="选择属性键"
              options={propertyKeyOptions.map((value) => ({
                label: graphPropertyLabels[value] || value,
                value,
              }))}
            />
          </Form.Item>
          <Form.Item label="属性值包含" name={["node", "property_value_contains"]}>
            <Input placeholder="例如：温、甘、三年" allowClear />
          </Form.Item>
        </div>

        <div>
          <Text style={sectionTitleStyle}>关系条件</Text>
          <Divider style={{ margin: "10px 0 16px" }} />
          <Form.Item label="关系类型" name={["edge", "rel_type"]}>
            <Select
              allowClear
              placeholder="全部关系类型"
              options={relationTypeOptions.map((value) => ({
                label: relTypeLabels[value] ? `${relTypeLabels[value]} (${value})` : value,
                value,
              }))}
            />
          </Form.Item>
          <Form.Item label="关系状态" name={["edge", "status"]}>
            <Select
              allowClear
              placeholder="全部状态"
              options={Object.entries(statusLabels).map(([value, label]) => ({
                label,
                value,
              }))}
            />
          </Form.Item>
          <Form.Item label="关联节点名称包含" name={["edge", "connected_name_contains"]}>
            <Input placeholder="例如：肺经、补血、黄芪" allowClear />
          </Form.Item>
        </div>

        <div>
          <Text style={sectionTitleStyle}>范围控制</Text>
          <Divider style={{ margin: "10px 0 16px" }} />
          <Form.Item label="查询深度" name="depth">
            <InputNumber min={1} max={3} precision={0} style={{ width: "100%" }} />
          </Form.Item>
          <Form.Item label="limit" name="limit">
            <InputNumber
              min={1}
              max={200}
              precision={0}
              placeholder="后端默认"
              style={{ width: "100%" }}
            />
          </Form.Item>
        </div>
      </Space>

      <Space style={{ width: "100%", marginTop: 20 }} size={12}>
        <Button onClick={handleReset} style={{ flex: 1, borderRadius: 14 }}>
          重置条件
        </Button>
        <Button
          type="text"
          onClick={() => setShowDeveloperPreview((value) => !value)}
          style={{ paddingInline: 0 }}
        >
          开发者预览
        </Button>
      </Space>

      {showDeveloperPreview ? (
        <div
          style={{
            marginTop: 16,
            padding: 12,
            borderRadius: 12,
            background: "rgba(255, 255, 255, 0.5)",
            border: "1px dashed rgba(46, 125, 50, 0.2)",
            fontFamily: "monospace",
            fontSize: 12,
          }}
        >
          <Text style={{ ...sectionTitleStyle, fontSize: 11, marginBottom: 8, display: "block" }}>
            实时请求预览 (JSON payload)
          </Text>
          <pre style={{ margin: 0, color: "#3D5A48", whiteSpace: "pre-wrap", wordBreak: "break-word" }}>
            {trimmedPayload && Object.keys(trimmedPayload).length > 0
              ? JSON.stringify(trimmedPayload, null, 2)
              : "{\n  // 请输入查询条件\n}"}
          </pre>
        </div>
      ) : null}

      <Button
        type="primary"
        htmlType="submit"
        icon={<SearchOutlined />}
        loading={loading}
        block
        style={{
          marginTop: 20,
          height: 42,
          borderRadius: 14,
          background: "linear-gradient(135deg, #456B57 0%, #2F5A46 100%)",
          boxShadow: "0 12px 28px rgba(47, 90, 70, 0.22)",
        }}
      >
        执行图谱查询
      </Button>
    </Form>
  );
};

export default GraphQueryPanel;
