import typer
from typing import List, Optional
from collections import namedtuple

app = typer.Typer()

from . import gitdriver

Opts = namedtuple('opts', ['docid', 'config', 'mime_types', 'all_types', 'exclude_types', 'raw', 'markdown'])

@app.command()
def main_gitdriver(
        # which document
        docid: str = typer.Argument(..., help='The document identifier (copy from URL)'),
        # authorisation
        config: str = typer.Option('gd.conf', help='Path to configuration file'),
        # mime settings
        text_type: bool = typer.Option(False, '--text', '-T', help='Download text/plain'),
        html_type: bool = typer.Option(False, '--html', '-H', help='Download text/html'),
        mime_types: List[str] = typer.Option([], help='MIME types to download'),
        all_types: bool = typer.Option(False, '--all', '-A', help='Export all available MIME types'),
        exclude_types: Optional[List[str]] = typer.Option([], '--exclude-type', '-E', help='MIME types to exclude'),
        raw: bool = typer.Option(False, '--raw', '-R', help='Download original file if possible. This will work for files that are not Google Docs files (custom extensions).'),
        # conversion settings
        # convert_to: Optional[str] = typer.Option(False, '--convert-to', '-C', help='Convert to')
        markdown: bool = typer.Option(False, '--markdown', '-M', help='Convert to markdown')
        ):
    if text_type:
        mime_types.append('text/plain')
    if html_type:
        mime_types.append('text/html')
    if markdown:
        mime_types.append('text/html')
    opts = Opts(docid=docid,
                config=config,
                mime_types=mime_types,
                all_types=all_types,
                exclude_types=exclude_types,
                raw=raw,
                markdown=markdown)
    gitdriver.main(opts)

if __name__ == "__main__":
    app()