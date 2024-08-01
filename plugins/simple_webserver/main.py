import logging
from fastapi import FastAPI

from plugins.simple_webserver import utils
from plugins.simple_webserver.models import GraphRAGResponseItem, GraphRAGItem

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = FastAPI()


@app.get("/")
def read_root():
    return "GraphRag API is running!"


@app.post("/graphrag", response_model=GraphRAGResponseItem)
def run(item: GraphRAGItem):
    cli = f"python -m graphrag.query --root ./ragtest --response_type '{item.response_type}' --method {item.method.value} '{item.question}'"
    logger.info(f"Running graphrag by CLI: {cli} ...")
    run_code, show_output, all_output = utils.run_script(cli, item.method)
    if run_code == 0:
        logger.debug(f"Response Content:\n{''.join(all_output)}")
        logger.info(f"Run graphrag successfully")

        pure_show_output, all_data_source = utils.extract_data_source(show_output)

        return GraphRAGResponseItem(code=200, message="success", data=pure_show_output, other={'data_source': all_data_source, 'all_output': all_output})
    else:
        return GraphRAGResponseItem(code=204, message="fail to run graphrag", data=[], other={'all_output': all_output})


if __name__ == '__main__':
    import uvicorn

    uvicorn.run(app, host="localhost", port=8000)
