from typing import List
from analyzer import AnalyzedCell

def format_as_markdown(analyzed_cells: List[AnalyzedCell], title: str = "Notebook Report") -> str:
    """Takes a list of analyzed cells and converts them to a cohesive Markdown document."""
    md_lines = [
        f"# {title}\n",
        "---\n\n"
    ]
    
    for cell in analyzed_cells:
        if cell.action == "SKIP":
            continue
            
        if cell.action == "SUMMARIZE":
            md_lines.append(f"> **Summary:** *{cell.explanation}*\n")
            continue
            
        # Action is INCLUDE
        source = cell.original_cell.source
        
        if cell.explanation:
             md_lines.append(f"> **AI Note:** *{cell.explanation}*\n")
             
        if cell.original_cell.cell_type == "markdown":
            md_lines.append(source)
            md_lines.append("\n")
        elif cell.original_cell.cell_type == "code":
            # Add Source
            md_lines.append("```python")
            md_lines.append(source)
            md_lines.append("```\n")
            
            # Add Outputs
            for out in cell.original_cell.outputs:
                if out.output_type == "stream":
                    md_lines.append("**Output:**")
                    md_lines.append("```text")
                    md_lines.append(out.text)
                    md_lines.append("```\n")
                elif out.output_type == "error":
                    md_lines.append(f"**Error [{out.error_name}]:**")
                    md_lines.append("```text")
                    md_lines.append(out.error_value)
                    md_lines.append("```\n")
                elif out.output_type in ("display_data", "execute_result"):
                    # Check for image first
                    if out.data and "image/png" in out.data:
                        b64_data = out.data["image/png"]
                        # Clean up formatting if it's multiple lines
                        b64_data = b64_data.replace('\\n', '').replace('\n', '')
                        md_lines.append(f"![Output Plot](data:image/png;base64,{b64_data})\n")
                    elif out.text: # Fallback to text
                        md_lines.append("**Result:**")
                        md_lines.append("```text")
                        md_lines.append(out.text)
                        md_lines.append("```\n")
                        
    return "\n".join(md_lines)
