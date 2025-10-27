using System;
using System.Linq;
using GraphRag.Entities;
using GraphRag.Finalization;
using GraphRag.Relationships;
using Xunit;

namespace ManagedCode.GraphRag.Tests.Integration.Finalization;

public class GraphFinalizerTests
{
    private static readonly EntitySeed[] SampleEntities =
    {
        new("Alice", "Person", "Researcher", new[] { "tu-1", "tu-2" }, 3),
        new("Bob", "Person", "Engineer", new[] { "tu-2" }, 2),
        new("Discovery", "Concept", "Important concept", Array.Empty<string>(), 1)
    };

    private static readonly RelationshipSeed[] SampleRelationships =
    {
        new("Alice", "Bob", "Collaborates with", 0.8, new[] { "tu-1" }),
        new("Alice", "Discovery", "Wrote about", 0.6, new[] { "tu-2" })
    };

    [Fact]
    public void FinalizeGraph_AssignsZeroLayout_WhenLayoutDisabled()
    {
        var result = GraphFinalizer.Finalize(SampleEntities, SampleRelationships);

        Assert.Equal(SampleEntities.Length, result.Entities.Count);
        Assert.Equal(SampleRelationships.Length, result.Relationships.Count);

        Assert.All(result.Entities, entity =>
        {
            Assert.NotNull(entity.Id);
            Assert.True(entity.HumanReadableId >= 0);
            Assert.Equal(entity.Title == "Alice" ? 2 : entity.Title == "Bob" ? 1 : 1, entity.Degree);
            Assert.Equal(0, entity.X);
            Assert.Equal(0, entity.Y);
        });

        Assert.All(result.Relationships, relationship =>
        {
            Assert.NotNull(relationship.Id);
            Assert.True(relationship.HumanReadableId >= 0);
            Assert.True(relationship.CombinedDegree > 0);
        });

        Assert.Equal(0, result.Entities.Sum(e => e.X));
        Assert.Equal(0, result.Entities.Sum(e => e.Y));
    }

    [Fact]
    public void FinalizeGraph_AssignsCircularLayout_WhenLayoutEnabled()
    {
        var options = new GraphFinalizerOptions(LayoutEnabled: true);
        var result = GraphFinalizer.Finalize(SampleEntities, SampleRelationships, options);

        Assert.Contains(result.Entities, e => Math.Abs(e.X) > double.Epsilon || Math.Abs(e.Y) > double.Epsilon);
    }
}
