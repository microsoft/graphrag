using System;
using System.Collections.Generic;

namespace GraphRag.Data;

public sealed record DocumentRecord
{
    public required string Id { get; init; }

    public string? Title { get; init; }

    public required string Text { get; init; }

    public DateTimeOffset? CreationDate { get; init; }

    public IDictionary<string, object?>? Metadata { get; init; }

    public IReadOnlyList<string> TextUnitIds { get; init; } = Array.Empty<string>();
}
