import logging
from typing import List
from pydantic import BaseModel, Field

from parser import ParsedNotebook, NotebookCell
from llm_manager import get_llm
from langchain_core.prompts import ChatPromptTemplate

logger = logging.getLogger("nb2pdf.analyzer")

class LLMAnalysisResult(BaseModel):
    """Evaluation of a Jupyter Notebook cell for PDF inclusion."""
    classification: str = Field(description="One of: TRIVIAL, INFORMATIONAL, CRITICAL")
    action: str = Field(description="One of: SKIP, INCLUDE, SUMMARIZE")
    explanation: str = Field(description="Concise explanation/summary of the cell (leave empty if not needed)", default="")

class AnalyzedCell(BaseModel):
    original_cell: NotebookCell
    classification: str  # CRITICAL, INFORMATIONAL, TRIVIAL
    action: str          # INCLUDE, SUMMARIZE, SKIP
    explanation: str = ""

def build_prompt_vars(cell: NotebookCell, prev_context: str) -> dict:
    outputs_repr = ""
    for out in cell.outputs:
        text = out.text or ""
        # Handle images by just indicating an image exists to save tokens
        if out.data and 'image/png' in out.data:
            text += "[Image Data Present]"
            
        # Truncate text to avoid huge context sizes
        if len(text) > 1000:
            text = text[:1000] + "\n...[truncated]"
            
        outputs_repr += f"[{out.output_type}] {text}\n"
        
    return {
        "cell_type": cell.cell_type,
        "source": cell.source,
        "outputs": outputs_repr if outputs_repr else "None",
        "prev_context": prev_context
    }

prompt_template = ChatPromptTemplate.from_messages([
    ("system", """You are an elite software engineering assistant compiling a high-quality PDF report from a Jupyter Notebook.
Evaluate the following notebook cell and decide how to handle it.

Rules for evaluation:
- TRIVIAL: Boilerplate imports, simple print statements, empty cells, or noisy pip installs. Action: SKIP.
- INFORMATIONAL: Useful context, basic data loading. Action: INCLUDE or SUMMARIZE.
- CRITICAL: Complex models, important plots, core logic, key insights. Action: INCLUDE.

Actions:
- SKIP: Do not include in final document.
- INCLUDE: Keep as is. If the cell is complex code, provide a concise 'explanation' outlining its purpose.
- SUMMARIZE: Replace the literal code/outputs with a clean summary in 'explanation'. Prefer this over repetition."""),
    ("user", """Cell Type: {cell_type}
Source Code/Markdown:
```
{source}
```

Outputs:
{outputs}

Previous Context (for continuous reading flow):
{prev_context}
""")
])

def analyze_cell(cell: NotebookCell, prev_context: str = "") -> AnalyzedCell:
    # Fast path for empty cells
    if not cell.source.strip() and not cell.outputs:
        return AnalyzedCell(
            original_cell=cell,
            classification="TRIVIAL",
            action="SKIP"
        )
        
    prompt_vars = build_prompt_vars(cell, prev_context)
    
    # Get LangChain LLM with structured output
    try:
        llm = get_llm(model="llama-3.1-8b-instant")
        structured_llm = llm.with_structured_output(LLMAnalysisResult)
        chain = prompt_template | structured_llm
        
        result = chain.invoke(prompt_vars)
        
        return AnalyzedCell(
            original_cell=cell,
            classification=result.classification.upper(),
            action=result.action.upper(),
            explanation=result.explanation.strip()
        )
    except Exception as e:
        logger.error(f"Failed to analyze cell {cell.index}: {e}. Defaulting to INCLUDE.")
        return AnalyzedCell(
            original_cell=cell,
            classification="INFORMATIONAL",
            action="INCLUDE",
            explanation=""
        )

def analyze_notebook(parsed_nb: ParsedNotebook, use_ai: bool = True) -> List[AnalyzedCell]:
    analyzed_cells = []
    prev_context = ""
    
    for i, cell in enumerate(parsed_nb.cells):
        if use_ai:
            analyzed = analyze_cell(cell, prev_context)
        else:
            analyzed = AnalyzedCell(
                original_cell=cell,
                classification="INFORMATIONAL",
                action="INCLUDE"
            )
            
        analyzed_cells.append(analyzed)
        
        if analyzed.action != "SKIP":
            ctx_addition = f"Cell {cell.index} ({analyzed.action}): {analyzed.explanation if analyzed.explanation else 'Code included'}"
            prev_context += "\n" + ctx_addition
            if len(prev_context) > 2000:
                prev_context = prev_context[-2000:]
                
    return analyzed_cells
