"""Page export functionality for HTML, Markdown, and PDF formats."""

from __future__ import annotations

from pathlib import Path
from datetime import datetime
from typing import Optional

import html2text
from weasyprint import HTML as WeasyHTML


class PageExporter:
    """Handle exporting web pages to various formats."""

    def __init__(self, output_dir: Optional[Path] = None):
        """Initialize the exporter.
        
        Args:
            output_dir: Directory to save exports. Defaults to ~/Downloads
        """
        if output_dir is None:
            self.output_dir = Path.home() / "Downloads"
        else:
            self.output_dir = Path(output_dir)
        
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def _generate_filename(self, url: str, extension: str) -> Path:
        """Generate a filename based on URL and current timestamp.
        
        Args:
            url: The page URL
            extension: File extension (e.g., 'html', 'md', 'pdf')
            
        Returns:
            Path object for the output file
        """
        # Clean URL for filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Extract a clean name from URL
        if url.startswith("data:"):
            base_name = "page"
        else:
            # Remove protocol and clean up
            clean_url = url.replace("https://", "").replace("http://", "")
            clean_url = clean_url.replace("/", "_").replace("?", "_").replace("&", "_")
            # Truncate to reasonable length
            clean_url = clean_url[:50]
            base_name = clean_url or "page"
        
        filename = f"{base_name}_{timestamp}.{extension}"
        return self.output_dir / filename

    def export_html(self, html_content: str, url: str) -> Path:
        """Export page as HTML snapshot.
        
        Args:
            html_content: The HTML content to save
            url: The page URL (for filename generation)
            
        Returns:
            Path to the saved file
        """
        output_path = self._generate_filename(url, "html")
        
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html_content)
        
        return output_path

    def export_markdown(self, html_content: str, url: str) -> Path:
        """Export page as Markdown.
        
        Args:
            html_content: The HTML content to convert
            url: The page URL (for filename generation and metadata)
            
        Returns:
            Path to the saved file
        """
        # Configure html2text
        h = html2text.HTML2Text()
        h.ignore_links = False
        h.ignore_images = False
        h.ignore_emphasis = False
        h.body_width = 0  # Don't wrap lines
        
        # Convert HTML to Markdown
        markdown_content = h.handle(html_content)
        
        # Add metadata header
        header = f"# Exported from: {url}\n"
        header += f"# Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        markdown_content = header + markdown_content
        
        output_path = self._generate_filename(url, "md")
        
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(markdown_content)
        
        return output_path

    def export_pdf(self, html_content: str, url: str) -> Path:
        """Export page as PDF.
        
        Args:
            html_content: The HTML content to convert
            url: The page URL (for filename generation)
            
        Returns:
            Path to the saved file
        """
        output_path = self._generate_filename(url, "pdf")
        
        # Create PDF from HTML
        # Note: WeasyPrint may have issues with some web content
        # (JavaScript, complex CSS, external resources)
        try:
            html_obj = WeasyHTML(string=html_content, base_url=url)
            html_obj.write_pdf(output_path)
        except Exception as e:
            # Fallback: create a simpler HTML version
            simple_html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <title>Exported Page</title>
                <style>
                    body {{ font-family: sans-serif; max-width: 800px; margin: 40px auto; }}
                    h1 {{ color: #333; }}
                    .error {{ color: red; margin: 20px 0; }}
                </style>
            </head>
            <body>
                <h1>Page Export</h1>
                <p class="error">Note: Could not render full page due to: {str(e)}</p>
                <p><strong>Source:</strong> {url}</p>
                <p><strong>Date:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                <hr>
                <div>
                    {html_content}
                </div>
            </body>
            </html>
            """
            html_obj = WeasyHTML(string=simple_html)
            html_obj.write_pdf(output_path)
        
        return output_path
