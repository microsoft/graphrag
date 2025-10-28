using GraphRag.Indexing.Runtime;
using GraphRag.Logging;

namespace GraphRag.Callbacks;

public interface IWorkflowCallbacks
{
    void PipelineStart(IReadOnlyList<string> names);

    void PipelineEnd(IReadOnlyList<PipelineRunResult> results);

    void WorkflowStart(string name, object? instance);

    void WorkflowEnd(string name, object? instance);

    void ReportProgress(ProgressSnapshot progress);
}
