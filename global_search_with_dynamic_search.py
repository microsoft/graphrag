import os

from graphrag.query.cli import run_global_search

if __name__ == "__main__":
    run_global_search(
        config_filepath=None,
        data_dir="examples_notebooks/inputs/podcast",
        root_dir=os.getcwd(),
        community_level=2,
        dynamic_selection=True,
        response_type="Multiple Paragraphs",
        streaming=False,
        query="Are there any common educational or career paths among the guests?",
    )
