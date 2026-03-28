import sys
import warnings
from pathlib import Path

# Suppress Pydantic V1 warnings from LangChain on Python 3.14+
warnings.filterwarnings("ignore", category=UserWarning, module="langchain_core")
warnings.filterwarnings("ignore", message=".*Core Pydantic V1.*")

# Add src directory to PYTHONPATH automatically
sys.path.insert(0, str(Path(__file__).parent / "src"))

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Prompt
from rich.panel import Panel

from parser import parse_notebook
from analyzer import analyze_notebook
from formatter import format_as_markdown
from pdf_gen import generate_pdf

app = typer.Typer(
    name="notebook-converter",
    help="󰐩 Convert Jupyter Notebooks to polished, AI-enhanced PDF reports.",
    add_completion=False,
    invoke_without_command=True
)

console = Console()

@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    input_file: str = typer.Argument(None, help="Path to the .ipynb file"),
    output_file: str = typer.Option(None, "--output", "-o", help="Path for the output .pdf file"),
    no_ai: bool = typer.Option(False, "--no-ai", help="Disable AI enhancements and include all cells as-is")
):
    """
    Intelligently compile a Jupyter Notebook into a professional PDF report.
    """
    # Display the new beautiful header
    console.print()
    console.print(Panel.fit(
        "[bold cyan]󰒋 Notebook Converter[/bold cyan]\n[dim]AI-Powered Jupyter to PDF formatting tool[/dim]",
        border_style="cyan",
        padding=(1, 4)
    ))
    console.print()
    
    # Interactive mode logic
    if input_file is None:
        input_file = Prompt.ask("[bold green] Please enter the path to the Jupyter Notebook (.ipynb) file[/bold green]")
        
    input_path = Path(input_file.strip("'\" "))
    
    if not input_path.exists():
        console.print(f"\n[bold red]󰅖 Error:[/] File '{input_path}' does not exist.")
        raise typer.Exit(1)
        
    if input_path.suffix != '.ipynb':
        console.print(f"\n[bold yellow] Warning:[/] Expected a Jupyter Notebook file (.ipynb), but got {input_path.suffix}")
        
    if not output_file:
        output_path = input_path.with_suffix(".pdf")
    else:
        output_path = Path(output_file.strip("'\" "))
        
    # Info panel
    console.print(f"[bold blue] Task Configuration[/bold blue]")
    console.print(f"  󰈙 [dim]Input:[/]  {input_path}")
    console.print(f"  󰓎 [dim]Output:[/] {output_path}")
    console.print(f"  󰚯 [dim]AI Mode:[/] {'[bold red]Disabled[/bold red]' if no_ai else '[bold green]Enabled (Groq LangChain)[/bold green]'}\n")
    
    try:
        with Progress(
            SpinnerColumn(spinner_name="dots12", style="bold cyan"),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            
            # Step 1: Parsing
            task1 = progress.add_task("[cyan]󰏘 Parsing notebook...", total=None)
            notebook = parse_notebook(str(input_path))
            progress.update(task1, description=f"[bold green]󰄬[/bold green] [green]Parsed notebook ({len(notebook.cells)} cells)[/green]")
            progress.stop_task(task1)
            
            # Step 2: AI Analysis
            task2 = progress.add_task(f"[cyan]󰚩 Analyzing content with AI...", total=None)
            analyzed_cells = analyze_notebook(notebook, use_ai=not no_ai)
            skipped = sum(1 for c in analyzed_cells if c.action == "SKIP")
            summarized = sum(1 for c in analyzed_cells if c.action == "SUMMARIZE")
            progress.update(task2, description=f"[bold green]󰄬[/bold green] [green]Analyzed content ([dim]Skipped: {skipped}, Summarized: {summarized}[/dim])[/green]")
            progress.stop_task(task2)
            
            # Step 3: Formatting
            task3 = progress.add_task("[cyan]󰐩 Structuring Markdown document...", total=None)
            md_content = format_as_markdown(analyzed_cells, title=input_path.stem.replace("_", " ").title())
            progress.update(task3, description="[bold green]󰄬[/bold green] [green]Structured Markdown document[/green]")
            progress.stop_task(task3)
            
            # Step 4: PDF Generation
            task4 = progress.add_task("[cyan] Rendering PDF layout...", total=None)
            generate_pdf(md_content, str(output_path))
            progress.update(task4, description="[bold green]󰄬[/bold green] [green]Rendered final PDF report[/green]")
            progress.stop_task(task4)
            
        console.print(f"\n[bold green]󰗠 Success![/] PDF report generated at [underline]{output_path}[/underline]\n")

    except Exception as e:
        console.print(f"\n[bold red]󰅖 Fatal Error:[/] {e}")
        import traceback
        console.print(traceback.format_exc(), style="dim red")
        raise typer.Exit(1)

if __name__ == "__main__":
    app()
