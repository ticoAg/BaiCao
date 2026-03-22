import { screen, waitFor } from "@testing-library/react";
import HerbDetailPage from "./HerbDetailPage";
import { renderWithProviders } from "../test/render-with-providers";
import { herbApi, provenanceApi } from "../services/api";

const mockHerb = {
  id: "herb-001",
  name: "人参",
  latin_name: "Panax ginseng",
  category: "补气药",
  description: "大补元气，复脉固脱，补脾益肺，生津养血，安神益智。",
  alias: ["棒槌", "园参"],
  efficacy: ["大补元气", "复脉固脱", "补脾益肺"],
  flavor: ["甘", "微苦"],
  meridian: ["脾经", "肺经", "心经"],
  dosage: "3-9g，另煎兑服",
  contraindications: "实证、热证而正气不虚者忌用",
  created_at: "2026-01-01T00:00:00Z",
  updated_at: "2026-01-01T00:00:00Z",
};

const mockEvidence = {
  evidence: [
    {
      id: "ev-001",
      content: "人参味甘微苦，归脾、肺、心经",
      source_name: "中国药典（2020年版）",
      page_reference: "p.8",
      status: "verified",
    },
  ],
  count: 1,
};

describe("HerbDetailPage", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it("renders herb detail with all sections", async () => {
    vi.spyOn(herbApi, "get").mockResolvedValue(mockHerb);
    vi.spyOn(provenanceApi, "getEntityEvidence").mockResolvedValue(mockEvidence);

    renderWithProviders(<HerbDetailPage />, "/herb/herb-001");

    // Wait for data to load and render
    expect(await screen.findByText("人参")).toBeInTheDocument();
    expect(screen.getByText("补气药")).toBeInTheDocument();
    expect(screen.getByText("Panax ginseng")).toBeInTheDocument();

    // Check sections exist
    expect(screen.getByText("基本信息")).toBeInTheDocument();
    expect(screen.getByText("功效")).toBeInTheDocument();
    expect(screen.getByText("性味归经")).toBeInTheDocument();
    expect(screen.getByText("用法用量")).toBeInTheDocument();
    expect(screen.getByText("禁忌")).toBeInTheDocument();
    expect(screen.getByText(/关联证据/)).toBeInTheDocument();

    // Check content
    expect(screen.getByText("大补元气")).toBeInTheDocument();
    expect(screen.getByText("3-9g，另煎兑服")).toBeInTheDocument();
    expect(screen.getByText(/实证、热证/)).toBeInTheDocument();

    // Check evidence
    expect(screen.getByText("中国药典（2020年版）")).toBeInTheDocument();
  });

  it("renders loading skeleton initially", () => {
    vi.spyOn(herbApi, "get").mockReturnValue(new Promise(() => {}));
    vi.spyOn(provenanceApi, "getEntityEvidence").mockReturnValue(new Promise(() => {}));

    const { container } = renderWithProviders(<HerbDetailPage />, "/herb/herb-001");

    // Skeleton should be rendered
    const skeletons = container.querySelectorAll(".ant-skeleton");
    expect(skeletons.length).toBeGreaterThan(0);
  });

  it("renders error state when API fails", async () => {
    vi.spyOn(herbApi, "get").mockRejectedValue(new Error("Not found"));
    vi.spyOn(provenanceApi, "getEntityEvidence").mockResolvedValue({ evidence: [], count: 0 });

    renderWithProviders(<HerbDetailPage />, "/herb/invalid-id");

    expect(await screen.findByText("无法加载药材信息")).toBeInTheDocument();
  });

  it("calls herbApi.get with correct id", async () => {
    const getSpy = vi.spyOn(herbApi, "get").mockResolvedValue(mockHerb);
    vi.spyOn(provenanceApi, "getEntityEvidence").mockResolvedValue(mockEvidence);

    renderWithProviders(<HerbDetailPage />, "/herb/herb-001");

    await waitFor(() => {
      expect(getSpy).toHaveBeenCalledWith("herb-001");
    });
  });

  it("calls provenanceApi.getEntityEvidence with correct id", async () => {
    vi.spyOn(herbApi, "get").mockResolvedValue(mockHerb);
    const evidenceSpy = vi.spyOn(provenanceApi, "getEntityEvidence").mockResolvedValue(mockEvidence);

    renderWithProviders(<HerbDetailPage />, "/herb/herb-001");

    await waitFor(() => {
      expect(evidenceSpy).toHaveBeenCalledWith("herb-001");
    });
  });

  it("renders empty state for missing optional fields", async () => {
    const minimalHerb = {
      id: "herb-002",
      name: "甘草",
      category: "补气药",
    };
    vi.spyOn(herbApi, "get").mockResolvedValue(minimalHerb);
    vi.spyOn(provenanceApi, "getEntityEvidence").mockResolvedValue({ evidence: [], count: 0 });

    renderWithProviders(<HerbDetailPage />, "/herb/herb-002");

    expect(await screen.findByText("甘草")).toBeInTheDocument();
    // Should have empty states for missing fields
    const emptyTexts = await screen.findAllByText(/暂无/);
    expect(emptyTexts.length).toBeGreaterThan(0);
  });
});
