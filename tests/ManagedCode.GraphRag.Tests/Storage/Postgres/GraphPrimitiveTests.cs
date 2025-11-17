using System.Reflection;
using GraphRag.Storage.Postgres.ApacheAge.Types;
using GraphPath = GraphRag.Storage.Postgres.ApacheAge.Types.Path;

namespace ManagedCode.GraphRag.Tests.Storage.Postgres;

public sealed class GraphPrimitiveTests
{
    [Fact]
    public void GraphId_ComparesAndFormats()
    {
        var a = new GraphId(10);
        var b = new GraphId(20);

        Assert.True(a < b);
        Assert.True(b > a);
        Assert.True(a <= b);
        Assert.True(b >= a);
        Assert.Equal("10", a.ToString());

        Assert.Equal(0, a.CompareTo(a));
        Assert.Equal(-1, a.CompareTo(b));
        Assert.Equal(1, b.CompareTo(a));

        Assert.True(a == new GraphId(10));
        Assert.True(a != b);
        Assert.Throws<ArgumentException>(() => a.CompareTo("not-a-graph-id"));
    }

    [Fact]
    public void Vertex_ToStringIncludesProperties()
    {
        var vertex = new Vertex
        {
            Id = new GraphId(1),
            Label = "Entity",
            Properties = new Dictionary<string, object?> { ["name"] = "alpha" }
        };

        var representation = vertex.ToString();
        Assert.Contains(@"""label"": ""Entity""", representation);
        Assert.Equal(vertex, vertex);
        var clone = vertex;
        Assert.True(vertex == clone);
        Assert.False(vertex != clone);
    }

    [Fact]
    public void Edge_ToStringIncludesEndpoints()
    {
        var edge = new Edge
        {
            Id = new GraphId(99),
            StartId = new GraphId(1),
            EndId = new GraphId(2),
            Label = "KNOWS",
            Properties = new Dictionary<string, object?> { ["weight"] = 0.5 }
        };

        var representation = edge.ToString();
        Assert.Contains(@"""start_id"": 1", representation);
        Assert.Contains(@"""end_id"": 2", representation);
        var clonedEdge = edge;
        Assert.True(edge == clonedEdge);
        Assert.False(edge != clonedEdge);
    }

    [Fact]
    public void Path_ConstructsFromVertexAndEdgeSequence()
    {
        var vertices = new[]
        {
            new Vertex { Id = new GraphId(1), Label = "Person", Properties = new Dictionary<string, object?>() },
            new Vertex { Id = new GraphId(2), Label = "Person", Properties = new Dictionary<string, object?>() },
            new Vertex { Id = new GraphId(3), Label = "Person", Properties = new Dictionary<string, object?>() }
        };

        var edges = new[]
        {
            new Edge { Id = new GraphId(10), Label = "L", StartId = vertices[0].Id, EndId = vertices[1].Id, Properties = new Dictionary<string, object?>() },
            new Edge { Id = new GraphId(11), Label = "L", StartId = vertices[1].Id, EndId = vertices[2].Id, Properties = new Dictionary<string, object?>() }
        };

        var rawPath = new object[] { vertices[0], edges[0], vertices[1], edges[1], vertices[2] };
        var ctor = typeof(GraphPath).GetConstructor(
            BindingFlags.NonPublic | BindingFlags.Instance,
            binder: null,
            types: new[] { typeof(object[]) },
            modifiers: null);
        Assert.NotNull(ctor);
        var path = (GraphPath)ctor!.Invoke(new object[] { rawPath });

        Assert.Equal(2, path.Length);
        Assert.Equal(3, path.Vertices.Length);
        Assert.Equal(2, path.Edges.Length);
        Assert.Equal(vertices[2].Id, path.Vertices[^1].Id);
        Assert.Equal(edges[1].Id, path.Edges[^1].Id);
    }

    [Fact]
    public void Path_InvalidSequenceThrows()
    {
        var rawPath = new object[] { new Edge() };
        var ctor = typeof(GraphPath).GetConstructor(
            BindingFlags.NonPublic | BindingFlags.Instance,
            binder: null,
            types: new[] { typeof(object[]) },
            modifiers: null);
        Assert.NotNull(ctor);
        Assert.Throws<FormatException>(() =>
        {
            try
            {
                ctor!.Invoke(new object[] { rawPath });
            }
            catch (TargetInvocationException ex) when (ex.InnerException is not null)
            {
                throw ex.InnerException;
            }
        });
    }
}
