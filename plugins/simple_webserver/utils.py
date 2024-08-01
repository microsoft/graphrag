import os
import re
import subprocess

from plugins.simple_webserver.models import GraphRAGItem


def run_script(cli: str, mode: GraphRAGItem.MethodEnum):
    """
    Run script with CLI command and mode.
    Args:
        cli: CLI command
        mode: Mode enum
    Returns:
        rc: Return code
        show_output: List of output to show
        all_output: List of all output
    """
    process = subprocess.Popen(cli, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True, text=True, env=os.environ)
    flag_begin_output = False
    all_output = []
    show_output = []
    while True:
        output = process.stdout.readline()
        all_output.append(output)
        if output == "" and process.poll() is not None:
            break
        if output and 'SUCCESS' in output:
            flag_begin_output = True
        if flag_begin_output:
            prefix_str = f'SUCCESS: {mode.value.capitalize()} Search Response:'
            result = output.replace(prefix_str, '')
            result = result.strip()
            if result:
                show_output.append(result)

    rc = process.poll()
    return rc, show_output, all_output


def extract_data_source(output: list[str]):
    """
    Extract data source from output.
    Args:
        output: List of output
    Returns:
        pure_output: List of pure output

        all_data_source: List of data source
    """
    all_data_source = []
    pure_output = []
    re_pattern = re.compile(r"\[Data: .*?\]")
    for idx, row in enumerate(output):
        if re_result := re_pattern.search(row):
            extract_data = re_result.group()
            all_data_source.append({'idx_in_data': idx, 'source': extract_data})
            row = re_pattern.sub('', row, count=1)
        pure_output.append(row)

    return pure_output, all_data_source
