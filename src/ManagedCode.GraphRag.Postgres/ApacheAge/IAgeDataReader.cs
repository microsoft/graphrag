namespace GraphRag.Storage.Postgres.ApacheAge;

/// <summary>
/// Defines the data reader for accessing the results from an AGE query execution.
/// </summary>
public interface IAgeDataReader
{
    /// <summary>
    /// Gets the number of columns in the current row.
    /// </summary>
    int FieldCount { get; }

    /// <summary>
    /// Indicates if the reader is positioned on a row. That is, whether
    /// a column can be read.
    /// </summary>
    bool IsOnRow { get; }

    /// <summary>
    /// Gets a value indicating whether this reader contains one or more rows.
    /// </summary>
    bool HasRows { get; }

    /// <summary>
    /// Gets a value indicating whether the data reader is closed.
    /// </summary>
    bool IsClosed { get; }

    /// <summary>
    /// Closes the internal reader, allowing other commands to be executed.
    /// </summary>
    void Close();

    /// <summary>
    /// Closes the internal reader, allowing other commands to be executed.
    /// </summary>
    void CloseAsync();

    /// <summary>
    /// Get the name of a column.
    /// </summary>
    /// <param name="ordinal">
    /// Zero-based column ordinal.
    /// </param>
    /// <returns>
    /// The name of the column.
    /// </returns>
    string GetName(int ordinal);

    /// <summary>
    /// Get the zero-based ordinal of the column with the given name.
    /// </summary>
    /// <param name="name">
    /// Column name.
    /// </param>
    /// <returns>
    /// A zero-based column ordinal.
    /// </returns>
    int GetOrdinal(string name);

    /// <summary>
    /// Gets the value of a specified column as an instance of <typeparamref name="T"/>.
    /// </summary>
    /// <param name="ordinal">
    /// Zero-based column ordinal.
    /// </param>
    /// <returns>
    /// The column's <typeparamref name="T"/> value.
    /// </returns>
    T GetValue<T>(int ordinal);

    /// <summary>
    /// Gets the value of a specified column as an instance of <typeparamref name="T"/>.
    /// </summary>
    /// <param name="ordinal">
    /// Zero-based column ordinal.
    /// </param>
    /// <returns>
    /// The column's <typeparamref name="T"/> value.
    /// </returns>
    Task<T> GetValueAsync<T>(int ordinal);

    /// <summary>
    /// Populates an array of objects with the field values of the current row.
    /// </summary>
    /// <param name="values">
    /// Array of objects to populate.
    /// </param>
    /// <returns>
    /// The number of fields returned.
    /// </returns>
    int GetValues(object[] values);

    /// <summary>
    /// Advances the reader to the next record in the result set.
    /// </summary>
    /// <returns>
    /// Returns <see langword="true"/> if there are more rows, otherwise, 
    /// <see langword="false"/>.
    /// </returns>
    bool Read();

    /// <summary>
    /// Asynchronously advances the reader to the next record in the result set.
    /// </summary>
    /// <returns>
    /// Returns <see langword="true"/> if there are more rows, otherwise, 
    /// <see langword="false"/>.
    /// </returns>
    Task<bool> ReadAsync();
}
