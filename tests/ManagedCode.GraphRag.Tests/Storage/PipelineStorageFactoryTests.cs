using System;
using System.IO;
using GraphRag.Config;
using GraphRag.Storage;
using Xunit;

namespace ManagedCode.GraphRag.Tests.Storage;

public sealed class PipelineStorageFactoryTests
{
    [Fact]
    public void Create_ReturnsMemoryStorageForMemoryType()
    {
        var config = new StorageConfig { Type = StorageType.Memory };
        var storage = PipelineStorageFactory.Create(config);
        Assert.IsType<MemoryPipelineStorage>(storage);
    }

    [Fact]
    public void Create_ReturnsFileStorageForFileType()
    {
        var config = new StorageConfig { Type = StorageType.File, BaseDir = Path.Combine(Path.GetTempPath(), Guid.NewGuid().ToString("N")) };
        var storage = PipelineStorageFactory.Create(config);
        try
        {
            Assert.IsType<FilePipelineStorage>(storage);
        }
        finally
        {
            if (Directory.Exists(config.BaseDir))
            {
                Directory.Delete(config.BaseDir, recursive: true);
            }
        }
    }

    [Fact]
    public void Create_ThrowsForUnsupportedType()
    {
        var config = new StorageConfig { Type = StorageType.Blob };
        Assert.Throws<NotSupportedException>(() => PipelineStorageFactory.Create(config));
    }
}
