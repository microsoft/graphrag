import streamlit as st
import subprocess
from loguru import logger


def run_script(cli, mode: str):
    process = subprocess.Popen(cli, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True, text=True)
    flag_begin_output = False
    all_output = []
    while True:
        output = process.stdout.readline()
        all_output.append(output)
        if output == "" and process.poll() is not None:
            break
        if output and 'SUCCESS' in output:
            flag_begin_output = True
        if flag_begin_output:
            prefix_str = f'SUCCESS: {mode.capitalize()} Search Response:'
            result = output.strip()
            result = result.replace(prefix_str, '')
            yield result.strip()

    rc = process.poll()
    logger.info(f"Return code: {rc}")
    logger.info("\n".join(all_output))
    return rc


def app():
    st.title("GraphRAG")
    mode = st.selectbox("Running Mode", ["local", "global"], index=0,
                        help="Local mode is used for running queries on a local search engine.\n\nGlobal mode is used for running queries on a global search engine.")
    output_mode = st.text_input("Output Mode",
                                help="Free form text describing the response type and format, can be anything.\n\ne.g. Multiple Paragraphs, Single Paragraph, Single Sentence, List of 3-7 Points, Single Page, Multi-Page Report",
                                value="Multiple Paragraphs")
    question = st.text_input("Question")
    if st.button("Run"):
        if question:
            cli = f"python -m graphrag.query --root ./ragtest --response_type '{output_mode}' --method {mode} '{question}'"

            for log in run_script(cli, mode):
                st.write(log)


if __name__ == "__main__":
    app()
