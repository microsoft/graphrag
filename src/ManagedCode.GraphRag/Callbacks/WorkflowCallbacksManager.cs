using GraphRag.Indexing.Runtime;
using GraphRag.Logging;

namespace GraphRag.Callbacks;

public sealed class WorkflowCallbacksManager : IWorkflowCallbacks
{
    private readonly List<IWorkflowCallbacks> _callbacks = new();

    public void Register(IWorkflowCallbacks callbacks)
    {
        ArgumentNullException.ThrowIfNull(callbacks);
        _callbacks.Add(callbacks);
    }

    public void PipelineStart(IReadOnlyList<string> names)
    {
        foreach (var callback in _callbacks)
        {
            callback.PipelineStart(names);
        }
    }

    public void PipelineEnd(IReadOnlyList<PipelineRunResult> results)
    {
        foreach (var callback in _callbacks)
        {
            callback.PipelineEnd(results);
        }
    }

    public void WorkflowStart(string name, object? instance)
    {
        foreach (var callback in _callbacks)
        {
            callback.WorkflowStart(name, instance);
        }
    }

    public void WorkflowEnd(string name, object? instance)
    {
        foreach (var callback in _callbacks)
        {
            callback.WorkflowEnd(name, instance);
        }
    }

    public void ReportProgress(ProgressSnapshot progress)
    {
        foreach (var callback in _callbacks)
        {
            callback.ReportProgress(progress);
        }
    }
}
