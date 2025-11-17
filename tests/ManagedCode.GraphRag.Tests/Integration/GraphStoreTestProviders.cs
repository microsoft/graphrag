namespace ManagedCode.GraphRag.Tests.Integration;

internal static class GraphStoreTestProviders
{
    private static readonly (string Key, string Label)[] ProviderMap =
    {
        ("postgres", "Chapter"),
        ("neo4j", "Person"),
        ("cosmos", "Document"),
        ("janus", "Person")
    };

    public static IEnumerable<object[]> ProviderKeys =>
        ProviderMap.Select(tuple => new object[] { tuple.Key });

    public static IEnumerable<object[]> ProviderKeysAndLabels =>
        ProviderMap.Select(tuple => new object[] { tuple.Key, tuple.Label });

    public static string GetLabel(string providerKey)
    {
        foreach (var tuple in ProviderMap)
        {
            if (string.Equals(tuple.Key, providerKey, StringComparison.OrdinalIgnoreCase))
            {
                return tuple.Label;
            }
        }

        return "Entity";
    }
}
