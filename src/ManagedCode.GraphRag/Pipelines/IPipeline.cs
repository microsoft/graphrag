using System.Collections.Generic;
using System.Threading;
using System.Threading.Tasks;

namespace GraphRag.Pipelines;

/// <summary>
/// Represents a unit of work in the GraphRAG indexing or query workflow.
/// </summary>
/// <remarks>
/// The original Python project models pipelines as ordered callables. In C# we expose
/// an asynchronous abstraction that mirrors the same behavior but is friendlier for DI.
/// </remarks>
public interface IPipeline
{
    ValueTask ExecuteAsync(PipelineContext context, CancellationToken cancellationToken = default);
}

/// <summary>
/// Provides ambient state for pipeline execution.
/// </summary>
public sealed record PipelineContext(
    IDictionary<string, object?> Items,
    IServiceProvider Services,
    CancellationToken CancellationToken);
