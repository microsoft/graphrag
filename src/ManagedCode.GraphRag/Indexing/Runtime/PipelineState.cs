using System.Collections.Generic;

namespace GraphRag.Indexing.Runtime;

/// <summary>
/// Mutable property bag shared across pipeline workflows.
/// </summary>
public sealed class PipelineState : Dictionary<string, object?>
{
    public PipelineState()
        : base(System.StringComparer.OrdinalIgnoreCase)
    {
    }

    public PipelineState(IDictionary<string, object?> values)
        : base(values, System.StringComparer.OrdinalIgnoreCase)
    {
    }
}
