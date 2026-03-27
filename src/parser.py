import nbformat
from pydantic import BaseModel
from typing import List, Optional, Any, Dict

class CellOutput(BaseModel):
    output_type: str
    text: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    error_name: Optional[str] = None
    error_value: Optional[str] = None

class NotebookCell(BaseModel):
    index: int
    cell_type: str
    source: str
    execution_count: Optional[int] = None
    outputs: List[CellOutput] = []

class ParsedNotebook(BaseModel):
    filename: str
    metadata: Dict[str, Any]
    cells: List[NotebookCell]

def parse_notebook(filepath: str) -> ParsedNotebook:
    """Read a Jupyter notebook and serialize it into a strongly typed Pydantic model."""
    with open(filepath, "r", encoding="utf-8") as f:
        nb = nbformat.read(f, as_version=4)
        
    parsed_cells: List[NotebookCell] = []
    
    for i, cell in enumerate(nb.cells):
        outputs = []
        if cell.cell_type == "code" and hasattr(cell, 'outputs'):
            for out in cell.outputs:
                if out.output_type == "stream":
                    outputs.append(CellOutput(output_type="stream", text=out.text))
                elif out.output_type in ("execute_result", "display_data"):
                    # Extract plain text representation and raw data dict (for images)
                    data = out.data
                    text_repr = data.get("text/plain", "")
                    outputs.append(CellOutput(
                        output_type=out.output_type, 
                        text=text_repr, 
                        data=dict(data) # converts NotebookNode dict-like to actual dict
                    ))
                elif out.output_type == "error":
                    outputs.append(CellOutput(
                        output_type="error",
                        error_name=out.ename,
                        error_value=out.evalue
                    ))
        
        parsed_cells.append(NotebookCell(
            index=i,
            cell_type=cell.cell_type,
            source=cell.source,
            execution_count=cell.get("execution_count"),
            outputs=outputs
        ))
        
    return ParsedNotebook(
        filename=filepath,
        metadata=dict(nb.get("metadata", {})),
        cells=parsed_cells
    )
