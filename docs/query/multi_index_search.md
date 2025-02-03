# Multi Index Search 🔎

## Multi Dataset Reasoning

GraphRAG takes in unstructured data contained in text documents and uses large languages models to “read” the documents in a targeted fashion and create a knowledge graph. This knowledge graph, or index, contains information about specific entities in the data, how the entities relate to one another, and high-level reports about communities and topics found in the data. Indexes can be searched by users to get meaningful information about the underlying data, including reports with citations that point back to the original unstructured text. 

Multi-index search is a new capability that has been added to the GraphRAG python library to query multiple knowledge stores at once. Multi-index search allows for many new search scenarios, including: 

- Combining knowledge from different domains – Many documents contain similar types of entities: person, place, thing. But GraphRAG can be tuned for highly specialized domains, such as science and engineering. With the recent updates to search, GraphRAG can now simultaneously query multiple datasets with completely different schemas and entity definitions.

- Combining knowledge with different access levels – Not all datasets are accessible to all people, even within an organization. Some datasets are publicly available. Some datasets, such as internal financial information or intellectual property, may only be accessible by a small number of employees at a company. Multi-index search allows multiple sources with different access controls to be queried at the same time, creating more nuanced and informative reports. Internal R&D findings can be seamlessly combined with open-source scientific publications. 

- Combining knowledge in different locations – With multi-index search, indexes do not need to be in the same location or type of storage to be queried. Indexes in the cloud in Azure Storage can be queried at the same time as indexes stored on a personal computer. Multi-index search makes these types of data joins easy and accessible. 

To search across multiple datasets, the underlying contexts from each index, based on the user query, are combined in-memory at query time, saving on computation and allowing the joint querying of indexes that can’t be joined inherently, either do access controls or differing schemas. Multi-index search automatically keeps track of provenance information, so that any references can be traced back to the correct indexes and correct original documents. 


## How to Use

An example of a global search scenario can be found in the following [notebook](../examples_notebooks/multi_index_search.ipynb).