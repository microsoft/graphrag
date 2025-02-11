import re
from dataclasses import dataclass
from pathlib import Path
from typing import List, Dict, Optional, Any
import logging

from graphrag.callbacks.noop_workflow_callbacks import NoopWorkflowCallbacks
from graphrag.config.load_config import load_config
from graphrag.config.models.graph_rag_config import GraphRagConfig
from graphrag.index.llm.load_llm import load_llm
from graphrag.index.operations.chunk_text.agentic_chunker import SemanticChunker


@dataclass
class Element:
    type: str
    content: str
    level: Optional[int] = None
    references: List[str] = None


@dataclass
class Chunk:
    content: List[Element]
    metadata: Dict
    context: Dict


async def handle_oversized_text(
    element: Element,
    config: GraphRagConfig,
    max_length: int = 600,
) -> List[Element]:
    """Run the semantic chunking strategy."""
    llm_config = config.get_language_model_config(
        config.extract_graph.model_id
    )
    llm = load_llm(
        "semantic_chunker",
        llm_config,
        callbacks=NoopWorkflowCallbacks(),
        cache=None
    )
    chunker = SemanticChunker(llm)
    semantic_chunks = await chunker.chunk_large_section(
        element.content,
        max_length
    )

    elements = []
    for chunk in semantic_chunks:
        content = chunk.content
        if chunk.dependencies:
            content = f"/* Required context: {', '.join(chunk.dependencies)} */\n{content}"

        elements.append(Element(
            type='text',
            content=content,
            references=chunk.dependencies
        ))

    return elements

class MarkdownChunker:
    def __init__(self, target_chunk_size: int = 600):
        self.target_chunk_size = target_chunk_size
        self.logger = logging.getLogger(__name__)

    def _create_text_element(self, content: str) -> Element:
        """Create a text element with extracted references."""
        references = []
        # Find references in the text
        figure_refs = re.findall(r'(?:Figure|Image)\s+(?:/\w+/\w+/)?\d+', content)
        table_refs = re.findall(r'Table\s+\d+(?:\.\d+)*', content)
        equation_refs = re.findall(r'Equation\s+\d+(?:\.\d+)*', content)
        references.extend(figure_refs + table_refs + equation_refs)

        return Element(
            type='text',
            content=content,
            references=references if references else None
        )

    def parse_markdown(self, content: str) -> List[Element]:
        elements = []
        lines = content.split('\n')
        current_element = []

        i = 0
        while i < len(lines):
            line = lines[i].strip()

            # Header detection - more strict
            if re.match(r'^#{1,6}\s+\w+', line):
                if current_element:
                    elements.append(self._create_text_element(''.join(current_element)))
                    current_element = []
                level = len(re.match(r'^(#+)', line).group(1))
                elements.append(Element(
                    type='header',
                    content=line,
                    level=level
                ))
                i += 1
                continue

            # Image block detection (includes description)
            if line.startswith('Image'):
                if current_element:
                    elements.append(self._create_text_element(''.join(current_element)))
                    current_element = []

                image_content = [line]
                i += 1
                elements.append(Element(
                    type='image',
                    content='\n'.join(image_content)
                ))
                continue

            # Table detection
            if line.startswith('|') and i + 1 < len(lines) and lines[i+1].strip().startswith('|--'):
                if current_element:
                    elements.append(self._create_text_element(''.join(current_element)))
                    current_element = []
                table_content = [line]
                i += 1
                while i < len(lines) and (lines[i].strip().startswith('|') or not lines[i].strip()):
                    table_content.append(lines[i])
                    i += 1
                elements.append(Element(
                    type='table',
                    content='\n'.join(table_content)
                ))
                continue

            # Quote block detection
            if line.startswith('>'):
                if current_element:
                    elements.append(self._create_text_element(''.join(current_element)))
                    current_element = []
                quote_content = [line]
                i += 1
                while i < len(lines) and (lines[i].strip().startswith('>') or not lines[i].strip()):
                    quote_content.append(lines[i])
                    i += 1
                elements.append(Element(
                    type='quote',
                    content='\n'.join(quote_content)
                ))
                continue

            # List item detection
            list_match = re.match(r'^(?:-|•|\d+\.)\s', line)
            if list_match:
                if current_element:
                    elements.append(self._create_text_element(''.join(current_element)))
                    current_element = []
                list_content = [line]
                i += 1
                while i < len(lines) and (re.match(r'^(?:-|•|\d+\.)\s', lines[i].strip()) or not lines[i].strip()):
                    list_content.append(lines[i])
                    i += 1
                elements.append(Element(
                    type='list',
                    content='\n'.join(list_content)
                ))
                continue

            current_element.append(lines[i] + '\n')
            i += 1

        if current_element:
            elements.append(self._create_text_element(''.join(current_element)))

        return elements

    def identify_semantic_boundaries(self, elements: List[Element]) -> List[int]:
        boundaries = set()

        for i, element in enumerate(elements):
            if element.type == 'header' and i > 0:
                boundaries.add(i)

        return sorted(list(boundaries))

    async def create_chunks(self, elements: List[Element], config: GraphRagConfig) -> List[Chunk]:
        chunks = []
        current_chunk = []
        current_size = 0
        boundaries = self.identify_semantic_boundaries(elements)

        current_context = {
            'chapter': None,
            'section': None,
            'subsection': None
        }

        i = 0
        while i < len(elements):
            element = elements[i]

            # Update context from headers
            if element.type == 'header':
                level = element.level
                if level == 1:
                    current_context['chapter'] = element.content
                elif level == 2:
                    current_context['section'] = element.content
                elif level == 3:
                    current_context['subsection'] = element.content

            element_size = len(element.content.split())

            # Start new chunk at semantic boundary or when size limit hit
            if (i in boundaries or current_size + element_size > self.target_chunk_size) and current_chunk:
                chunks.append(self._create_chunk(current_chunk, current_context))
                current_chunk = []
                current_size = 0

                # Add context headers to new chunk if not at boundary
                if i not in boundaries:
                    for level in range(1, 4):
                        header = self._get_last_header(chunks, level)
                        if header:
                            current_chunk.append(header)
                            current_size += len(header.content.split())

            # Handle oversized elements
            if element_size > self.target_chunk_size:
                if element.type in ['image', 'quote', 'table']:
                    if current_chunk:
                        chunks.append(self._create_chunk(current_chunk, current_context))
                        current_chunk = []
                        current_size = 0
                    chunks.append(self._create_chunk([element], current_context))
                elif element.type == 'text':
                    new_elements = await handle_oversized_text(element, config, self.target_chunk_size, )

                    for new_element in new_elements:
                        element_size = len(new_element.content.split())
                        if current_size + element_size > self.target_chunk_size and current_chunk:
                            chunks.append(self._create_chunk(current_chunk, current_context))
                            current_chunk = []
                            current_size = 0
                        current_chunk.append(new_element)
                        current_size += element_size
                i += 1
                continue
            current_chunk.append(element)
            current_size += element_size
            i += 1

        # Add final chunk
        if current_chunk:
            chunks.append(self._create_chunk(current_chunk, current_context))

        return chunks

    def _create_chunk(self, elements: List[Element], context: Dict) -> Chunk:
        return Chunk(
            content=elements,
            metadata={'size': sum(len(e.content.split()) for e in elements)},
            context=context.copy()
        )

    def _get_last_header(self, chunks: List[Chunk], level: int) -> Optional[Element]:
        """Get the most recent header of given level from previous chunks"""
        for chunk in reversed(chunks):
            for element in reversed(chunk.content):
                if element.type == 'header' and element.level == level:
                    return element
        return None

    def _chunk_to_string(self, chunk: Chunk) -> str:
        return '\n\n'.join(element.content for element in chunk.content)

    async def run_semantic_chunker(self, text: str, config: GraphRagConfig) -> List[str]:
        elements = self.parse_markdown(text)
        chunks = await self.create_chunks(elements, config)
        return [self._chunk_to_string(chunk) for chunk in chunks]