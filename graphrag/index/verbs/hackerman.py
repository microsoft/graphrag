from datashaper import verb, VerbInput, VerbResult, TableContainer
 
@verb(name="hackerman")
def hackerman(input: VerbInput, **kwargs) -> VerbResult:
    print("I'm in the hacked! verb!")
    text_units_table = input.get_input()
    docs_table = input.get_others()[0]
 
    print("text_units_table\n", text_units_table)
    print("docs_table\n", docs_table)
 
    for index, row in text_units_table.iterrows():
        document_id = row["document_ids"][0]
        document_row = docs_table.loc[docs_table["id"] == document_id]
        document_title = document_row["title"].values[0]
        text_units_table.at[index, "chunk"] = document_title + " " + row["chunk"]
        
    return TableContainer(table=text_units_table)