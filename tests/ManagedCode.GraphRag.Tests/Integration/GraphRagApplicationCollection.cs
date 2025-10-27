using Xunit;

namespace ManagedCode.GraphRag.Tests.Integration;

[CollectionDefinition(nameof(GraphRagApplicationCollection))]
public sealed class GraphRagApplicationCollection : ICollectionFixture<GraphRagApplicationFixture>
{
}
