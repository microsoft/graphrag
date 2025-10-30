using System;
using System.IO;
using GraphRag.Config;
using GraphRag.Constants;
using GraphRag.LanguageModels;
using Xunit;

namespace ManagedCode.GraphRag.Tests.LanguageModels;

public sealed class PromptTemplateLoaderTests : IDisposable
{
    private readonly string _rootDir;

    public PromptTemplateLoaderTests()
    {
        _rootDir = Path.Combine(Path.GetTempPath(), Guid.NewGuid().ToString("N"));
        Directory.CreateDirectory(_rootDir);
    }

    [Fact]
    public void ResolveOrDefault_UsesExplicitPath()
    {
        var templatePath = Path.Combine(_rootDir, "custom.txt");
        File.WriteAllText(templatePath, "explicit prompt");

        var config = new GraphRagConfig { RootDir = _rootDir };
        var loader = PromptTemplateLoader.Create(config);

        var prompt = loader.ResolveOrDefault(PromptTemplateKeys.ExtractGraphUser, "custom.txt", "fallback");

        Assert.Equal("explicit prompt", prompt);
    }

    [Fact]
    public void ResolveOptional_ReadsManualDirectory()
    {
        var manualDirectory = Path.Combine(_rootDir, "manual");
        Directory.CreateDirectory(Path.Combine(manualDirectory, "index", "community_reports"));
        var manualPath = Path.Combine(manualDirectory, "index", "community_reports", "user.txt");
        File.WriteAllText(manualPath, "manual prompt");

        var config = new GraphRagConfig
        {
            RootDir = _rootDir,
            PromptTuning = new PromptTuningConfig
            {
                Manual = new ManualPromptTuningConfig
                {
                    Enabled = true,
                    Directory = "manual"
                }
            }
        };

        var loader = PromptTemplateLoader.Create(config);
        var prompt = loader.ResolveOptional(PromptTemplateKeys.CommunitySummaryUser, null);

        Assert.Equal("manual prompt", prompt);
    }

    [Fact]
    public void ResolveOrDefault_FallsBackToAutoDirectory()
    {
        var autoDirectory = Path.Combine(_rootDir, "auto");
        Directory.CreateDirectory(Path.Combine(autoDirectory, "index", "extract_graph"));
        var autoPath = Path.Combine(autoDirectory, "index", "extract_graph", "system.txt");
        File.WriteAllText(autoPath, "auto system");

        var config = new GraphRagConfig
        {
            RootDir = _rootDir,
            PromptTuning = new PromptTuningConfig
            {
                Auto = new AutoPromptTuningConfig
                {
                    Enabled = true,
                    Directory = "auto"
                }
            }
        };

        var loader = PromptTemplateLoader.Create(config);
        var prompt = loader.ResolveOrDefault(PromptTemplateKeys.ExtractGraphSystem, null, "fallback");

        Assert.Equal("auto system", prompt);
    }

    public void Dispose()
    {
        try
        {
            if (Directory.Exists(_rootDir))
            {
                Directory.Delete(_rootDir, recursive: true);
            }
        }
        catch
        {
        }
    }
}
