using System.Text;
using System.Text.Json;
using System.Text.Json.Serialization;
using GraphRag.Storage.Postgres.ApacheAge.JsonConverters;
using GraphRag.Storage.Postgres.ApacheAge.Types;

namespace ManagedCode.GraphRag.Tests.Storage.Postgres;

public sealed class AgeJsonConverterTests
{
    [Fact]
    public void GraphIdConverter_ReadsAndWrites()
    {
        var converter = new GraphIdConverter();
        var json = JsonDocument.Parse("123").RootElement.GetRawText();
        var reader = new Utf8JsonReader(Encoding.UTF8.GetBytes(json));
        reader.Read();
        var graphId = converter.Read(ref reader, typeof(GraphId), new JsonSerializerOptions());
        Assert.Equal((ulong)123, graphId.Value);

        using var stream = new MemoryStream();
        using var writer = new Utf8JsonWriter(stream);
        converter.Write(writer, graphId, new JsonSerializerOptions());
        writer.Flush();
        Assert.Equal("123", Encoding.UTF8.GetString(stream.ToArray()));
    }

    [Fact]
    public void InferredObjectConverter_ParsesTokens()
    {
        var converter = new InferredObjectConverter();
        var options = new JsonSerializerOptions { NumberHandling = JsonNumberHandling.AllowNamedFloatingPointLiterals };

        object Read(string payload)
        {
            var reader = new Utf8JsonReader(Encoding.UTF8.GetBytes(payload));
            reader.Read();
            return converter.Read(ref reader, typeof(object), options)!;
        }

        var smallInt = Read("5");
        Assert.IsType<int>(smallInt);
        Assert.Equal(5, (int)smallInt);

        var largeInt = Read("5000000000");
        Assert.IsType<long>(largeInt);
        Assert.Equal(5000000000L, (long)largeInt);

        var decimalValue = Read("5.5");
        Assert.IsType<decimal>(decimalValue);
        Assert.Equal(5.5m, (decimal)decimalValue);

        Assert.True((bool)Read("true"));
        Assert.Equal("text", Read(@"""text"""));
        Assert.True(double.IsPositiveInfinity((double)Read(@"""Infinity""")));
        var array = (List<object?>)Read("[1,2,3]");
        Assert.Equal(3, array.Count);
    }

    [Fact]
    public void PathObjectConverter_AlternatesVerticesAndEdges()
    {
        var converter = new PathObjectConverter();
        var vertex = @"{""id"":1,""label"":""Node"",""properties"":{}}";
        var edge = @"{""id"":2,""label"":""LINKS_TO"",""start_id"":1,""end_id"":2,""properties"":{}}";

        object Deserialize(string payload)
        {
            var reader = new Utf8JsonReader(Encoding.UTF8.GetBytes(payload));
            reader.Read();
            return converter.Read(ref reader, typeof(object), SerializerOptions.Default)!;
        }

        Assert.IsType<Vertex>(Deserialize(vertex));
        Assert.IsType<Edge>(Deserialize(edge));
        Assert.IsType<Vertex>(Deserialize(vertex));
    }

    [Fact]
    public void SerializerOptions_ConfiguresConverters()
    {
        Assert.Contains(SerializerOptions.Default.Converters, converter => converter is InferredObjectConverter);
        Assert.Contains(SerializerOptions.Default.Converters, converter => converter is GraphIdConverter);
        Assert.Contains(SerializerOptions.PathSerializer.Converters, converter => converter is PathObjectConverter);
    }
}
