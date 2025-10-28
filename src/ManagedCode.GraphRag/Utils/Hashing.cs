using System.Security.Cryptography;
using System.Text;

namespace GraphRag.Utils;

public static class Hashing
{
    public static string GenerateSha512Hash(IEnumerable<KeyValuePair<string, object?>> fields)
    {
        ArgumentNullException.ThrowIfNull(fields);

        var builder = new StringBuilder();
        foreach (var field in fields)
        {
            builder.Append(field.Key);
            builder.Append(':');
            builder.Append(field.Value);
            builder.Append('|');
        }

        var bytes = Encoding.UTF8.GetBytes(builder.ToString());
        var hash = SHA512.HashData(bytes);
        return Convert.ToHexString(hash).ToLowerInvariant();
    }

    public static string GenerateSha512Hash(params (string Key, object? Value)[] fields)
    {
        return GenerateSha512Hash(fields.Select(field => new KeyValuePair<string, object?>(field.Key, field.Value)));
    }
}
