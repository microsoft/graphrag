using GraphRag.Utils;

namespace ManagedCode.GraphRag.Tests.Utils;

public class HashingTests
{
    [Fact]
    public void GenerateSha512Hash_WithSingleProperty_ReturnsConsistentHash()
    {
        var fields = new[] { new KeyValuePair<string, object?>("id", "entity-123") };

        var hash1 = Hashing.GenerateSha512Hash(fields);
        var hash2 = Hashing.GenerateSha512Hash(fields);

        Assert.Equal(hash1, hash2);
        Assert.Equal(128, hash1.Length);  // SHA512 = 64 bytes = 128 hex chars
        Assert.True(hash1.All(c => char.IsAsciiHexDigitLower(c) || char.IsDigit(c)));
    }

    [Fact]
    public void GenerateSha512Hash_WithMultipleProperties_ReturnsConsistentHash()
    {
        var fields = new[]
        {
            new KeyValuePair<string, object?>("id", "123"),
            new KeyValuePair<string, object?>("name", "Test"),
            new KeyValuePair<string, object?>("count", 42),
        };

        var hash1 = Hashing.GenerateSha512Hash(fields);
        var hash2 = Hashing.GenerateSha512Hash(fields);

        Assert.Equal(hash1, hash2);
    }

    [Fact]
    public void GenerateSha512Hash_WithEmptyValue_HandlesCorrectly()
    {
        var fields = new[] { new KeyValuePair<string, object?>("empty", "") };

        var hash = Hashing.GenerateSha512Hash(fields);

        Assert.NotEmpty(hash);
    }

    [Fact]
    public void GenerateSha512Hash_WithNullValue_HandlesCorrectly()
    {
        var fields = new[] { new KeyValuePair<string, object?>("nullable", null) };

        var hash = Hashing.GenerateSha512Hash(fields);

        Assert.NotEmpty(hash);
    }

    [Fact]
    public void GenerateSha512Hash_WithUnicodeValue_HandlesCorrectly()
    {
        var fields = new[] { new KeyValuePair<string, object?>("unicode", "日本語🎉émoji") };

        var hash = Hashing.GenerateSha512Hash(fields);

        Assert.Equal(128, hash.Length);
    }

    [Fact]
    public void GenerateSha512Hash_WithLargeValue_HandlesCorrectly()
    {
        var largeValue = new string('x', 10_000);
        var fields = new[] { new KeyValuePair<string, object?>("large", largeValue) };

        var hash = Hashing.GenerateSha512Hash(fields);

        Assert.Equal(128, hash.Length);
    }

    [Fact]
    public void GenerateSha512Hash_DifferentInputs_ProduceDifferentHashes()
    {
        var fields1 = new[] { new KeyValuePair<string, object?>("id", "1") };
        var fields2 = new[] { new KeyValuePair<string, object?>("id", "2") };

        var hash1 = Hashing.GenerateSha512Hash(fields1);
        var hash2 = Hashing.GenerateSha512Hash(fields2);

        Assert.NotEqual(hash1, hash2);
    }

    [Fact]
    public void GenerateSha512Hash_PropertyOrderMatters()
    {
        var fields1 = new[]
        {
            new KeyValuePair<string, object?>("a", "1"),
            new KeyValuePair<string, object?>("b", "2"),
        };
        var fields2 = new[]
        {
            new KeyValuePair<string, object?>("b", "2"),
            new KeyValuePair<string, object?>("a", "1"),
        };

        var hash1 = Hashing.GenerateSha512Hash(fields1);
        var hash2 = Hashing.GenerateSha512Hash(fields2);

        Assert.NotEqual(hash1, hash2);
    }

    [Fact]
    public void GenerateSha512Hash_TuplesOverload_MatchesKeyValuePairOverload()
    {
        var kvpHash = Hashing.GenerateSha512Hash([
            new KeyValuePair<string, object?>("id", "123"),
            new KeyValuePair<string, object?>("name", "Test")
        ]);

        var tupleHash = Hashing.GenerateSha512Hash(
            ("id", (object?)"123"),
            ("name", (object?)"Test"));

        Assert.Equal(kvpHash, tupleHash);
    }
}
