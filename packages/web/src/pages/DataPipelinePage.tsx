import { useEffect } from "react";
import { useSearchParams } from "react-router-dom";
import PipelineShell from "../components/pipeline/PipelineShell";
import { usePipelineRun } from "../hooks/usePipelineRun";

const DataPipelinePage = () => {
  const [searchParams] = useSearchParams();
  const { restoreRun, run } = usePipelineRun();

  useEffect(() => {
    const runId = searchParams.get("runId");
    if (!runId || run?.id === runId) {
      return;
    }
    void restoreRun(runId);
  }, [restoreRun, run?.id, searchParams]);

  return <PipelineShell />;
};

export default DataPipelinePage;
