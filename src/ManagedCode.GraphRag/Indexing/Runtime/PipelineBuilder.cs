using System;
using System.Collections.Generic;

namespace GraphRag.Indexing.Runtime;

/// <summary>
/// Lightweight pipeline builder inspired by the Python workflow factory.
/// </summary>
public sealed class PipelineBuilder
{
    private readonly IList<WorkflowStep> _steps = new List<WorkflowStep>();
    private string _name = "pipeline";

    public PipelineBuilder Named(string name)
    {
        _name = name;
        return this;
    }

    public PipelineBuilder Step(string name, WorkflowDelegate workflow)
    {
        ArgumentException.ThrowIfNullOrWhiteSpace(name);
        ArgumentNullException.ThrowIfNull(workflow);
        _steps.Add(new WorkflowStep(name, workflow));
        return this;
    }

    public WorkflowPipeline Build()
    {
        return new WorkflowPipeline(_name, _steps);
    }
}
