namespace GraphRag.Indexing.Runtime;

/// <summary>
/// Represents the outcome of executing a single workflow within the pipeline.
/// </summary>
public sealed record PipelineRunResult(
    string Workflow,
    object? Result,
    PipelineState State,
    IReadOnlyList<Exception>? Errors);
