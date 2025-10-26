using GraphRag.Config;

namespace GraphRag.Indexing.Runtime;

public delegate ValueTask<WorkflowResult> WorkflowDelegate(
    GraphRagConfig config,
    PipelineRunContext context,
    CancellationToken cancellationToken);
