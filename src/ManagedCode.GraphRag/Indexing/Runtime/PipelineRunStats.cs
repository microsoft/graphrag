namespace GraphRag.Indexing.Runtime;

/// <summary>
/// Captures aggregate statistics for a pipeline run.
/// </summary>
public sealed class PipelineRunStats
{
    private readonly Dictionary<string, Dictionary<string, double>> _workflows = new(StringComparer.OrdinalIgnoreCase);

    public double TotalRuntime { get; set; }

    public int NumDocuments { get; set; }

    public int UpdateDocuments { get; set; }

    public double InputLoadTime { get; set; }

    public IReadOnlyDictionary<string, Dictionary<string, double>> Workflows => _workflows;

    public Dictionary<string, double> GetOrAddWorkflowStats(string workflowName)
    {
        if (!_workflows.TryGetValue(workflowName, out var stats))
        {
            stats = new Dictionary<string, double>(StringComparer.OrdinalIgnoreCase);
            _workflows[workflowName] = stats;
        }

        return stats;
    }
}
