import { Radio, Space, Typography } from "antd";
import type { PipelineSourceType, PipelineUploadResponse } from "../../types/pipeline";

const { Text } = Typography;

interface SourceIngestionFormProps {
  sourceType: PipelineSourceType;
  sourceLocator: string;
  uploadedSource: PipelineUploadResponse | null;
  disabled: boolean;
  onSourceTypeChange: (value: PipelineSourceType) => void;
  onSourceLocatorChange: (value: string) => void;
  onUploadFile: (file: File) => void;
}

const SourceIngestionForm = ({
  sourceType,
  sourceLocator,
  uploadedSource,
  disabled,
  onSourceTypeChange,
  onSourceLocatorChange,
  onUploadFile,
}: SourceIngestionFormProps) => {
  return (
    <Space direction="vertical" size={10} style={{ width: "100%" }}>
      <label htmlFor="pipeline-source-type">来源类型</label>
      <Radio.Group
        id="pipeline-source-type"
        aria-label="来源类型"
        value={sourceType}
        onChange={(event) => onSourceTypeChange(event.target.value as PipelineSourceType)}
        disabled={disabled}
      >
        <Radio.Button value="huggingface_repo">Hugging Face Repo</Radio.Button>
        <Radio.Button value="remote_url">远程直链</Radio.Button>
        <Radio.Button value="local_upload">本地上传</Radio.Button>
      </Radio.Group>

      {sourceType === "huggingface_repo" ? (
        <>
          <label htmlFor="pipeline-repo-id">Repo ID</label>
          <input
            id="pipeline-repo-id"
            aria-label="Repo ID"
            value={sourceLocator}
            disabled={disabled}
            onChange={(event) => onSourceLocatorChange(event.target.value)}
            placeholder="ZJUFanLab/TCMChat-dataset-600k"
            style={{ width: "100%", minHeight: 32, padding: "4px 11px" }}
          />
        </>
      ) : null}

      {sourceType === "remote_url" ? (
        <>
          <label htmlFor="pipeline-remote-url">远程直链</label>
          <input
            id="pipeline-remote-url"
            aria-label="远程直链"
            value={sourceLocator}
            disabled={disabled}
            onChange={(event) => onSourceLocatorChange(event.target.value)}
            placeholder="https://example.com/dataset.zip"
            style={{ width: "100%", minHeight: 32, padding: "4px 11px" }}
          />
        </>
      ) : null}

      {sourceType === "local_upload" ? (
        <Space direction="vertical" size={8} style={{ width: "100%" }}>
          <label htmlFor="pipeline-local-upload">上传文件</label>
          <input
            id="pipeline-local-upload"
            aria-label="上传文件"
            type="file"
            disabled={disabled}
            onChange={(event) => {
              const file = event.target.files?.[0];
              if (file) {
                onUploadFile(file);
              }
            }}
          />
          <Text type="secondary">{uploadedSource ? `已上传：${uploadedSource.filename}` : "支持文件和压缩包"}</Text>
        </Space>
      ) : null}
    </Space>
  );
};

export default SourceIngestionForm;
