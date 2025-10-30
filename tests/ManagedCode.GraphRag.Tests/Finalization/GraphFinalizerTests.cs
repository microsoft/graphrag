using GraphRag.Entities;
using GraphRag.Finalization;
using GraphRag.Relationships;

namespace ManagedCode.GraphRag.Tests.Finalization;

public sealed class GraphFinalizerTests
{
    [Fact]
    public void Finalize_ComputesDegreesWithoutLayout()
    {
        var entities = new[]
        {
            new EntitySeed("Alice", "Person", "A", new[] { "unit-1" }, 2),
            new EntitySeed("Bob", "Person", null, new[] { "unit-2" }, 1)
        };

        var relationships = new[]
        {
            new RelationshipSeed("Alice", "Bob", "Friends", 0.5, new[] { "unit-1" })
        };

        var result = GraphFinalizer.Finalize(entities, relationships, new GraphFinalizerOptions(LayoutEnabled: false));

        Assert.Equal(2, result.Entities.Count);
        var alice = result.Entities.Single(e => e.Title == "Alice");
        Assert.Equal(1, alice.Degree);
        Assert.Equal(0d, alice.X);
        Assert.Equal(0d, alice.Y);

        var relationship = Assert.Single(result.Relationships);
        Assert.Equal(2, relationship.CombinedDegree);
    }

    [Fact]
    public void Finalize_ComputesLayoutWhenEnabled()
    {
        var entities = new[]
        {
            new EntitySeed("Alice", "Person", "A", new[] { "unit-1" }, 1),
            new EntitySeed("Bob", "Person", null, new[] { "unit-2" }, 1),
            new EntitySeed("Charlie", "Person", null, new[] { "unit-3" }, 1)
        };

        var result = GraphFinalizer.Finalize(entities, Array.Empty<RelationshipSeed>(), new GraphFinalizerOptions(LayoutEnabled: true));

        Assert.Contains(result.Entities, e => Math.Abs(e.X) > 0.001 || Math.Abs(e.Y) > 0.001);
    }
}
