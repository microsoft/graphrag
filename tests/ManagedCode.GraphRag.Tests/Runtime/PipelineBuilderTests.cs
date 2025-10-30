using GraphRag.Indexing.Runtime;

namespace ManagedCode.GraphRag.Tests.Runtime;

public sealed class PipelineBuilderTests
{
    private static readonly WorkflowDelegate Noop = (config, context, token) => ValueTask.FromResult(new WorkflowResult(null));

    [Fact]
    public void Build_CreatesPipelineWithNamedSteps()
    {
        var pipeline = new PipelineBuilder()
            .Named("demo")
            .Step("step1", Noop)
            .Step("step2", Noop)
            .Build();

        Assert.Equal("demo", pipeline.Name);
        Assert.Equal(new[] { "step1", "step2" }, pipeline.Names);
    }

    [Fact]
    public void Remove_EliminatesMatchingSteps()
    {
        var pipeline = new PipelineBuilder()
            .Step("alpha", Noop)
            .Step("beta", Noop)
            .Build();

        pipeline.Remove("alpha");

        Assert.DoesNotContain("alpha", pipeline.Names);
        Assert.Contains("beta", pipeline.Names);
    }
}
