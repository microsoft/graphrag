# Inputs

GraphRAG supports several input formats to simplify ingesting your data. The mechanics and features available for input files and text chunking are discussed here.

## Input Loading and Schema

All input formats are loaded within GraphRAG and passed to the indexing pipeline as a `documents` DataFrame. This DataFrame has a row for each document using a shared column schema:

| name          | type | description |
| ------------- | ---- | ----------- |
| id            | str  | ID of the document. This is generated using a hash of the text content to ensure stability across runs. |
| text          | str  | The full text of the document. |
| title         | str  | Name of the document. Some formats allow this to be configured. |
| creation_date | str  | The creation date of the document, represented as an ISO8601 string. This is harvested from the source file system. |
| metadata      | dict | Optional additional document metadata. More details below. |

Also see the [outputs](outputs.md) documentation for the final documents table schema saved to parquet after pipeline completion.

## Formats

We support three file formats out-of-the-box. This covers the overwhelming majority of use cases we have encountered. If you have a different format, we recommend writing a script to convert to one of these, which are widely used and supported by many tools and libraries.

### Plain Text

Plain text files (typically ending in .txt file extension). With plain text files we import the entire file contents as the `text` field, and the `title` is always the filename.

### Comma-delimited

CSV files (typically ending in a .csv extension). These are loaded using pandas' [`read_csv` method](https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.read_csv.html) with default options. Each row in a CSV file is treated as a single document. If you have multiple CSV files in your input folder, they will be concatenated into a single resulting `documents` DataFrame.

With the CSV format you can configure the `text_column`, and `title_column` if your data has structured content you would prefer to use. If you do not configure these within the `input` block of your settings.yaml, the title will be the filename as described in the schema above. The `text_column` is assumed to be "text" in your file if not configured specifically. We will also look for and use an "id" column if present, otherwise the ID will be generated as described above.

### JSON

JSON files (typically ending in a .json extension) contain [structured objects](https://www.json.org/). These are loaded using python's [`json.loads` method](https://docs.python.org/3/library/json.html), so your files must be properly compliant. JSON files may contain a single object in the file *or* the file may contain an array of objects at the root. We will check for and handle either of these cases. As with CSV, multiple files will be concatenated into a final table, and the `text_column` and `title_column` config options will be applied to the properties of each loaded object. Note that the specialized jsonl format produced by some libraries (one full JSON object on each line, not in an array) is not currently supported.

## Metadata

With the structured file formats (CSV and JSON) you can configure any number of columns to be added to a persisted `metadata` field in the DataFrame. This is configured by supplying a list of columns name to collect. If this is configured, the output `metadata` column will have a dict containing a key for each column, and the value of the column for that document. This metadata can optionally be used later in the GraphRAG pipeline.

### Example

software.csv

```csv
text,title,tag
My first program,Hello World,tutorial
An early space shooter game,Space Invaders,arcade
```

settings.yaml

```yaml
input:
    metadata: [title,tag]
```

Documents DataFrame

| id                    | title          | text                        | creation_date                 | metadata                                       |
| --------------------- | -------------- | --------------------------- | ----------------------------- | ---------------------------------------------- |
| (generated from text) | Hello World    | My first program            | (create date of software.csv) | { "title": "Hello World", "tag": "tutorial" }  |
| (generated from text) | Space Invaders | An early space shooter game | (create date of software.csv) | { "title": "Space Invaders", "tag": "arcade" } |

## Chunking and Metadata

As described on the [default dataflow](default_dataflow.md#phase-1-compose-textunits) page, documents are *chunked* into smaller "text units" for processing. This is done because document content size often exceeds the available context window for a given language model. There are a handful of settings you can adjust for this chunking, the most relevant being the `chunk_size` and `overlap`. We now also support a metadata processing scheme that can improve indexing results for some use cases. We will describe this feature in detail here.

Imagine the following scenario: you are indexing a collection of news articles. Each article text starts with a headline and author, and then proceeds with the content. When documents are chunked, they are split evenly according to your configured chunk size. In other words, the first *n* tokens are read into a text unit, and then the next *n*, until the end of the content. This means that front matter at the beginning of the document (such as the headline and author in this example) *is not copied to each chunk*. It only exists in the first chunk. When we later retrieve those chunks for summarization, they may therefore be missing shared information about the source document that should always be provided to the model. We have configuration options to copy repeated content into each text unit to address this issue.

### Input Config

As described above, when documents are imported you can specify a list of `metadata` columns to include with each row. This must be configured for the per-chunk copying to work.

### Chunking Config

Next, the `chunks` block needs to instruct the chunker how to handle this metadata when creating text units. By default, it is ignored. We have two settings to include it:

- `prepend_metadata`. This instructs the importer to copy the contents of the `metadata` column for each row into the start of every single text chunk. This metadata is copied as key: value pairs on new lines.
- `chunk_size_includes_metadata`: This tells the chunker how to compute the chunk size when metadata is included. By default, we create the text units using your specified `chunk_size` *and then* prepend the metadata. This means that the final text unit lengths may be longer than your configured `chunk_size`, and it will vary based on the length of the metadata for each document. When this setting is `True`, we will compute the raw text using the remainder after measuring the metadata length so that the resulting text units always comply with your configured `chunk_size`.

### Examples

The following are several examples to help illustrate how chunking config and metadate prepending works for each file format. Note that we are using word count here as "tokens" for the illustration, but language model tokens are [not equivalent to words](https://help.openai.com/en/articles/4936856-what-are-tokens-and-how-to-count-them).

#### Text files

This example uses two individual news article text files.

--

**File:** US to lift most federal COVID-19 vaccine mandates.txt

**Content:**

WASHINGTON (AP) The Biden administration will end most of the last remaining federal COVID-19 vaccine requirements next week when the national public health emergency for the coronavirus ends, the White House said Monday. Vaccine requirements for federal workers and federal contractors, as well as foreign air travelers to the U.S., will end May 11. The government is also beginning the process of lifting shot requirements for Head Start educators, healthcare workers, and noncitizens at U.S. land borders. The requirements are among the last vestiges of some of the more coercive measures taken by the federal government to promote vaccination as the deadly virus raged, and their end marks the latest display of how President Joe Biden's administration is moving to treat COVID-19 as a routine, endemic illness. "While I believe that these vaccine mandates had a tremendous beneficial impact, we are now at a point where we think that it makes a lot of sense to pull these requirements down," White House COVID-19 coordinator Dr. Ashish Jha told The Associated Press on Monday.

--

**File:** NY lawmakers begin debating budget 1 month after due date.txt

**Content:**

ALBANY, N.Y. (AP) New York lawmakers began voting Monday on a $229 billion state budget due a month ago that would raise the minimum wage, crack down on illicit pot shops and ban gas stoves and furnaces in new buildings. Negotiations among Gov. Kathy Hochul and her fellow Democrats in control of the Legislature dragged on past the April 1 budget deadline, largely because of disagreements over changes to the bail law and other policy proposals included in the spending plan. Floor debates on some budget bills began Monday. State Senate Majority Leader Andrea Stewart-Cousins said she expected voting to be wrapped up Tuesday for a budget she said contains "significant wins" for New Yorkers. "I would have liked to have done this sooner. I think we would all agree to that," Cousins told reporters before voting began. "This has been a very policy-laden budget and a lot of the policies had to parsed through." Hochul was able to push through a change to the bail law that will eliminate the standard that requires judges to prescribe the "least restrictive" means to ensure defendants return to court. Hochul said judges needed the extra discretion. Some liberal lawmakers argued that it would undercut the sweeping bail reforms approved in 2019 and result in more people with low incomes and people of color in pretrial detention. Here are some other policy provisions that will be included in the budget, according to state officials. The minimum wage would be raised to $17 in New York City and some of its suburbs and $16 in the rest of the state by 2026. That's up from $15 in the city and $14.20 upstate.

--

settings.yaml

```yaml
input:
    file_type: text
    metadata: [title]

chunks:
    size: 100
    overlap: 0
    prepend_metadata: true
    chunk_size_includes_metadata: false
```

Documents DataFrame

| id                    | title                                                         | text                        | creation_date                     | metadata                                                                     |
| --------------------- | ------------------------------------------------------------- | --------------------------- | --------------------------------- | ---------------------------------------------------------------------------- |
| (generated from text) | US to lift most federal COVID-19 vaccine mandates.txt         | (full content of text file) | (create date of article txt file) | { "title": "US to lift most federal COVID-19 vaccine mandates.txt" }         |
| (generated from text) | NY lawmakers begin debating budget 1 month after due date.txt | (full content of text file) | (create date of article txt file) | { "title": "NY lawmakers begin debating budget 1 month after due date.txt" } |

Raw Text Chunks

| content | length  |
| ------- | ------: |
| title: US to lift most federal COVID-19 vaccine mandates.txt<br>WASHINGTON (AP) The Biden administration will end most of the last remaining federal COVID-19 vaccine requirements next week when the national public health emergency for the coronavirus ends, the White House said Monday. Vaccine requirements for federal workers and federal contractors, as well as foreign air travelers to the U.S., will end May 11. The government is also beginning the process of lifting shot requirements for Head Start educators, healthcare workers, and noncitizens at U.S. land borders. The requirements are among the last vestiges of some of the more coercive measures taken by the federal government to promote vaccination as | 109 |
| title: US to lift most federal COVID-19 vaccine mandates.txt<br>the deadly virus raged, and their end marks the latest display of how President Joe Biden's administration is moving to treat COVID-19 as a routine, endemic illness. "While I believe that these vaccine mandates had a tremendous beneficial impact, we are now at a point where we think that it makes a lot of sense to pull these requirements down," White House COVID-19 coordinator Dr. Ashish Jha told The Associated Press on Monday. | 82 |
| title: NY lawmakers begin debating budget 1 month after due date.txt<br>ALBANY, N.Y. (AP) New York lawmakers began voting Monday on a $229 billion state budget due a month ago that would raise the minimum wage, crack down on illicit pot shops and ban gas stoves and furnaces in new buildings. Negotiations among Gov. Kathy Hochul and her fellow Democrats in control of the Legislature dragged on past the April 1 budget deadline, largely because of disagreements over changes to the bail law and other policy proposals included in the spending plan. Floor debates on some budget bills began Monday. State Senate Majority Leader Andrea Stewart-Cousins said she expected voting to | 111 |
| title: NY lawmakers begin debating budget 1 month after due date.txt<br>be wrapped up Tuesday for a budget she said contains "significant wins" for New Yorkers. "I would have liked to have done this sooner. I think we would all agree to that," Cousins told reporters before voting began. "This has been a very policy-laden budget and a lot of the policies had to parsed through." Hochul was able to push through a change to the bail law that will eliminate the standard that requires judges to prescribe the "least restrictive" means to ensure defendants return to court. Hochul said judges needed the extra discretion. Some liberal lawmakers argued that it | 111 |
| title: NY lawmakers begin debating budget 1 month after due date.txt<br>would undercut the sweeping bail reforms approved in 2019 and result in more people with low incomes and people of color in pretrial detention. Here are some other policy provisions that will be included in the budget, according to state officials. The minimum wage would be raised to $17 in New York City and some of its suburbs and $16 in the rest of the state by 2026. That's up from $15 in the city and $14.20 upstate. | 89 |

In this example we can see that the two input documents were parsed into five output text chunks. The title (filename) of each document is prepended but not included in the computed chunk size. Also note that the final text chunk for each document is usually smaller than the chunk size because it contains the last tokens.

#### CSV files

This example uses a single CSV file with the same two articles as rows (note that the text content is not properly escaped for actual CSV use).

--

**File:** articles.csv

**Content**

headline,article

US to lift most federal COVID-19 vaccine mandates,WASHINGTON (AP) The Biden administration will end most of the last remaining federal COVID-19 vaccine requirements next week when the national public health emergency for the coronavirus ends, the White House said Monday. Vaccine requirements for federal workers and federal contractors, as well as foreign air travelers to the U.S., will end May 11. The government is also beginning the process of lifting shot requirements for Head Start educators, healthcare workers, and noncitizens at U.S. land borders. The requirements are among the last vestiges of some of the more coercive measures taken by the federal government to promote vaccination as the deadly virus raged, and their end marks the latest display of how President Joe Biden's administration is moving to treat COVID-19 as a routine, endemic illness. "While I believe that these vaccine mandates had a tremendous beneficial impact, we are now at a point where we think that it makes a lot of sense to pull these requirements down," White House COVID-19 coordinator Dr. Ashish Jha told The Associated Press on Monday.

NY lawmakers begin debating budget 1 month after due date,ALBANY, N.Y. (AP) New York lawmakers began voting Monday on a $229 billion state budget due a month ago that would raise the minimum wage, crack down on illicit pot shops and ban gas stoves and furnaces in new buildings. Negotiations among Gov. Kathy Hochul and her fellow Democrats in control of the Legislature dragged on past the April 1 budget deadline, largely because of disagreements over changes to the bail law and other policy proposals included in the spending plan. Floor debates on some budget bills began Monday. State Senate Majority Leader Andrea Stewart-Cousins said she expected voting to be wrapped up Tuesday for a budget she said contains "significant wins" for New Yorkers. "I would have liked to have done this sooner. I think we would all agree to that," Cousins told reporters before voting began. "This has been a very policy-laden budget and a lot of the policies had to parsed through." Hochul was able to push through a change to the bail law that will eliminate the standard that requires judges to prescribe the "least restrictive" means to ensure defendants return to court. Hochul said judges needed the extra discretion. Some liberal lawmakers argued that it would undercut the sweeping bail reforms approved in 2019 and result in more people with low incomes and people of color in pretrial detention. Here are some other policy provisions that will be included in the budget, according to state officials. The minimum wage would be raised to $17 in New York City and some of its suburbs and $16 in the rest of the state by 2026. That's up from $15 in the city and $14.20 upstate.

--

settings.yaml

```yaml
input:
    file_type: csv
    title_column: headline
    text_column: article
    metadata: [headline]

chunks:
    size: 50
    overlap: 5
    prepend_metadata: true
    chunk_size_includes_metadata: true
```

Documents DataFrame

| id                    | title                                                     | text                     | creation_date                 | metadata                                                                    |
| --------------------- | --------------------------------------------------------- | ------------------------ | ----------------------------- | --------------------------------------------------------------------------- |
| (generated from text) | US to lift most federal COVID-19 vaccine mandates         | (article column content) | (create date of articles.csv) | { "headline": "US to lift most federal COVID-19 vaccine mandates" }         |
| (generated from text) | NY lawmakers begin debating budget 1 month after due date | (article column content) | (create date of articles.csv) | { "headline": "NY lawmakers begin debating budget 1 month after due date" } |

Raw Text Chunks

| content | length  |
| ------- | ------: |
| title: US to lift most federal COVID-19 vaccine mandates<br>WASHINGTON (AP) The Biden administration will end most of the last remaining federal COVID-19 vaccine requirements next week when the national public health emergency for the coronavirus ends, the White House said Monday. Vaccine requirements for federal workers and federal contractors, | 50 |
| title: US to lift most federal COVID-19 vaccine mandates<br>federal workers and federal contractors as well as foreign air travelers to the U.S., will end May 11. The government is also beginning the process of lifting shot requirements for Head Start educators, healthcare workers, and noncitizens at U.S. land borders. | 50 |
| title: US to lift most federal COVID-19 vaccine mandates<br>noncitizens at U.S. land borders. The requirements are among the last vestiges of some of the more coercive measures taken by the federal government to promote vaccination as the deadly virus raged, and their end marks the latest display of how | 50 |
| title: US to lift most federal COVID-19 vaccine mandates<br>the latest display of how  President Joe Biden's administration is moving to treat COVID-19 as a routine, endemic illness. "While I believe that these vaccine mandates had a tremendous beneficial impact, we are now at a point where we think that | 50 |
| title: US to lift most federal COVID-19 vaccine mandates<br>point where we think that it makes a lot of sense to pull these requirements down," White House COVID-19 coordinator Dr. Ashish Jha told The Associated Press on Monday. | 38 |
| title: NY lawmakers begin debating budget 1 month after due date<br>ALBANY, N.Y. (AP) New York lawmakers began voting Monday on a $229 billion state budget due a month ago that would raise the minimum wage, crack down on illicit pot shops and ban gas stoves and furnaces in new | 50 |
| title: NY lawmakers begin debating budget 1 month after due date<br>stoves and furnaces in new buildings. Negotiations among Gov. Kathy Hochul and her fellow Democrats in control of the Legislature dragged on past the April 1 budget deadline, largely because of disagreements over changes to the bail law and | 50 |
| title: NY lawmakers begin debating budget 1 month after due date<br>to the bail law and other policy proposals included in the spending plan. Floor debates on some budget bills began Monday. State Senate Majority Leader Andrea Stewart-Cousins said she expected voting to be wrapped up Tuesday for a budget | 50 |
|title: NY lawmakers begin debating budget 1 month after due date<br>up Tuesday for a budget she said contains "significant wins" for New Yorkers. "I would have liked to have done this sooner. I think we would all agree to that," Cousins told reporters before voting began. "This has been | 50 |
| title: NY lawmakers begin debating budget 1 month after due date<br>voting began. "This has been a very policy-laden budget and a lot of the policies had to parsed through." Hochul was able to push through a change to the bail law that will eliminate the standard that requires judges | 50 |
| title: NY lawmakers begin debating budget 1 month after due date<br>the standard that requires judges to prescribe the "least restrictive" means to ensure defendants return to court. Hochul said judges needed the extra discretion. Some liberal lawmakers argued that it would undercut the sweeping bail reforms approved in 2019 | 50 |
| title: NY lawmakers begin debating budget 1 month after due date<br>bail reforms approved in 2019 and result in more people with low incomes and people of color in pretrial detention. Here are some other policy provisions that will be included in the budget, according to state officials. The minimum | 50 |
| title: NY lawmakers begin debating budget 1 month after due date<br>to state officials. The minimum  wage would be raised to $17 in be raised to $17 in New York City and some of its suburbs and $16 in the rest of the state by 2026. That's up from $15 | 50 |
| title: NY lawmakers begin debating budget 1 month after due date<br>2026. That's up from $15 in the city and $14.20 upstate. | 22 |


In this example we can see that the two input documents were parsed into fourteen output text chunks. The title (headline) of each document is prepended and included in the computed chunk size, so each chunk matches the configured chunk size (except the last one for each document). We've also configured some overlap in these text chunks, so the last five tokens are shared. Why would you use overlap in your text chunks? Consider that when you are splitting documents based on tokens, it is highly likely that sentences or even related concepts will be split into separate chunks. Each text chunk is processed separately by the language model, so this may result in incomplete "ideas" at the boundaries of the chunk. Overlap ensures that these split concepts are fully contained in at least one of the chunks.


#### JSON files

This final example uses a JSON file for each of the same two articles. In this example we'll set the object fields to read, but we will not add metadata to the text chunks.

--

**File:** article1.json

**Content**

```json
{
    "headline": "US to lift most federal COVID-19 vaccine mandates",
    "content": "WASHINGTON (AP) The Biden administration will end most of the last remaining federal COVID-19 vaccine requirements next week when the national public health emergency for the coronavirus ends, the White House said Monday. Vaccine requirements for federal workers and federal contractors, as well as foreign air travelers to the U.S., will end May 11. The government is also beginning the process of lifting shot requirements for Head Start educators, healthcare workers, and noncitizens at U.S. land borders. The requirements are among the last vestiges of some of the more coercive measures taken by the federal government to promote vaccination as the deadly virus raged, and their end marks the latest display of how President Joe Biden's administration is moving to treat COVID-19 as a routine, endemic illness. "While I believe that these vaccine mandates had a tremendous beneficial impact, we are now at a point where we think that it makes a lot of sense to pull these requirements down," White House COVID-19 coordinator Dr. Ashish Jha told The Associated Press on Monday."
}
```

**File:** article2.json

**Content**

```json
{
    "headline": "NY lawmakers begin debating budget 1 month after due date",
    "content": "ALBANY, N.Y. (AP) New York lawmakers began voting Monday on a $229 billion state budget due a month ago that would raise the minimum wage, crack down on illicit pot shops and ban gas stoves and furnaces in new buildings. Negotiations among Gov. Kathy Hochul and her fellow Democrats in control of the Legislature dragged on past the April 1 budget deadline, largely because of disagreements over changes to the bail law and other policy proposals included in the spending plan. Floor debates on some budget bills began Monday. State Senate Majority Leader Andrea Stewart-Cousins said she expected voting to be wrapped up Tuesday for a budget she said contains "significant wins" for New Yorkers. "I would have liked to have done this sooner. I think we would all agree to that," Cousins told reporters before voting began. "This has been a very policy-laden budget and a lot of the policies had to parsed through." Hochul was able to push through a change to the bail law that will eliminate the standard that requires judges to prescribe the "least restrictive" means to ensure defendants return to court. Hochul said judges needed the extra discretion. Some liberal lawmakers argued that it would undercut the sweeping bail reforms approved in 2019 and result in more people with low incomes and people of color in pretrial detention. Here are some other policy provisions that will be included in the budget, according to state officials. The minimum wage would be raised to $17 in New York City and some of its suburbs and $16 in the rest of the state by 2026. That's up from $15 in the city and $14.20 upstate."
}
```

--

settings.yaml

```yaml
input:
    file_type: json
    title_column: headline
    text_column: content

chunks:
    size: 100
    overlap: 10
```

Documents DataFrame

| id                    | title                                                     | text                     | creation_date                  | metadata |
| --------------------- | --------------------------------------------------------- | ------------------------ | ------------------------------ | -------- |
| (generated from text) | US to lift most federal COVID-19 vaccine mandates         | (article column content) | (create date of article1.json) | { }      |
| (generated from text) | NY lawmakers begin debating budget 1 month after due date | (article column content) | (create date of article2.json) | { }      |

Raw Text Chunks

| content | length  |
| ------- | ------: |
| WASHINGTON (AP) The Biden administration will end most of the last remaining federal COVID-19 vaccine requirements next week when the national public health emergency for the coronavirus ends, the White House said Monday. Vaccine requirements for federal workers and federal contractors, as well as foreign air travelers to the U.S., will end May 11. The government is also beginning the process of lifting shot requirements for Head Start educators, healthcare workers, and noncitizens at U.S. land borders. The requirements are among the last vestiges of some of the more coercive measures taken by the federal government to promote vaccination as | 100 |
| measures taken by the federal government to promote vaccination as  the deadly virus raged, and their end marks the latest display of how President Joe Biden's administration is moving to treat COVID-19 as a routine, endemic illness. "While I believe that these vaccine mandates had a tremendous beneficial impact, we are now at a point where we think that it makes a lot of sense to pull these requirements down," White House COVID-19 coordinator Dr. Ashish Jha told The Associated Press on Monday. | 83 |
| ALBANY, N.Y. (AP) New York lawmakers began voting Monday on a $229 billion state budget due a month ago that would raise the minimum wage, crack down on illicit pot shops and ban gas stoves and furnaces in new buildings. Negotiations among Gov. Kathy Hochul and her fellow Democrats in control of the Legislature dragged on past the April 1 budget deadline, largely because of disagreements over changes to the bail law and other policy proposals included in the spending plan. Floor debates on some budget bills began Monday. State Senate Majority Leader Andrea Stewart-Cousins said she expected voting to | 100 |
| Senate Majority Leader Andrea Stewart-Cousins said she expected voting to be wrapped up Tuesday for a budget she said contains "significant wins" for New Yorkers. "I would have liked to have done this sooner. I think we would all agree to that," Cousins told reporters before voting began. "This has been a very policy-laden budget and a lot of the policies had to parsed through." Hochul was able to push through a change to the bail law that will eliminate the standard that requires judges to prescribe the "least restrictive" means to ensure defendants return to court. Hochul said judges | 100 |
| means to ensure defendants return to court. Hochul said judges needed the extra discretion. Some liberal lawmakers argued that it would undercut the sweeping bail reforms approved in 2019 and result in more people with low incomes and people of color in pretrial detention. Here are some other policy provisions that will be included in the budget, according to state officials. The minimum wage would be raised to $17 in New York City and some of its suburbs and $16 in the rest of the state by 2026. That's up from $15 in the city and $14.20 upstate. | 98 |


In this example the two input documents were parsed into five output text chunks. There is no metadata prepended, so each chunk matches the configured chunk size (except the last one for each document). We've also configured some overlap in these text chunks, so the last ten tokens are shared.



