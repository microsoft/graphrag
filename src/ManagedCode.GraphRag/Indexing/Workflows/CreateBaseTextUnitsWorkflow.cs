using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using GraphRag.Config;
using GraphRag.Data;
using GraphRag.Indexing.Operations;
using GraphRag.Indexing.Runtime;
using GraphRag.Logging;
using GraphRag.Storage;
using GraphRag.Utils;

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

            foreach (var document in documents)
            {
                cancellationToken.ThrowIfCancellationRequested();

                var metadataPrefix = config.Chunks.PrependMetadata
                    ? FormatMetadata(document.Metadata)
                    : null;

                var chunks = TextChunker.Chunk(document, config.Chunks, metadataPrefix, config.Chunks.ChunkSizeIncludesMetadata);

                foreach (var chunk in chunks)
                {
                    var id = Hashing.GenerateSha512Hash(("document", document.Id), ("text", chunk.Text));
                    textUnits.Add(new TextUnitRecord
                    {
                        Id = id,
                        Text = chunk.Text,
                        TokenCount = chunk.TokenCount,
                        DocumentIds = chunk.DocumentIds
                    });
                }

                callbacks.ReportProgress(new Logging.ProgressSnapshot($"Chunked document {document.Id}", documents.Count, textUnits.Count));
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
}
