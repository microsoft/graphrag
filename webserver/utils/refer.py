import re
from collections import defaultdict
from typing import Set, Dict

from webserver.configs import settings

pattern = re.compile(r'\[Data: ((?:Entities|Relationships|Sources|Claims|Reports) \((?:[\d, ]*[^,])(?:, \+more)?\)('
                     r'?:; )?)+\]')


def get_reference(text: str) -> dict:
    data_dict = defaultdict(set)
    for match in pattern.finditer(text):
        data_blocks = match.group(0)
        inner_pattern = re.compile(r'(Entities|Relationships|Sources|Claims|Reports) \(([\d, ,]*)(?:, \+more)?\)')
        for inner_match in inner_pattern.finditer(data_blocks):
            category = inner_match.group(1)
            numbers = inner_match.group(2).replace(" ", "").split(',')
            data_dict[category].update(map(int, filter(None, numbers)))  # filter to remove empty strings

    return dict(data_dict)


def generate_ref_links(data: Dict[str, Set[int]], index_id: str) -> str:
    base_url = f"{settings.server_host}:{settings.server_port}/v1/references"
    lines = []
    for key, values in data.items():
        for value in values:
            lines.append(f'[{key}: {value}]({base_url}/{index_id}/{key.lower()}/{value})')
    return ", ".join(lines)
