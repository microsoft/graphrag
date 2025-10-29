using System.Collections.Immutable;
using System.Linq;
using GraphRag.Community;
using Xunit;

namespace ManagedCode.GraphRag.Tests.Community;

public sealed class CommunityRecordTests
{
    [Fact]
    public void Constructor_PopulatesAllProperties()
    {
        var record = new CommunityRecord(
            Id: "community-uuid",
            HumanReadableId: 12,
            CommunityId: 42,
            Level: 3,
            ParentId: 7,
            Children: ImmutableArray.Create(8, 9),
            Title: "Energy Sector",
            EntityIds: ImmutableArray.Create("entity-1", "entity-2"),
            RelationshipIds: ImmutableArray.Create("rel-1"),
            TextUnitIds: ImmutableArray.Create("unit-1", "unit-2"),
            Period: "2024-05-01",
            Size: 18);

        Assert.Equal("community-uuid", record.Id);
        Assert.Equal(12, record.HumanReadableId);
        Assert.Equal(42, record.CommunityId);
        Assert.Equal(3, record.Level);
        Assert.Equal(7, record.ParentId);
        Assert.Equal(new[] { 8, 9 }, record.Children.ToArray());
        Assert.Equal("Energy Sector", record.Title);
        Assert.Equal(new[] { "entity-1", "entity-2" }, record.EntityIds.ToArray());
        Assert.Equal(new[] { "rel-1" }, record.RelationshipIds.ToArray());
        Assert.Equal(new[] { "unit-1", "unit-2" }, record.TextUnitIds.ToArray());
        Assert.Equal("2024-05-01", record.Period);
        Assert.Equal(18, record.Size);
    }
}
