using GraphRag.Storage.Postgres.ApacheAge.Types;
using Npgsql;

namespace GraphRag.Storage.Postgres.ApacheAge;

/// <summary>
/// Data reader for accessing the results from an AGE query execution.
/// </summary>
public class AgeDataReader : IAgeDataReader, IDisposable, IAsyncDisposable
{
    private readonly NpgsqlDataReader _reader;
    private bool _isDisposed;

    /// <summary>
    /// Initialises a new instance of <see cref="AgeDataReader"/>.
    /// </summary>
    /// <param name="reader">
    /// </param>
    internal AgeDataReader(NpgsqlDataReader reader)
    {
        _reader = reader;
    }

    public int FieldCount => _reader.FieldCount;
    public bool IsOnRow => _reader.IsOnRow;
    public bool HasRows => _reader.HasRows;
    public bool IsClosed => _reader.IsClosed;

    public void Close() => _reader.Close();

    public void CloseAsync() => _reader.CloseAsync();

    public bool Read() => _reader.Read();

    public Task<bool> ReadAsync() => _reader.ReadAsync();

    public int GetValues(object[] values)
    {
        var loaded = _reader.GetValues(values);
        for (var index = 0; index < loaded; index++)
        {
            if (values[index] is string text && IsAgtypeColumn(index))
            {
                values[index] = new Agtype(text);
            }
        }

        return loaded;
    }

    public T GetValue<T>(int ordinal)
    {
        if (IsAgtypeRequest(typeof(T), out var isNullable))
        {
            if (_reader.IsDBNull(ordinal))
            {
                return default!;
            }

            var agtype = ReadAgtype(ordinal);
            return ConvertAgtypeResult<T>(agtype, isNullable);
        }

        return _reader.GetFieldValue<T>(ordinal);
    }

    public async Task<T> GetValueAsync<T>(int ordinal)
    {
        if (IsAgtypeRequest(typeof(T), out var isNullable))
        {
            if (await _reader.IsDBNullAsync(ordinal))
            {
                return default!;
            }

            var agtype = await ReadAgtypeAsync(ordinal);
            return ConvertAgtypeResult<T>(agtype, isNullable);
        }

        return await _reader.GetFieldValueAsync<T>(ordinal);
    }

    public string GetName(int ordinal) => _reader.GetName(ordinal);

    public int GetOrdinal(string name) => _reader.GetOrdinal(name);

    #region Dispose

    ~AgeDataReader() => _reader.Dispose();

    public void Dispose()
    {
        if (!_isDisposed)
        {
            _reader.Dispose();
            GC.SuppressFinalize(this);
        }
        _isDisposed = true;
    }

    public async ValueTask DisposeAsync()
    {
        if (!_isDisposed)
        {
            await _reader.DisposeAsync();
            GC.SuppressFinalize(this);
        }
        _isDisposed = true;
    }

    #endregion

    private static bool IsAgtypeRequest(Type requestedType, out bool isNullable)
    {
        if (requestedType == typeof(Agtype))
        {
            isNullable = false;
            return true;
        }

        var underlying = Nullable.GetUnderlyingType(requestedType);
        if (underlying == typeof(Agtype))
        {
            isNullable = true;
            return true;
        }

        isNullable = false;
        return false;
    }

    private static T ConvertAgtypeResult<T>(Agtype agtype, bool isNullable)
    {
        if (isNullable)
        {
            Agtype? nullable = agtype;
            return (T)(object)nullable;
        }

        return (T)(object)agtype;
    }

    private bool IsAgtypeColumn(int ordinal)
    {
        var typeName = _reader.GetDataTypeName(ordinal);
        return IsAgtypeTypeName(typeName) || IsTextualTypeName(typeName) || IsUnknownTypeName(typeName);
    }

    private Agtype ReadAgtype(int ordinal)
    {
        var typeName = _reader.GetDataTypeName(ordinal);
        if (IsAgtypeTypeName(typeName))
        {
            try
            {
                return _reader.GetFieldValue<Agtype>(ordinal);
            }
            catch (InvalidCastException)
            {
                return ReadAgtypeFromString(ordinal);
            }
        }

        if (IsTextualTypeName(typeName) || IsUnknownTypeName(typeName))
        {
            return ReadAgtypeFromString(ordinal);
        }

        throw new InvalidOperationException(
            $"Field '{_reader.GetName(ordinal)}' ({typeName}) cannot be materialized as Agtype.");
    }

    private async Task<Agtype> ReadAgtypeAsync(int ordinal)
    {
        var typeName = _reader.GetDataTypeName(ordinal);
        if (IsAgtypeTypeName(typeName))
        {
            try
            {
                return await _reader.GetFieldValueAsync<Agtype>(ordinal);
            }
            catch (InvalidCastException)
            {
                return await ReadAgtypeFromStringAsync(ordinal);
            }
        }

        if (IsTextualTypeName(typeName) || IsUnknownTypeName(typeName))
        {
            return await ReadAgtypeFromStringAsync(ordinal);
        }

        throw new InvalidOperationException(
            $"Field '{_reader.GetName(ordinal)}' ({typeName}) cannot be materialized as Agtype.");
    }

    private static bool IsAgtypeTypeName(string? typeName) =>
        string.Equals(typeName, "ag_catalog.agtype", StringComparison.OrdinalIgnoreCase) ||
        string.Equals(typeName, "agtype", StringComparison.OrdinalIgnoreCase);

    private static bool IsTextualTypeName(string? typeName) =>
        string.Equals(typeName, "text", StringComparison.OrdinalIgnoreCase) ||
        string.Equals(typeName, "varchar", StringComparison.OrdinalIgnoreCase) ||
        string.Equals(typeName, "character varying", StringComparison.OrdinalIgnoreCase);

    private static bool IsUnknownTypeName(string? typeName) =>
        string.IsNullOrWhiteSpace(typeName) ||
        typeName.Contains("unknown", StringComparison.OrdinalIgnoreCase);

    private Agtype ReadAgtypeFromString(int ordinal)
    {
        var raw = _reader.GetString(ordinal);
        return new Agtype(raw);
    }

    private async Task<Agtype> ReadAgtypeFromStringAsync(int ordinal)
    {
        var raw = await _reader.GetFieldValueAsync<string>(ordinal);
        return new Agtype(raw);
    }
}
