using System.Collections.Generic;
using System.Collections.Immutable;
using GraphRag.Relationships;
using Xunit;

namespace ManagedCode.GraphRag.Tests.Relationships;

public sealed class RelationshipRecordTests
{
    [Fact]
    public void RelationshipRecord_StoresValues()
    {
        var textUnits = ImmutableArray.Create("unit-1", "unit-2");
        var record = new RelationshipRecord("rel-1", 7, "source", "target", "related_to", "description", 0.42, 3, textUnits, true);

        Assert.Equal("rel-1", record.Id);
        Assert.Equal(7, record.HumanReadableId);
        Assert.Equal("source", record.Source);
        Assert.Equal("target", record.Target);
        Assert.Equal("related_to", record.Type);
        Assert.Equal("description", record.Description);
        Assert.Equal(0.42, record.Weight);
        Assert.Equal(3, record.CombinedDegree);
        Assert.Equal(textUnits, record.TextUnitIds);
        Assert.True(record.Bidirectional);
    }

    [Fact]
    public void RelationshipSeed_StoresValues()
    {
        var textUnits = new List<string> { "unit-1", "unit-2" };
        var seed = new RelationshipSeed("source", "target", "seed", 0.33, textUnits)
        {
            Type = "influences",
            Bidirectional = true
        };

        Assert.Equal("source", seed.Source);
        Assert.Equal("target", seed.Target);
        Assert.Equal("seed", seed.Description);
        Assert.Equal(0.33, seed.Weight);
        Assert.Equal(textUnits, seed.TextUnitIds);
        Assert.Equal("influences", seed.Type);
        Assert.True(seed.Bidirectional);
    }
}
