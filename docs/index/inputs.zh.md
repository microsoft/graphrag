# 输入

GraphRAG 支持多种输入格式，以简化数据摄取。这里将讨论输入文件和文本分块可用的机制与功能。

## 输入加载与架构

所有输入格式都会在 GraphRAG 中加载，并作为 `documents` DataFrame 传递给索引流水线。该 DataFrame 为每个文档包含一行，并使用共享的列架构：

| name          | type | description |
| ------------- | ---- | ----------- |
| id            | str  | 文档的 ID。它使用文本内容的哈希生成，以确保在多次运行之间保持稳定。 |
| text          | str  | 文档的完整文本。 |
| title         | str  | 文档名称。某些格式允许对此进行配置。 |
| creation_date | str  | 文档的创建日期，以 ISO8601 字符串表示。这是从源文件系统中提取的。 |
| metadata      | dict | 可选的附加文档元数据。更多细节见下文。 |

另请参阅 [outputs](outputs.md) 文档，了解流水线完成后保存到 parquet 的最终 documents 表架构。

## 自带 DataFrame

GraphRAG 的 [索引 API 方法](https://github.com/microsoft/graphrag/blob/main/packages/graphrag/graphrag/api/index.py) 允许你传入自己的 pandas DataFrame，并绕过下一节中描述的所有输入加载/解析过程。如果你的内容采用我们开箱即用不支持的格式或存储位置，这会很方便。_你必须确保输入的 DataFrame 符合上述架构。_ 后文描述的所有分块行为都将完全相同地进行。

## 自定义文件处理

我们使用可注入的 InputReader 提供程序类。这意味着你可以在一个继承 InputReader 的类中实现任何你想要的输入文件处理逻辑，并将其注册到 InputReaderFactory。有关我们标准提供程序模式的更多信息，请参阅 [architecture page](https://microsoft.github.io/graphrag/index/architecture/)。

## 格式

我们开箱即用支持三种文件格式。这覆盖了我们遇到的绝大多数用例。如果你使用的是不同格式，我们建议你要么实现自己的 InputReader，要么编写脚本转换为以下格式之一，因为它们被广泛使用，并受到许多工具和库的支持。

### 纯文本

纯文本文件（通常以 .txt 文件扩展名结尾）。对于纯文本文件，我们将整个文件内容导入为 `text` 字段，而 `title` 始终为文件名。

### 逗号分隔

CSV 文件（通常以 .csv 扩展名结尾）。这些文件使用 pandas 的默认选项通过 [`read_csv` method](https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.read_csv.html) 加载。CSV 文件中的每一行都被视为单个文档。如果你的输入文件夹中有多个 CSV 文件，它们将被串联成一个结果 `documents` DataFrame。

对于 CSV 格式，如果你的数据包含你希望使用的结构化内容，可以配置 `text_column` 和 `title_column`。如果你没有在 settings.yaml 的 `input` 块中配置这些项，那么标题将如上面架构所述为文件名。如果未特别配置，则假定文件中的 `text_column` 为 "text"。如果存在 "id" 列，我们也会查找并使用它；否则将按上述方式生成 ID。

### JSON

JSON 文件（通常以 .json 扩展名结尾）包含[结构化对象](https://www.json.org/)。这些文件使用 python 的 [`json.loads` method](https://docs.python.org/3/library/json.html) 加载，因此你的文件必须严格符合规范。JSON 文件可以在文件中包含单个对象，*或者* 文件根节点可以包含对象数组。我们会检查并处理这两种情况。与 CSV 一样，多个文件将被串联为最终表格，并且 `text_column` 与 `title_column` 配置选项会应用到每个已加载对象的属性上。请注意，一些库生成的专用 jsonl 格式（每行一个完整 JSON 对象，而不是放在数组中）目前尚不支持。

## 元数据

对于结构化文件格式（CSV 和 JSON），你可以配置任意数量的列，将其添加到 DataFrame 中持久化的 `metadata` 字段中。这是通过提供要收集的列名列表来配置的。如果配置了此项，输出的 `metadata` 列将包含一个 dict，其中每一列对应一个键，其值为该文档该列的值。这些元数据随后可以选择性地在 GraphRAG 流水线中使用。

### 示例

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

## 分块与元数据

如 [default dataflow](default_dataflow.md#phase-1-compose-textunits) 页面所述，文档会被 *chunked* 成更小的“文本单元”以便处理。这样做是因为文档内容大小通常会超出给定语言模型可用的上下文窗口。你可以调整少量与此分块相关的设置，其中最重要的是 `chunk_size` 和 `overlap`。我们还支持一种元数据处理方案，它可以改善某些用例的索引结果。下面将详细说明此功能。

设想如下场景：你正在为一组新闻文章建立索引。每篇文章的文本都以标题和作者开头，然后是正文内容。当文档被分块时，它们会根据你配置的块大小均匀切分。换句话说，前 *n* 个 token 会被读入一个文本单元，然后是下一个 *n* 个，直到内容结束。这意味着文档开头的前置信息（例如本例中的标题和作者）*不会被复制到每个块中*。它只存在于第一个块中。当我们之后检索这些块进行摘要时，它们因此可能缺少关于源文档的共享信息，而这些信息本应始终提供给模型。为了解决这个问题，我们提供了将重复内容复制到每个文本单元中的配置选项。

### 输入配置

如上所述，导入文档时，你可以指定一个 `metadata` 列表，将其包含在每一行中。必须配置此项，每块复制功能才能工作。

### 分块配置

接下来，`chunks` 块需要指示分块器在创建文本单元时如何处理这些元数据。默认情况下，它会被忽略。我们提供以下设置来包含它：

- `prepend_metadata`。这会指示导入器将每一行 `metadata` 列的内容复制到每个文本块的开头。这些元数据会以新行上的 key: value 对形式复制。

### 示例

下面给出几个示例，以帮助说明对于每种文件格式，分块配置和元数据前置是如何工作的。请注意，为了说明方便，我们这里将词数作为“tokens”，但语言模型的 token [并不等同于单词](https://help.openai.com/en/articles/4936856-what-are-tokens-and-how-to-count-them)。

#### 文本文件

本示例使用两个独立的新闻文章文本文件。

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
    type: text
    metadata: [title]

chunks:
    size: 100
    overlap: 0
    prepend_metadata: true
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

在此示例中，我们可以看到这两个输入文档被解析成了五个输出文本块。每个文档的标题（文件名）都被前置，但不计入计算出的块大小。还要注意，每个文档的最后一个文本块通常会小于块大小，因为它包含的是最后一批 token。

#### CSV 文件

本示例使用单个 CSV 文件，其中两行是与上面相同的两篇文章（请注意，文本内容并未针对实际 CSV 使用进行正确转义）。

--

**File:** articles.csv

**Content**

headline,article

US to lift most federal COVID-19 vaccine mandates,WASHINGTON (AP) The Biden administration will end most of the last remaining federal COVID-19 vaccine requirements next week when the national public health emergency for the coronavirus ends, the White House said Monday. Vaccine requirements for federal workers and federal contractors, as well as foreign air travelers to the U.S., will end May 11. The government is also beginning the process of lifting shot requirements for Head Start educators, healthcare workers, and noncitizens at U.S. land borders. The requirements are among the last vestiges of some of the more coercive measures taken by the federal government to promote vaccination as the deadly virus raged, and their end marks the latest display of how President Joe Biden's administration is moving to treat COVID-19 as a routine, endemic illness. "While I believe that these vaccine mandates had a tremendous beneficial impact, we are now at a point where we think that it makes a lot of sense to pull these requirements down," White House COVID-19 coordinator Dr. Ashish Jha told The Associated Press on Monday.

NY lawmakers begin debating budget 1 month after due date,ALBANY, N.Y. (AP) New York lawmakers began voting Monday on a $229 billion state budget due a month ago that would raise the minimum wage, crack down on illicit pot shops and ban gas stoves and furnaces in new buildings. Negotiations among Gov. Kathy Hochul and her fellow Democrats in control of the Legislature dragged on past the April 1 budget deadline, largely because of disagreements over changes to the bail law and other policy proposals included in the spending plan. Floor debates on some budget bills began Monday. State Senate Majority Leader Andrea Stewart-Cousins said she expected voting to be wrapped up Tuesday for a budget she said contains "significant wins" for New Yorkers. "I would have liked to have done this sooner. I think we would all agree to that," Cousins told reporters before voting began. "This has been a very policy-laden budget and a lot of the policies had to parsed through." Hochul was able to push through a change to the bail law that will eliminate the standard that requires judges to prescribe the "least restrictive" means to ensure defendants return to court. Hochul said judges needed the extra discretion. Some liberal lawmakers argued that it would undercut the sweeping bail reforms approved in 2019 and result in more people with low incomes and people of color in pretrial detention. Here are some other policy provisions that will be included in the budget, according to state officials. The minimum wage would be raised to $17 in New York City and some of its suburbs and $16 in the rest of the state by 2026. That's up from $15 in the city and $14.20 upstate.

#### JSON 文件

最后这个示例对同样两篇文章中的每一篇使用一个 JSON 文件。在本示例中，我们将设置要读取的对象字段，但不会向文本块中添加元数据。

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
    type: json
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


在此示例中，这两个输入文档被解析成了五个输出文本块。没有前置任何元数据，因此每个块都与配置的块大小匹配（每个文档最后一个块除外）。我们还在这些文本块中配置了一些重叠，因此最后十个 token 是共享的。