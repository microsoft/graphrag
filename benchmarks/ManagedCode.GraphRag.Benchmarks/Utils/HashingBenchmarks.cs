using BenchmarkDotNet.Attributes;
using GraphRag.Utils;

namespace ManagedCode.GraphRag.Benchmarks.Utils;

[MemoryDiagnoser]
public class HashingBenchmarks
{
    private KeyValuePair<string, object?>[] _smallProperties = null!;
    private KeyValuePair<string, object?>[] _mediumProperties = null!;
    private KeyValuePair<string, object?>[] _largeProperties = null!;
    private KeyValuePair<string, object?>[] _largeValueProperties = null!;

    [GlobalSetup]
    public void Setup()
    {
        // 1 property with small value
        _smallProperties = new[]
        {
            new KeyValuePair<string, object?>("id", "entity-123")
        };

        // 5 properties with medium values
        _mediumProperties = new[]
        {
            new KeyValuePair<string, object?>("id", "entity-123"),
            new KeyValuePair<string, object?>("name", "Sample Entity Name"),
            new KeyValuePair<string, object?>("type", "ORGANIZATION"),
            new KeyValuePair<string, object?>("frequency", 42),
            new KeyValuePair<string, object?>("active", true)
        };

        // 20 properties with various values
        _largeProperties = Enumerable.Range(0, 20)
            .Select(i => new KeyValuePair<string, object?>($"property_{i}", $"value_{i}_with_some_content"))
            .ToArray();

        // 5 properties with large string values
        _largeValueProperties = new[]
        {
            new KeyValuePair<string, object?>("id", "entity-123"),
            new KeyValuePair<string, object?>("description", new string('x', 1000)),
            new KeyValuePair<string, object?>("content", new string('y', 2000)),
            new KeyValuePair<string, object?>("summary", new string('z', 500)),
            new KeyValuePair<string, object?>("metadata", new string('w', 1500))
        };
    }

    [Benchmark(Baseline = true)]
    public string HashSmallProperties()
    {
        return Hashing.GenerateSha512Hash(_smallProperties);
    }

    [Benchmark]
    public string HashSmallPropertiesOptimized()
    {
        return Hashing.GenerateSha512Hash_OptimizedV1(_smallProperties);
    }

    [Benchmark]
    public string HashMediumProperties()
    {
        return Hashing.GenerateSha512Hash(_mediumProperties);
    }

    [Benchmark]
    public string HashMediumPropertiesOptimized()
    {
        return Hashing.GenerateSha512Hash_OptimizedV1(_mediumProperties);
    }

    [Benchmark]
    public string HashLargeProperties()
    {
        return Hashing.GenerateSha512Hash(_largeProperties);
    }

    [Benchmark]
    public string HashLargePropertiesOptimized()
    {
        return Hashing.GenerateSha512Hash_OptimizedV1(_largeProperties);
    }

    [Benchmark]
    public string HashLargeValueProperties()
    {
        return Hashing.GenerateSha512Hash(_largeValueProperties);
    }

    [Benchmark]
    public string HashLargeValuePropertiesOptimized()
    {
        return Hashing.GenerateSha512Hash_OptimizedV1(_largeValueProperties);
    }

    [Benchmark]
    public string HashWithTuples()
    {
        return Hashing.GenerateSha512Hash(
            ("id", "entity-123"),
            ("name", "Sample Entity Name"),
            ("type", "ORGANIZATION"),
            ("frequency", (object?)42),
            ("active", (object?)true));
    }
}
