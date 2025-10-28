using System.Text;
using System.Text.Json;
using System.Text.RegularExpressions;
using GraphRag.Config;
using GraphRag.Constants;
using GraphRag.Data;
using GraphRag.Indexing.Runtime;
using GraphRag.Storage;
using GraphRag.Utils;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging;

namespace GraphRag.Indexing.Workflows;

internal static class LoadInputDocumentsWorkflow
{
    public const string Name = "load_input_documents";

    public static WorkflowDelegate Create()
    {
        return async (config, context, cancellationToken) =>
        {
            var logger = context.Services.GetService<ILoggerFactory>()?.CreateLogger(typeof(LoadInputDocumentsWorkflow));
            var documents = await LoadDocumentsAsync(config.Input, context.InputStorage, logger, cancellationToken).ConfigureAwait(false);

            context.Stats.NumDocuments = documents.Count;
            logger?.LogInformation("Final number of documents loaded: {Count}", documents.Count);

            await context.OutputStorage.WriteTableAsync(PipelineTableNames.Documents, documents, cancellationToken).ConfigureAwait(false);
            return new WorkflowResult(documents);
        };
    }

    private static async Task<IReadOnlyList<DocumentRecord>> LoadDocumentsAsync(
        InputConfig inputConfig,
        IPipelineStorage storage,
        ILogger? logger,
        CancellationToken cancellationToken)
    {
        ArgumentNullException.ThrowIfNull(inputConfig);
        ArgumentNullException.ThrowIfNull(storage);

        logger?.LogInformation("Loading input documents from {Root}", inputConfig.Storage.BaseDir);

        var pattern = new Regex(inputConfig.FilePattern, RegexOptions.IgnoreCase | RegexOptions.Compiled);
        IReadOnlyDictionary<string, object?>? fileFilter = inputConfig.FileFilter?.ToDictionary(
            static kvp => kvp.Key,
            static kvp => (object?)kvp.Value,
            StringComparer.OrdinalIgnoreCase);
        var matches = new List<PipelineStorageItem>();

        await foreach (var item in storage.FindAsync(pattern, fileFilter: fileFilter, cancellationToken: cancellationToken))
        {
            matches.Add(item);
        }

        if (matches.Count == 0)
        {
            throw new InvalidOperationException($"No files matching pattern '{inputConfig.FilePattern}' were found.");
        }

        logger?.LogInformation("Found {Count} candidate files", matches.Count);

        return inputConfig.FileType switch
        {
            InputFileType.Text => await LoadTextDocumentsAsync(storage, matches, inputConfig, logger, cancellationToken).ConfigureAwait(false),
            InputFileType.Csv => await LoadCsvDocumentsAsync(storage, matches, inputConfig, logger, cancellationToken).ConfigureAwait(false),
            InputFileType.Json => await LoadJsonDocumentsAsync(storage, matches, inputConfig, logger, cancellationToken).ConfigureAwait(false),
            _ => throw new NotSupportedException($"Input file type '{inputConfig.FileType}' is not supported yet.")
        };
    }

    private static async Task<IReadOnlyList<DocumentRecord>> LoadCsvDocumentsAsync(
        IPipelineStorage storage,
        IReadOnlyList<PipelineStorageItem> matches,
        InputConfig inputConfig,
        ILogger? logger,
        CancellationToken cancellationToken)
    {
        var encoding = ResolveEncoding(inputConfig.Encoding);
        var documents = new List<DocumentRecord>();

        foreach (var match in matches)
        {
            cancellationToken.ThrowIfCancellationRequested();

            try
            {
                var csvText = await ReadTextAsync(storage, match.Path, encoding, cancellationToken).ConfigureAwait(false);
                using var reader = new StringReader(csvText);
                using var parser = new Microsoft.VisualBasic.FileIO.TextFieldParser(reader)
                {
                    TextFieldType = Microsoft.VisualBasic.FileIO.FieldType.Delimited,
                    HasFieldsEnclosedInQuotes = true
                };
                parser.SetDelimiters(",");

                if (parser.EndOfData)
                {
                    continue;
                }

                var headers = parser.ReadFields() ?? Array.Empty<string>();
                var headerIndex = headers
                    .Select((header, idx) => new { header, idx })
                    .ToDictionary(pair => pair.header.Trim(), pair => pair.idx, StringComparer.OrdinalIgnoreCase);

                while (!parser.EndOfData)
                {
                    var row = parser.ReadFields();
                    if (row is null)
                    {
                        continue;
                    }

                    var record = BuildDocumentFromRow(row, headers, headerIndex, match, inputConfig);
                    documents.Add(record);
                }
            }
            catch (Exception ex)
            {
                logger?.LogWarning(ex, "Failed to load CSV document {Path}. Skipping.", match.Path);
            }
        }

        logger?.LogInformation("Loaded {Count} CSV documents", documents.Count);
        return documents;
    }

    private static DocumentRecord BuildDocumentFromRow(
        string[] row,
        string[] headers,
        IReadOnlyDictionary<string, int> headerIndex,
        PipelineStorageItem item,
        InputConfig config)
    {
        var values = new Dictionary<string, object?>(StringComparer.OrdinalIgnoreCase);
        for (var index = 0; index < headers.Length && index < row.Length; index++)
        {
            values[headers[index]] = row[index];
        }

        var text = ResolveColumnValue(config.TextColumn, values) ?? string.Join(' ', row);
        var title = ResolveColumnValue(config.TitleColumn, values) ?? Path.GetFileName(item.Path);

        var metadata = new Dictionary<string, object?>(StringComparer.OrdinalIgnoreCase);
        if (config.Metadata is { Count: > 0 })
        {
            foreach (var column in config.Metadata)
            {
                if (values.TryGetValue(column, out var value) && value is not null)
                {
                    metadata[column] = value;
                }
            }
        }

        var hashComponents = values.Select(kvp => new KeyValuePair<string, object?>(kvp.Key, kvp.Value)).ToList();
        hashComponents.Add(new KeyValuePair<string, object?>(HashFieldNames.Text, text));
        var id = Hashing.GenerateSha512Hash(hashComponents);

        return new DocumentRecord
        {
            Id = id,
            Title = title,
            Text = text,
            CreationDate = item.CreatedAt,
            Metadata = metadata,
            TextUnitIds = Array.Empty<string>()
        };
    }

    private static async Task<IReadOnlyList<DocumentRecord>> LoadJsonDocumentsAsync(
        IPipelineStorage storage,
        IReadOnlyList<PipelineStorageItem> matches,
        InputConfig inputConfig,
        ILogger? logger,
        CancellationToken cancellationToken)
    {
        var encoding = ResolveEncoding(inputConfig.Encoding);
        var documents = new List<DocumentRecord>();

        foreach (var match in matches)
        {
            cancellationToken.ThrowIfCancellationRequested();

            try
            {
                var jsonText = await ReadTextAsync(storage, match.Path, encoding, cancellationToken).ConfigureAwait(false);
                if (string.IsNullOrWhiteSpace(jsonText))
                {
                    continue;
                }

                var parsed = TryParseJsonDocument(jsonText, match, inputConfig, documents, logger);
                if (!parsed)
                {
                    AppendJsonLines(documents, jsonText, match, inputConfig, logger);
                }
            }
            catch (Exception ex)
            {
                logger?.LogWarning(ex, "Failed to load JSON document {Path}. Skipping.", match.Path);
            }
        }

        logger?.LogInformation("Loaded {Count} JSON documents", documents.Count);
        return documents;
    }

    private static bool TryParseJsonDocument(
        string jsonText,
        PipelineStorageItem item,
        InputConfig config,
        ICollection<DocumentRecord> accumulator,
        ILogger? logger)
    {
        try
        {
            using var document = JsonDocument.Parse(jsonText);
            if (document.RootElement.ValueKind == JsonValueKind.Array)
            {
                foreach (var element in document.RootElement.EnumerateArray())
                {
                    AppendJsonDocument(accumulator, element, item, config);
                }

                return true;
            }

            if (document.RootElement.ValueKind == JsonValueKind.Object)
            {
                AppendJsonDocument(accumulator, document.RootElement, item, config);
                return true;
            }

            return false;
        }
        catch (JsonException ex)
        {
            logger?.LogDebug(ex, "Failed to parse JSON document {Path} as object/array, falling back to JSON Lines.", item.Path);
            return false;
        }
    }

    private static void AppendJsonLines(
        ICollection<DocumentRecord> accumulator,
        string jsonText,
        PipelineStorageItem item,
        InputConfig config,
        ILogger? logger)
    {
        var lines = jsonText.Split(['\n'], StringSplitOptions.RemoveEmptyEntries | StringSplitOptions.TrimEntries);
        foreach (var line in lines)
        {
            if (string.IsNullOrWhiteSpace(line))
            {
                continue;
            }

            try
            {
                using var lineDoc = JsonDocument.Parse(line);
                AppendJsonDocument(accumulator, lineDoc.RootElement, item, config);
            }
            catch (JsonException ex)
            {
                logger?.LogDebug(ex, "Skipping malformed JSON line in {Path}.", item.Path);
            }
        }
    }

    private static void AppendJsonDocument(
        ICollection<DocumentRecord> accumulator,
        JsonElement element,
        PipelineStorageItem item,
        InputConfig config)
    {
        if (element.ValueKind != JsonValueKind.Object)
        {
            return;
        }

        var values = element.EnumerateObject().ToDictionary(p => p.Name, p => JsonElementToValue(p.Value), StringComparer.OrdinalIgnoreCase);

        var text = ResolveColumnValue(config.TextColumn, values) ?? element.GetRawText();
        var title = ResolveColumnValue(config.TitleColumn, values) ?? Path.GetFileName(item.Path);

        var metadata = new Dictionary<string, object?>(StringComparer.OrdinalIgnoreCase);
        if (config.Metadata is { Count: > 0 })
        {
            foreach (var column in config.Metadata)
            {
                if (values.TryGetValue(column, out var value) && value is not null)
                {
                    metadata[column] = value;
                }
            }
        }

        var hashComponents = values.Select(kvp => new KeyValuePair<string, object?>(kvp.Key, kvp.Value)).ToList();
        hashComponents.Add(new KeyValuePair<string, object?>(HashFieldNames.Text, text));
        var id = Hashing.GenerateSha512Hash(hashComponents);

        accumulator.Add(new DocumentRecord
        {
            Id = id,
            Title = title,
            Text = text,
            CreationDate = item.CreatedAt,
            Metadata = metadata,
            TextUnitIds = Array.Empty<string>()
        });
    }

    private static string? ResolveColumnValue(string? columnName, IReadOnlyDictionary<string, object?> values)
    {
        if (string.IsNullOrWhiteSpace(columnName))
        {
            return null;
        }

        return values.TryGetValue(columnName, out var value) ? value?.ToString() : null;
    }

    private static object? JsonElementToValue(JsonElement element)
    {
        return element.ValueKind switch
        {
            JsonValueKind.String => element.GetString(),
            JsonValueKind.Number => element.TryGetInt64(out var i64) ? i64 : element.GetDouble(),
            JsonValueKind.True => true,
            JsonValueKind.False => false,
            JsonValueKind.Array => element.EnumerateArray().Select(JsonElementToValue).ToArray(),
            JsonValueKind.Object => element.EnumerateObject().ToDictionary(p => p.Name, p => JsonElementToValue(p.Value)),
            _ => null
        };
    }

    private static async Task<IReadOnlyList<DocumentRecord>> LoadTextDocumentsAsync(
        IPipelineStorage storage,
        IReadOnlyList<PipelineStorageItem> matches,
        InputConfig inputConfig,
        ILogger? logger,
        CancellationToken cancellationToken)
    {
        var encoding = ResolveEncoding(inputConfig.Encoding);
        var documents = new List<DocumentRecord>(matches.Count);

        foreach (var match in matches)
        {
            cancellationToken.ThrowIfCancellationRequested();

            try
            {
                var text = await ReadTextAsync(storage, match.Path, encoding, cancellationToken).ConfigureAwait(false);
                var createdAt = match.CreatedAt ?? await storage.GetCreationDateAsync(match.Path, cancellationToken).ConfigureAwait(false);
                var metadata = match.Metadata is { Count: > 0 } ? new Dictionary<string, object?>(match.Metadata) : new Dictionary<string, object?>();

                var hashComponents = new List<KeyValuePair<string, object?>>
                {
                    new(HashFieldNames.Path, match.Path),
                    new(HashFieldNames.Text, text)
                };

                foreach (var kvp in metadata)
                {
                    hashComponents.Add(new KeyValuePair<string, object?>(kvp.Key, kvp.Value));
                }

                var id = Hashing.GenerateSha512Hash(hashComponents);

                documents.Add(new DocumentRecord
                {
                    Id = id,
                    Title = Path.GetFileName(match.Path),
                    Text = text,
                    CreationDate = createdAt,
                    Metadata = metadata,
                    TextUnitIds = Array.Empty<string>()
                });
            }
            catch (Exception ex)
            {
                logger?.LogWarning(ex, "Failed to load document {Path}. Skipping.", match.Path);
            }
        }

        logger?.LogInformation("Loaded {Count} documents", documents.Count);
        return documents;
    }

    private static async Task<string> ReadTextAsync(
        IPipelineStorage storage,
        string path,
        Encoding encoding,
        CancellationToken cancellationToken)
    {
        await using var stream = await storage.GetAsync(path, asBytes: true, cancellationToken: cancellationToken).ConfigureAwait(false)
            ?? throw new FileNotFoundException($"Input document '{path}' not found in storage.");

        using var memory = new MemoryStream();
        await stream.CopyToAsync(memory, cancellationToken).ConfigureAwait(false);
        return encoding.GetString(memory.ToArray());
    }

    private static Encoding ResolveEncoding(string encodingName)
    {
        if (string.IsNullOrWhiteSpace(encodingName))
        {
            return Encoding.UTF8;
        }

        try
        {
            return Encoding.GetEncoding(encodingName);
        }
        catch (Exception ex)
        {
            throw new InvalidOperationException($"Unsupported encoding '{encodingName}'.", ex);
        }
    }
}
