import json
import logging
from typing import List
from pydantic import BaseModel

from parser import ParsedNotebook, NotebookCell
from llm_manager import call_llm

logger = logging.getLogger("nb2pdf.analyzer")

class AnalyzedCell(BaseModel):
    original_cell: NotebookCell
    classification: str  # CRITICAL, INFORMATIONAL, TRIVIAL
    action: str          # INCLUDE, SUMMARIZE, SKIP
    explanation: str = ""

def build_prompt(cell: NotebookCell, prev_context: str) -> str:
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
        
    return f"""You are an elite software engineering assistant compiling a high-quality PDF report from a Jupyter Notebook.
Evaluate the following notebook cell and decide how to handle it.

Cell Type: {cell.cell_type}
Source Code/Markdown:
```
{cell.source}
```

Outputs:
{outputs_repr if outputs_repr else "None"}

Previous Context (for continuous reading flow):
{prev_context}

Rules for evaluation:
- TRIVIAL: Boilerplate imports, simple print statements, empty cells, or noisy pip installs. Action: SKIP.
- INFORMATIONAL: Useful context, basic data loading. Action: INCLUDE or SUMMARIZE.
- CRITICAL: Complex models, important plots, core logic, key insights. Action: INCLUDE.

Actions:
- SKIP: Do not include in final document.
- INCLUDE: Keep as is. If the cell is complex code, provide a concise 'explanation' outlining its purpose.
- SUMMARIZE: Replace the literal code/outputs with a clean summary in 'explanation'. Prefer this over repetition.

Output exactly in JSON format:
{{
    "classification": "TRIVIAL" | "INFORMATIONAL" | "CRITICAL",
    "action": "SKIP" | "INCLUDE" | "SUMMARIZE",
    "explanation": "Your concise explanation/summary here (leave empty if not needed)"
}}
"""

def analyze_cell(cell: NotebookCell, prev_context: str = "") -> AnalyzedCell:
    # Fast path for empty cells
    if not cell.source.strip() and not cell.outputs:
        return AnalyzedCell(
            original_cell=cell,
            classification="TRIVIAL",
            action="SKIP"
        )
        
    # If the markdown is just simple text/headings without need for AI filtering, maybe skip LLM?
    # Let's let the LLM decide everything for maximum intelligence as requested.
    
    prompt = build_prompt(cell, prev_context)
    
    try:
        response_text = call_llm(
            messages=[
                {"role": "system", "content": "You are a professional technical writer and data scientist. Output strictly valid JSON without wrapping markdown blocks. Just the JSON object."},
                {"role": "user", "content": prompt}
            ],
            model="llama-3.1-8b-instant" # Fast lightweight model
        )
        
        # Clean response text
        response_text = response_text.strip()
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        elif response_text.startswith("```"):
            response_text = response_text[3:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]
            
        data = json.loads(response_text.strip())
        
        return AnalyzedCell(
            original_cell=cell,
            classification=data.get("classification", "INFORMATIONAL").upper(),
            action=data.get("action", "INCLUDE").upper(),
            explanation=data.get("explanation", "").strip()
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
