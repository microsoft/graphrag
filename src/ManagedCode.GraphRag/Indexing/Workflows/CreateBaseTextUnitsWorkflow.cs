using System;
using System.Collections.Generic;
using System.Linq;
using GraphRag.Chunking;
using GraphRag.Config;
using GraphRag.Data;
using GraphRag.Indexing.Runtime;
using GraphRag.Logging;
using GraphRag.Utils;
using Microsoft.Extensions.DependencyInjection;
using GraphRag.Tokenization;
using GraphRag.Storage;

namespace GraphRag.Indexing.Workflows;

internal static class CreateBaseTextUnitsWorkflow
{
    public const string Name = "create_base_text_units";

    public static WorkflowDelegate Create()
    {
        return async (config, context, cancellationToken) =>
        {
            var documents = await context.OutputStorage.LoadTableAsync<DocumentRecord>("documents", cancellationToken).ConfigureAwait(false);
            context.Stats.NumDocuments = documents.Count;

            var textUnits = new List<TextUnitRecord>();
            var callbacks = context.Callbacks;
            var chunkingConfig = config.Chunks;
            var chunkerResolver = context.Services.GetRequiredService<IChunkerResolver>();
            var tokenizerProvider = context.Services.GetRequiredService<ITokenizerProvider>();
            var chunker = chunkerResolver.Resolve(chunkingConfig.Strategy);

            foreach (var document in documents)
            {
                cancellationToken.ThrowIfCancellationRequested();

                var metadataPrefix = chunkingConfig.PrependMetadata
                    ? FormatMetadata(document.Metadata)
                    : null;

                var tokenizer = tokenizerProvider.GetTokenizer(chunkingConfig.EncodingModel);
                var metadataTokens = metadataPrefix is null ? 0 : tokenizer.CountTokens(metadataPrefix);
                var chunkConfig = CreateEffectiveConfig(chunkingConfig, metadataTokens);

                var slices = new[] { new ChunkSlice(document.Id, document.Text) };
                var chunks = chunker.Chunk(slices, chunkConfig);

                foreach (var chunk in chunks)
                {
                    var text = metadataPrefix is null ? chunk.Text : metadataPrefix + chunk.Text;
                    var id = Hashing.GenerateSha512Hash(("document", document.Id), ("text", text));
                    textUnits.Add(new TextUnitRecord
                    {
                        Id = id,
                        Text = text,
                        TokenCount = chunk.TokenCount,
                        DocumentIds = chunk.DocumentIds,
                        EntityIds = Array.Empty<string>(),
                        RelationshipIds = Array.Empty<string>(),
                        CovariateIds = Array.Empty<string>()
                    });
                }

                callbacks.ReportProgress(new ProgressSnapshot($"Chunked document {document.Id}", documents.Count, textUnits.Count));
            }

            var filtered = textUnits
                .Where(unit => !string.IsNullOrWhiteSpace(unit.Text))
                .ToArray();

            await context.OutputStorage.WriteTableAsync("text_units", filtered, cancellationToken).ConfigureAwait(false);

            return new WorkflowResult(filtered);
        };
    }

    private static string? FormatMetadata(IDictionary<string, object?>? metadata)
    {
        if (metadata is null || metadata.Count == 0)
        {
            return null;
        }

        var builder = new System.Text.StringBuilder();
        foreach (var entry in metadata)
        {
            if (entry.Value is null)
            {
                continue;
            }

            builder.Append(entry.Key);
            builder.Append(':');
            builder.Append(' ');
            builder.Append(entry.Value);
            builder.Append(".\n");
        }

        return builder.ToString();
    }

    private static ChunkingConfig CreateEffectiveConfig(ChunkingConfig original, int metadataTokens)
    {
        if (!original.ChunkSizeIncludesMetadata || metadataTokens == 0)
        {
            return original;
        }

        if (metadataTokens >= original.Size)
        {
            throw new InvalidOperationException("Metadata tokens exceed the maximum tokens per chunk. Increase chunk size.");
        }

        return new ChunkingConfig
        {
            Size = original.Size - metadataTokens,
            Overlap = original.Overlap,
            EncodingModel = original.EncodingModel,
            Strategy = original.Strategy,
            PrependMetadata = original.PrependMetadata,
            ChunkSizeIncludesMetadata = original.ChunkSizeIncludesMetadata,
            GroupByColumns = original.GroupByColumns is { Count: > 0 }
                ? new List<string>(original.GroupByColumns)
                : new List<string>()
        };
    }
}
