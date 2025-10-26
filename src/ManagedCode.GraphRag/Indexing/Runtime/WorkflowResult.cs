namespace GraphRag.Indexing.Runtime;

/// <summary>
/// Represents the value returned by an individual workflow step.
/// </summary>
public sealed record WorkflowResult(object? Result, bool Stop = false);
