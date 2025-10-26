using GraphRag.Config;

namespace GraphRag.Storage;

public static class PipelineStorageFactory
{
    public static IPipelineStorage Create(StorageConfig config)
    {
        ArgumentNullException.ThrowIfNull(config);

        return config.Type switch
        {
            StorageType.File => new FilePipelineStorage(config.BaseDir),
            StorageType.Memory => new MemoryPipelineStorage(),
            _ => throw new NotSupportedException($"Storage type '{config.Type}' is not supported yet.")
        };
    }
}
