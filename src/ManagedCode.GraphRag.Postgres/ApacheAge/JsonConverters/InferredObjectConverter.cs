using System.Text.Json;
using System.Text.Json.Serialization;

namespace GraphRag.Storage.Postgres.ApacheAge.JsonConverters;

/// <summary>
/// A custom converter to infer object types from their JSON token type.
/// <para>
/// For example, numbers in the json will be returned as a valid number type
/// in C# (<see langword="int"/>, <see langword="long"/>, <see langword="decimal"/>, or 
/// <see langword="double"/>).
/// </para>
/// </summary>
internal sealed class InferredObjectConverter : JsonConverter<object>
{
    public override object? Read(ref Utf8JsonReader reader, Type typeToConvert, JsonSerializerOptions options)
    {
        switch (reader.TokenType)
        {
            // If it's a '[' token, parse it as an array.
            case JsonTokenType.StartArray:
                return JsonDocument.ParseValue(ref reader).Deserialize<List<object?>>(options);

            // Parse 'Infinity', '-Infinity', and 'NaN' as doubles instead of strings if required.
            case JsonTokenType.String:
                if ((options.NumberHandling & JsonNumberHandling.AllowNamedFloatingPointLiterals) != 0)
                {
                    if (reader.GetString()!.Equals("Infinity", StringComparison.OrdinalIgnoreCase))
                    {
                        return double.PositiveInfinity;
                    }

                    if (reader.GetString()!.Equals("-Infinity", StringComparison.OrdinalIgnoreCase))
                    {
                        return double.NegativeInfinity;
                    }

                    if (reader.GetString()!.Equals("NaN", StringComparison.OrdinalIgnoreCase))
                    {
                        return double.NaN;
                    }
                }
                return reader.GetString()!;

            // Parse number.
            // First, try to parse it as an int. If that doesn't work, parse it as a long.
            // And if that doesn't work, go on to parse it as a decimal.
            // Finally, if decimal doesn't work, parse it as a double.
            case JsonTokenType.Number:
                if (reader.TryGetInt32(out var integer))
                {
                    return integer;
                }
                else if (reader.TryGetInt64(out var @long))
                {
                    return @long;
                }
                else if (reader.TryGetDecimal(out var @decimal))
                {
                    return @decimal;
                }
                else
                {
                    return reader.GetDouble();
                }

            case JsonTokenType.True:
                return true;

            case JsonTokenType.False:
                return false;

            case JsonTokenType.Null:
                return null;

            default:
                return JsonDocument.ParseValue(ref reader).RootElement.Clone();
        }
    }

    public override void Write(Utf8JsonWriter writer, object value, JsonSerializerOptions options)
    {
        JsonSerializer.Serialize(writer, value, value.GetType(), options);
    }
}
