import logging
import markdown
from weasyprint import HTML, CSS

logger = logging.getLogger("nb2pdf.pdf_gen")

CSS_STYLE = """
@page {
    size: A4;
    margin: 2cm;
}

body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif, "Apple Color Emoji", "Segoe UI Emoji", "Segoe UI Symbol";
    color: #1a202c;
    line-height: 1.6;
}

h1, h2, h3 {
    color: #2d3748;
    border-bottom: 2px solid #edf2f7;
    padding-bottom: 0.3em;
    margin-top: 1.5em;
}

pre {
    background-color: #f7fafc;
    padding: 1.2em;
    border-radius: 8px;
    overflow-x: auto;
    border: 1px solid #e2e8f0;
    box-shadow: inset 0 2px 4px 0 rgba(0, 0, 0, 0.04);
}

code {
    font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;
    font-size: 0.9em;
    color: #4a5568;
}

blockquote {
    border-left: 4px solid #4299e1;
    background-color: #ebf8ff;
    padding: 0.75em 1.25em;
    margin: 1.5em 0;
    color: #2b6cb0;
    border-radius: 0 8px 8px 0;
    font-style: italic;
}

img {
    max-width: 100%;
    height: auto;
    border-radius: 6px;
    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    margin: 1.5em 0;
    display: block;
}

hr {
    border: 0;
    height: 1px;
    background: #e2e8f0;
    margin: 2em 0;
}
"""

def generate_pdf(markdown_content: str, output_path: str):
    """Converts a Markdown string to a polished PDF document using WeasyPrint."""
    try:
        # Convert MD to HTML
        # Using standard extensions to support code blocks and tables
        html_content = markdown.markdown(
            markdown_content, 
            extensions=['fenced_code', 'tables']
        )
        
        # Wrap in basic HTML structure
        html_doc = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
        </head>
        <body>
            {html_content}
        </body>
        </html>
        """
        
        # Render PDF
        logger.info(f"Rendering PDF to {output_path}...")
        HTML(string=html_doc).write_pdf(
            output_path, 
            stylesheets=[CSS(string=CSS_STYLE)]
        )
        logger.info(f"Successfully created: {output_path}")
    except Exception as e:
        logger.error(f"Failed to generate PDF: {e}")
        raise
