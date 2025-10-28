namespace GraphRag.Indexing.Runtime;

public sealed class WorkflowPipeline(string name, IEnumerable<WorkflowStep> steps)
{
    private readonly List<WorkflowStep> _steps = steps?.ToList() ?? throw new ArgumentNullException(nameof(steps));

    public string Name { get; } = name ?? throw new ArgumentNullException(nameof(name));

    public IReadOnlyList<WorkflowStep> Steps => _steps;

    public IReadOnlyList<string> Names => _steps.Select(step => step.Name).ToArray();

    public void Remove(string name)
    {
        ArgumentException.ThrowIfNullOrWhiteSpace(name);
        _steps.RemoveAll(step => string.Equals(step.Name, name, StringComparison.OrdinalIgnoreCase));
    }
}

public sealed record WorkflowStep(string Name, WorkflowDelegate Delegate);
