using GraphRag.Indexing.Runtime;
using GraphRag.Logging;

namespace GraphRag.Callbacks;

public sealed class NoopWorkflowCallbacks : IWorkflowCallbacks
{
    public static NoopWorkflowCallbacks Instance { get; } = new();

    private NoopWorkflowCallbacks()
    {
    }

    public void PipelineStart(IReadOnlyList<string> names)
    {
    }

    public void PipelineEnd(IReadOnlyList<PipelineRunResult> results)
    {
    }

    public void WorkflowStart(string name, object? instance)
    {
    }

    public void WorkflowEnd(string name, object? instance)
    {
    }

    public void ReportProgress(ProgressSnapshot progress)
    {
    }
}
