using System.Collections.Generic;
using System.Globalization;
using System.Text;
using GraphRag.Entities;

namespace GraphRag.LanguageModels;

internal static class GraphRagPromptLibrary
{
    internal const string ExtractGraphSystemPrompt = """
You are a precise information extraction engine. Analyse the supplied text and return structured JSON describing:
- distinct entities (people, organisations, locations, products, events, concepts, technologies, dates, other)
- relationships between those entities

Rules:
- Only use information explicitly stated or implied in the text.
- Prefer short, human-readable titles.
- Use snake_case relationship types (e.g., "works_with", "located_in").
- Always return valid JSON adhering to the response schema.
""";

    internal const string CommunitySummarySystemPrompt = """
You are an investigative analyst. Produce concise, neutral summaries that describe the shared theme binding the supplied entities.
Highlight how they relate, why the cluster matters, and any notable signals the reader should know. Do not invent facts.
""";

    internal static string BuildExtractGraphUserPrompt(string textUnit, int maxEntities, string? template = null)
    {
        if (!string.IsNullOrWhiteSpace(template))
        {
            return template
                .Replace("{{max_entities}}", maxEntities.ToString(CultureInfo.InvariantCulture), StringComparison.Ordinal)
                .Replace("{{text}}", textUnit, StringComparison.Ordinal);
        }

        return @$"Extract up to {maxEntities} of the most important entities and their relationships from the following text.

Text (between <BEGIN_TEXT> and <END_TEXT> markers):
<BEGIN_TEXT>
{textUnit}
<END_TEXT>

Respond with JSON matching this schema:
{{
  ""entities"": [
    {{
      ""title"": ""string"",
      ""type"": ""person | organization | location | product | event | concept | technology | date | other"",
      ""description"": ""short description"",
      ""confidence"": 0.0 - 1.0
    }}
  ],
  ""relationships"": [
    {{
      ""source"": ""entity title"",
      ""target"": ""entity title"",
      ""type"": ""relationship_type"",
      ""description"": ""short description"",
      ""weight"": 0.0 - 1.0,
      ""bidirectional"": true | false
    }}
  ]
}}";
    }

    internal static string BuildCommunitySummaryUserPrompt(IReadOnlyList<EntityRecord> community, int maxLength, string? template = null)
    {
        var entityLines = BuildEntityLines(community);

        if (!string.IsNullOrWhiteSpace(template))
        {
            return template
                .Replace("{{max_length}}", maxLength.ToString(CultureInfo.InvariantCulture), StringComparison.Ordinal)
                .Replace("{{entities}}", entityLines, StringComparison.Ordinal);
        }

        var builder = new StringBuilder();
        builder.Append("Summarise the key theme that connects the following entities in no more than ");
        builder.Append(maxLength);
        builder.AppendLine(" characters. Focus on what unites them and why the group matters. Avoid bullet lists.");
        builder.AppendLine();
        builder.AppendLine("Entities:");

        builder.AppendLine(entityLines);
        builder.AppendLine();
        builder.AppendLine("Provide a single paragraph answer.");
        return builder.ToString();
    }

    private static string BuildEntityLines(IEnumerable<EntityRecord> community)
    {
        var builder = new StringBuilder();
        foreach (var entity in community)
        {
            builder.Append("- ");
            builder.Append(entity.Title);
            if (!string.IsNullOrWhiteSpace(entity.Description))
            {
                builder.Append(": ");
                builder.Append(entity.Description);
            }

            builder.AppendLine();
        }

        return builder.ToString().TrimEnd();
    }
}
