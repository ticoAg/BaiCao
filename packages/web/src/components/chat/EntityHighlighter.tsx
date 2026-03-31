// EntityHighlighter - 将纯文本中的实体名高亮为可点击 Tag
import { Tag, Typography } from "antd";
import { useNavigate } from "react-router-dom";
import type { Entity } from "../../types/chat";
import { getGraphNodeTagColor, isHerbGraphLabel } from "../../types/graph";

const { Paragraph } = Typography;

interface Segment {
  text: string;
  isEntity: boolean;
  entity?: Entity;
}

function splitTextByEntities(text: string, entities: Entity[]): Segment[] {
  if (!entities || entities.length === 0) {
    return [{ text, isEntity: false }];
  }

  // 按实体名长度降序排列，优先匹配更长的实体名，避免短名遮盖长名
  const sorted = [...entities].sort((a, b) => b.name.length - a.name.length);

  // 用所有实体名构建正则（转义特殊字符）
  const pattern = sorted
    .map((e) => e.name.replace(/[.*+?^${}()|[\]\\]/g, "\\$&"))
    .join("|");

  if (!pattern) {
    return [{ text, isEntity: false }];
  }

  const regex = new RegExp(`(${pattern})`, "g");
  const parts = text.split(regex);

  // 构建实体名 -> Entity 的快速查找表
  const entityMap = new Map<string, Entity>();
  for (const e of entities) {
    entityMap.set(e.name, e);
  }

  const segments: Segment[] = [];
  for (const part of parts) {
    if (!part) continue;
    const matchedEntity = entityMap.get(part);
    if (matchedEntity) {
      segments.push({ text: part, isEntity: true, entity: matchedEntity });
    } else {
      segments.push({ text: part, isEntity: false });
    }
  }

  return segments;
}

interface EntityHighlighterProps {
  content: string;
  entities?: Entity[];
}

const EntityHighlighter = ({ content, entities }: EntityHighlighterProps) => {
  const navigate = useNavigate();

  const handleEntityClick = (entity: Entity) => {
    if (isHerbGraphLabel(entity.type)) {
      const target = entity.id
        ? `/herb/${encodeURIComponent(entity.id)}`
        : `/herb/${encodeURIComponent(entity.name)}`;
      navigate(target);
    } else {
      navigate(`/graph/${encodeURIComponent(entity.name)}`);
    }
  };

  if (!entities || entities.length === 0) {
    return (
      <Paragraph style={{ margin: 0, whiteSpace: "pre-wrap" }}>
        {content}
      </Paragraph>
    );
  }

  const segments = splitTextByEntities(content, entities);

  return (
    <Paragraph style={{ margin: 0, whiteSpace: "pre-wrap" }}>
      {segments.map((seg, idx) => {
        if (seg.isEntity && seg.entity) {
          const color = getGraphNodeTagColor(seg.entity.type);
          return (
            <Tag
              key={idx}
              color={color}
              style={{ cursor: "pointer", margin: "0 2px" }}
              onClick={() => handleEntityClick(seg.entity!)}
            >
              {seg.text}
            </Tag>
          );
        }
        return <span key={idx}>{seg.text}</span>;
      })}
    </Paragraph>
  );
};

export default EntityHighlighter;
