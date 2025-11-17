using System.Globalization;
using GraphRag.Storage.Postgres.ApacheAge.Types;

namespace ManagedCode.GraphRag.Tests.Storage.Postgres;

public sealed class AgtypeTests
{
    [Fact]
    public void Agtype_ConvertsNumericValues()
    {
        var agtype = new Agtype("42");
        Assert.Equal("42", agtype.GetString());
        Assert.Equal(42, agtype.GetInt32());
        Assert.Equal(42u, agtype.GetUInt32());
        Assert.Equal(42L, agtype.GetInt64());
        Assert.Equal(42UL, agtype.GetUInt64());
        Assert.Equal(42m, agtype.GetDecimal());
        Assert.Equal((byte)42, agtype.GetByte());
        Assert.Equal((sbyte)42, agtype.GetSByte());
        Assert.Equal((short)42, agtype.GetInt16());
        Assert.Equal((ushort)42, agtype.GetUInt16());
    }

    [Fact]
    public void Agtype_ConvertsFloatingPointLiterals()
    {
        Assert.True(new Agtype("true").GetBoolean());
        Assert.False(new Agtype("false").GetBoolean());

        Assert.Equal(double.NegativeInfinity, new Agtype("-Infinity").GetDouble());
        Assert.Equal(double.PositiveInfinity, new Agtype("Infinity").GetDouble());
        Assert.True(double.IsNaN(new Agtype("NaN").GetDouble()));

        Assert.Equal(float.NegativeInfinity, new Agtype("-Infinity").GetFloat());
        Assert.Equal(float.PositiveInfinity, new Agtype("Infinity").GetFloat());
        Assert.True(float.IsNaN(new Agtype("NaN").GetFloat()));
    }

    [Fact]
    public void Agtype_ReturnsListsAndVertices()
    {
        var payload = @"[{""value"":1},{""value"":2}]";
        var list = new Agtype(payload).GetList();
        Assert.Equal(2, list.Count);

        var vertexJson =
            @"{""id"": 1,""label"": ""Entity"",""properties"": {""name"": ""alpha""}}::vertex";
        var vertex = new Agtype(vertexJson).GetVertex();
        Assert.Equal("Entity", vertex.Label);
        Assert.Equal("alpha", vertex.Properties["name"]);

        var edgeJson =
            @"{""id"": 2,""label"": ""CONNECTS"",""start_id"": 1,""end_id"": 2,""properties"": {""weight"": 0.5}}::edge";
        var edge = new Agtype(edgeJson).GetEdge();
        Assert.Equal("CONNECTS", edge.Label);
        Assert.Equal(0.5m, Convert.ToDecimal(edge.Properties["weight"], CultureInfo.InvariantCulture));
    }

    [Fact]
    public void Agtype_ReturnsPaths()
    {
        var vertexA =
            @"{""id"": 1,""label"": ""Entity"",""properties"": {""name"": ""alpha""}}::vertex";
        var vertexB =
            @"{""id"": 2,""label"": ""Entity"",""properties"": {""name"": ""beta""}}::vertex";
        var edge =
            @"{""id"": 3,""label"": ""CONNECTS"",""start_id"": 1,""end_id"": 2,""properties"": {}}::edge";
        var pathPayload = $"[{vertexA},{edge},{vertexB}]::path";

        var path = new Agtype(pathPayload).GetPath();

        Assert.Equal(1, path.Length);
        Assert.Equal(2, path.Vertices.Length);
        Assert.Single(path.Edges);
        Assert.Equal("alpha", path.Vertices[0].Properties["name"]);
        Assert.Equal("CONNECTS", path.Edges[0].Label);
    }

    [Fact]
    public void Agtype_InvalidVertexThrows()
    {
        var agtype = new Agtype(@"{""id"":1}::edge");
        Assert.Throws<FormatException>(() => agtype.GetVertex());
    }

    [Fact]
    public void Agtype_InvalidPathThrows()
    {
        var agtype = new Agtype(@"[{""id"":1}]");
        Assert.Throws<FormatException>(() => agtype.GetPath());
    }
}
