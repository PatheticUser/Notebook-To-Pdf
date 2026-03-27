import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from pathlib import Path

from parser import parse_notebook
from analyzer import analyze_notebook
from formatter import format_as_markdown
from pdf_gen import generate_pdf

app = typer.Typer(
    name="nb2pdf",
    help="Convert Jupyter Notebooks to polished, AI-enhanced PDF reports.",
    add_completion=False
)

console = Console()

@app.command()
def main(
    input_file: Path = typer.Argument(..., help="Path to the .ipynb file"),
    output_file: Path = typer.Option(None, "--output", "-o", help="Path for the output .pdf file"),
    no_ai: bool = typer.Option(False, "--no-ai", help="Disable AI enhancements and include all cells as-is")
):
    """
    Intelligently compile a Jupyter Notebook into a professional PDF report.
    """
    if not input_file.exists():
        console.print(f"[bold red]Error:[/] File '{input_file}' does not exist.")
        raise typer.Exit(1)
        
    if not output_file:
        output_file = input_file.with_suffix(".pdf")
        
    console.print(f"\n[bold blue]nb2pdf[/] | [dim]Compiling {input_file.name} to {output_file.name}[/]\n")
    
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            
            # Step 1: Parsing
            task1 = progress.add_task("[cyan]Parsing notebook...", total=None)
            notebook = parse_notebook(str(input_file))
            progress.update(task1, description=f"[green]✔ Parsed notebook ({len(notebook.cells)} cells)[/]")
            progress.stop_task(task1)
            
            # Step 2: AI Analysis
            task2 = progress.add_task(f"[cyan]Analyzing content with AI intelligence (mode={'fallback' if no_ai else 'Groq LLM'})...", total=None)
            analyzed_cells = analyze_notebook(notebook, use_ai=not no_ai)
            skipped = sum(1 for c in analyzed_cells if c.action == "SKIP")
            summarized = sum(1 for c in analyzed_cells if c.action == "SUMMARIZE")
            progress.update(task2, description=f"[green]✔ Analyzed content (Skipped: {skipped}, Summarized: {summarized})[/]")
            progress.stop_task(task2)
            
            # Step 3: Formatting
            task3 = progress.add_task("[cyan]Structuring document...", total=None)
            md_content = format_as_markdown(analyzed_cells, title=input_file.stem.replace("_", " ").title())
            progress.update(task3, description="[green]✔ Structured document[/]")
            progress.stop_task(task3)
            
            # Step 4: PDF Generation
            task4 = progress.add_task("[cyan]Rendering PDF...", total=None)
            generate_pdf(md_content, str(output_file))
            progress.update(task4, description="[green]✔ Rendered PDF[/]")
            progress.stop_task(task4)
            
        console.print(f"\n[bold green]Success![/] PDF report generated at [underline]{output_file}[/]\n")

    except Exception as e:
        console.print(f"\n[bold red]Fatal Error:[/] {e}")
        import traceback
        console.print(traceback.format_exc(), style="dim red")
        raise typer.Exit(1)

if __name__ == "__main__":
    app()
