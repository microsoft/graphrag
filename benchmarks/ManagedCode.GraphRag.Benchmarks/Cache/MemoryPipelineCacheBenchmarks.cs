using BenchmarkDotNet.Attributes;
using GraphRag.Cache;
using Microsoft.Extensions.Caching.Memory;

namespace ManagedCode.GraphRag.Benchmarks.Cache;

[MemoryDiagnoser]
public class MemoryPipelineCacheBenchmarks
{
    private IMemoryCache _memoryCache = null!;
    private MemoryPipelineCache _cache = null!;
    private string[] _keys = null!;
    private object[] _values = null!;

    [Params(1_000, 10_000, 100_000)]
    public int EntryCount { get; set; }

    [GlobalSetup]
    public void Setup()
    {
        _memoryCache = new MemoryCache(new MemoryCacheOptions());
        _cache = new MemoryPipelineCache(_memoryCache);

        _keys = new string[EntryCount];
        _values = new object[EntryCount];

        for (var i = 0; i < EntryCount; i++)
        {
            _keys[i] = $"key-{i:D8}";
            _values[i] = new { Id = i, Name = $"Value-{i}", Data = new byte[100] };
        }
    }

    [GlobalCleanup]
    public void Cleanup()
    {
        _memoryCache.Dispose();
    }

    [Benchmark]
    public async Task SetEntries()
    {
        for (var i = 0; i < EntryCount; i++)
        {
            await _cache.SetAsync(_keys[i], _values[i]);
        }
    }

    [Benchmark]
    public async Task GetEntries()
    {
        // Pre-populate
        for (var i = 0; i < EntryCount; i++)
        {
            await _cache.SetAsync(_keys[i], _values[i]);
        }

        // Measure gets
        for (var i = 0; i < EntryCount; i++)
        {
            _ = await _cache.GetAsync(_keys[i]);
        }
    }

    [Benchmark]
    public async Task HasEntries()
    {
        // Pre-populate
        for (var i = 0; i < EntryCount; i++)
        {
            await _cache.SetAsync(_keys[i], _values[i]);
        }

        // Measure has checks
        for (var i = 0; i < EntryCount; i++)
        {
            _ = await _cache.HasAsync(_keys[i]);
        }
    }

    [Benchmark]
    public async Task ClearCache()
    {
        // Pre-populate
        for (var i = 0; i < EntryCount; i++)
        {
            await _cache.SetAsync(_keys[i], _values[i]);
        }

        // Measure clear
        await _cache.ClearAsync();
    }

    [Benchmark]
    public IPipelineCache CreateChildScope()
    {
        return _cache.CreateChild("child-scope");
    }
}
