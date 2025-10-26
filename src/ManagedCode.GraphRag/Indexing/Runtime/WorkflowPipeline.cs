using System;
using System.Collections.Generic;
using System.Linq;

namespace GraphRag.Indexing.Runtime;

public sealed class WorkflowPipeline
{
    private readonly List<WorkflowStep> _steps;

    public WorkflowPipeline(string name, IEnumerable<WorkflowStep> steps)
    {
        Name = name ?? throw new ArgumentNullException(nameof(name));
        _steps = steps?.ToList() ?? throw new ArgumentNullException(nameof(steps));
    }

    public string Name { get; }

    public IReadOnlyList<WorkflowStep> Steps => _steps;

    public IReadOnlyList<string> Names => _steps.Select(step => step.Name).ToArray();

    public void Remove(string name)
    {
        ArgumentException.ThrowIfNullOrWhiteSpace(name);
        _steps.RemoveAll(step => string.Equals(step.Name, name, StringComparison.OrdinalIgnoreCase));
    }
}

public sealed record WorkflowStep(string Name, WorkflowDelegate Delegate);
