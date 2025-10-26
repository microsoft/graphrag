using System;
using System.Collections.Generic;
using System.Linq;
using GraphRag.Constants;
using GraphRag.Data;
using GraphRag.Indexing.Runtime;
using GraphRag.Storage;

namespace GraphRag.Indexing.Workflows;

internal static class CreateFinalDocumentsWorkflow
{
    public const string Name = "create_final_documents";

    public static WorkflowDelegate Create()
    {
        return async (config, context, cancellationToken) =>
        {
            var documents = await context.OutputStorage.LoadTableAsync<DocumentRecord>(PipelineTableNames.Documents, cancellationToken).ConfigureAwait(false);
            var textUnits = await context.OutputStorage.LoadTableAsync<TextUnitRecord>(PipelineTableNames.TextUnits, cancellationToken).ConfigureAwait(false);

            var updates = documents.ToDictionary(
                document => document.Id,
                document => new DocumentAggregation(document));

            foreach (var unit in textUnits)
            {
                cancellationToken.ThrowIfCancellationRequested();

                foreach (var documentId in unit.DocumentIds)
                {
                    if (updates.TryGetValue(documentId, out var aggregation))
                    {
                        aggregation.TextUnitIds.Add(unit.Id);
                    }
                }
            }

            var finalized = updates.Values
                .Select((aggregation, index) => aggregation.ToRecord(index))
                .ToArray();

            await context.OutputStorage.WriteTableAsync(PipelineTableNames.Documents, finalized, cancellationToken).ConfigureAwait(false);

            return new WorkflowResult(finalized);
        };
    }

    private sealed class DocumentAggregation
    {
        private readonly DocumentRecord _source;

        public DocumentAggregation(DocumentRecord source)
        {
            _source = source ?? throw new ArgumentNullException(nameof(source));
            TextUnitIds = new List<string>(_source.TextUnitIds ?? Array.Empty<string>());
        }

        public List<string> TextUnitIds { get; }

        public DocumentRecord ToRecord(int index)
        {
            return _source with
            {
                TextUnitIds = TextUnitIds.Count > 0 ? TextUnitIds.ToArray() : Array.Empty<string>(),
                HumanReadableId = index,
                Metadata = _source.Metadata ?? new Dictionary<string, object?>()
            };
        }
    }
}
