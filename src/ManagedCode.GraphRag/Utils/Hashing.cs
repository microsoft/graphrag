using System.Security.Cryptography;
using System.Text;

namespace GraphRag.Utils;

public static class Hashing
{
    private static Encoder Utf8Encoder { get; } = Encoding.UTF8.GetEncoder();

    public static string GenerateSha512Hash(IEnumerable<KeyValuePair<string, object?>> fields)
    {
        ArgumentNullException.ThrowIfNull(fields);

        using var hasher = IncrementalHash.CreateHash(HashAlgorithmName.SHA512);

        Span<byte> buffer = stackalloc byte[512];

        foreach (var field in fields)
        {
            AppendStringChunked(hasher, field.Key, buffer);
            hasher.AppendData(":"u8);
            AppendStringChunked(hasher, field.Value?.ToString(), buffer);
            hasher.AppendData("|"u8);
        }

        Span<byte> hash = stackalloc byte[64];
        hasher.GetHashAndReset(hash);
        return Convert.ToHexStringLower(hash);
    }

    private static void AppendStringChunked(IncrementalHash hasher, string? value, Span<byte> buffer)
    {
        if (string.IsNullOrEmpty(value)) return;

        var remaining = value.AsSpan();

        while (remaining.Length > 0)
        {
            Utf8Encoder.Convert(remaining, buffer, flush: true, out var charsUsed, out var bytesUsed, out _);

            hasher.AppendData(buffer[..bytesUsed]);
            remaining = remaining[charsUsed..];
        }
    }

    public static string GenerateSha512Hash(params (string Key, object? Value)[] fields)
    {
        return GenerateSha512Hash(fields.Select(field => new KeyValuePair<string, object?>(field.Key, field.Value)));
    }
}
