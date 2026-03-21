import { Route, Routes } from "react-router-dom";
import GraphPage from "./GraphPage";
import { renderWithProviders } from "../test/render-with-providers";
import { nodeStyleMap } from "../types/graph";

type MockNetworkGraphProps = {
  data: {
    nodes: Array<{ id: string; style: { labelFill: string } }>;
  };
};

const mockNetworkGraph = vi.fn((props?: unknown) => (
  <div data-testid="network-graph" data-props={props ? "captured" : "missing"} />
));
const mockUseGraph = vi.fn();
const mockUseGraphWorkspace = vi.fn();

vi.mock("@ant-design/graphs", () => ({
  NetworkGraph: (props: unknown) => mockNetworkGraph(props),
}));

vi.mock("../hooks/useGraph", () => ({
  useGraph: (...args: unknown[]) => mockUseGraph(...args),
}));

vi.mock("../hooks/useGraphWorkspace", () => ({
  useGraphWorkspace: (...args: unknown[]) => mockUseGraphWorkspace(...args),
}));

const createWorkspaceResult = (overrides?: Record<string, unknown>) => ({
  graphData: {
    center: {
      id: "herb-1",
      name: "人参",
      labels: ["Herb"],
      status: "verified",
    },
    nodes: [
      {
        id: "herb-1",
        name: "人参",
        labels: ["Herb"],
        status: "verified",
      },
      {
        id: "efficacy-1",
        name: "大补元气",
        labels: ["Efficacy"],
        status: "verified",
      },
    ],
    edges: [],
  },
  querySummary: null,
  mode: "herb" as const,
  loading: false,
  selected: null,
  setSelected: vi.fn(),
  depth: 1,
  setDepth: vi.fn(),
  refetch: vi.fn(),
  runAdvancedQuery: vi.fn(),
  ...overrides,
});

describe("GraphPage", () => {
  beforeEach(() => {
    mockNetworkGraph.mockClear();
    mockUseGraph.mockReset();
    mockUseGraphWorkspace.mockReset();
    mockUseGraph.mockReturnValue(createWorkspaceResult());
    mockUseGraphWorkspace.mockReturnValue(createWorkspaceResult());
  });

  it("uses nodeStyleMap text colors for graph labels", () => {
    mockUseGraphWorkspace.mockReturnValue(createWorkspaceResult());

    renderWithProviders(
      <Routes>
        <Route path="/graph/:name?" element={<GraphPage />} />
      </Routes>,
      "/graph/人参",
    );

    const [graphProps] =
      mockNetworkGraph.mock.calls[mockNetworkGraph.mock.calls.length - 1] ?? [];
    const typedGraphProps = graphProps as MockNetworkGraphProps;
    const centerNode = typedGraphProps.data.nodes.find((node) => node.id === "herb-1");
    const efficacyNode = typedGraphProps.data.nodes.find(
      (node) => node.id === "efficacy-1",
    );

    expect(centerNode).toBeDefined();
    expect(efficacyNode).toBeDefined();

    if (!centerNode || !efficacyNode) {
      throw new Error("Expected graph nodes to be present in NetworkGraph props");
    }

    expect(centerNode.style.labelFill).toBe(nodeStyleMap.Herb.textColor);
    expect(efficacyNode.style.labelFill).toBe(nodeStyleMap.Efficacy.textColor);
    expect(mockUseGraphWorkspace).toHaveBeenCalledWith("人参");
    expect(mockUseGraph).not.toHaveBeenCalled();
  });

  it("renders on /graph without a name param and calls the workspace hook", () => {
    mockUseGraphWorkspace.mockReturnValue(
      createWorkspaceResult({
        graphData: null,
        selected: null,
      }),
    );

    renderWithProviders(
      <Routes>
        <Route path="/graph/:name?" element={<GraphPage />} />
      </Routes>,
      "/graph",
    );

    expect(mockUseGraphWorkspace).toHaveBeenCalledWith(undefined);
    expect(mockUseGraph).not.toHaveBeenCalled();
  });
});
