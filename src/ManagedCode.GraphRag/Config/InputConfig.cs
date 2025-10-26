using System.Collections.Generic;

namespace GraphRag.Config;

public sealed class InputConfig
{
    public StorageConfig Storage { get; set; } = new()
    {
        BaseDir = "input",
        Type = StorageType.File
    };

    public InputFileType FileType { get; set; } = InputFileType.Text;

    public string Encoding { get; set; } = "utf-8";

    public string FilePattern { get; set; } = ".*\\.txt$";

    public Dictionary<string, string>? FileFilter { get; set; }
        = new(StringComparer.OrdinalIgnoreCase);

    public string TextColumn { get; set; } = "text";

    public string? TitleColumn { get; set; } = "title";

    public List<string>? Metadata { get; set; }
        = new() { "publication" };
}
