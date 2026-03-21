"""
CrawlKit CLI — Command-line interface.

Usage:
    crawlkit scrape <url> [--parser tvpl] [--format json] [--chunk]
    crawlkit batch urls.txt [--output data/] [--delay 2]
    crawlkit discover tvpl --query "Doanh-nghiep" --limit 100
"""

from __future__ import annotations
import sys
import json
import click
import orjson

from .core.crawler import CrawlKit


@click.group()
@click.version_option(version="0.1.0", prog_name="crawlkit")
def main():
    """CrawlKit — Vietnamese Web Intelligence API"""
    pass


@main.command()
@click.argument("url")
@click.option("--parser", "-p", default=None, help="Force parser (tvpl, vbpl, vnexpress, batdongsan, cafef)")
@click.option("--format", "-f", "output_format", default="json", type=click.Choice(["json", "markdown", "text", "jsonl"]))
@click.option("--chunk/--no-chunk", default=True, help="Enable RAG chunking")
@click.option("--chunk-size", default=512, help="Max tokens per chunk")
@click.option("--js/--no-js", "force_js", default=False, help="Force JS rendering")
@click.option("--static/--no-static", "force_static", default=False, help="Force static fetch")
@click.option("--pretty/--compact", default=True, help="Pretty print JSON")
@click.option("--output", "-o", default=None, help="Output file (default: stdout)")
def scrape(url, parser, output_format, chunk, chunk_size, force_js, force_static, pretty, output):
    """Scrape a URL and extract structured data."""
    crawler = CrawlKit(auto_chunk=chunk, chunk_max_tokens=chunk_size)
    
    click.echo(f"🦐 Crawling {url}...", err=True)
    result = crawler.scrape(url, parser=parser, force_js=force_js, force_static=force_static)
    
    if result.error:
        click.echo(f"❌ Error: {result.error}", err=True)
        sys.exit(1)
    
    click.echo(
        f"✅ {result.title[:60]} | {result.content_length:,} chars | "
        f"{len(result.chunks)} chunks | {result.crawl_time_ms}ms | "
        f"parser={result.parser_used} | type={result.content_type}",
        err=True,
    )
    
    # Format output
    if output_format == "json":
        data = orjson.dumps(result.to_dict(), option=orjson.OPT_INDENT_2 if pretty else 0)
        _output(data.decode(), output)
    elif output_format == "markdown":
        _output(result.markdown, output)
    elif output_format == "text":
        _output(result.text, output)
    elif output_format == "jsonl":
        lines = result.to_jsonl_rows()
        _output("\n".join(l.decode() for l in lines), output)


@main.command()
@click.argument("file", type=click.Path(exists=True))
@click.option("--parser", "-p", default=None)
@click.option("--output", "-o", default="output", help="Output directory")
@click.option("--delay", default=1.5, help="Delay between requests (seconds)")
@click.option("--format", "-f", "output_format", default="json", type=click.Choice(["json", "jsonl"]))
def batch(file, parser, output, delay, output_format):
    """Batch scrape URLs from a file."""
    import os
    
    with open(file) as f:
        urls = [line.strip() for line in f if line.strip() and not line.startswith("#")]
    
    click.echo(f"🦐 Batch scraping {len(urls)} URLs...", err=True)
    
    os.makedirs(output, exist_ok=True)
    crawler = CrawlKit()
    
    results = crawler.batch_scrape(urls, parser=parser, delay=delay)
    
    success = sum(1 for r in results if r.success)
    click.echo(f"✅ Done: {success}/{len(results)} successful", err=True)
    
    if output_format == "json":
        # Save individual files
        for i, result in enumerate(results):
            if result.success:
                filename = f"{output}/{i:04d}_{_slugify(result.title[:50])}.json"
                with open(filename, "wb") as f:
                    f.write(result.to_json(pretty=True))
                click.echo(f"  💾 {filename}", err=True)
    elif output_format == "jsonl":
        # Save as single JSONL file
        filename = f"{output}/data.jsonl"
        with open(filename, "w") as f:
            for result in results:
                if result.success:
                    for row in result.to_jsonl_rows():
                        f.write(row.decode() + "\n")
        click.echo(f"  💾 {filename}", err=True)


@main.command()
@click.argument("source")
@click.option("--query", "-q", default=None, help="Search query")
@click.option("--limit", default=100, help="Max URLs to discover")
def discover(source, query, limit):
    """Discover URLs from a source (tvpl, vnexpress, batdongsan)."""
    crawler = CrawlKit()
    
    click.echo(f"🔍 Discovering URLs from {source}...", err=True)
    
    try:
        urls = crawler.discover(source, query=query, limit=limit)
        click.echo(f"✅ Found {len(urls)} URLs", err=True)
        
        for u in urls:
            click.echo(u["url"])
    except Exception as e:
        click.echo(f"❌ {e}", err=True)
        sys.exit(1)


def _output(text: str, filepath: str | None):
    """Write to file or stdout."""
    if filepath:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(text)
        click.echo(f"💾 Saved to {filepath}", err=True)
    else:
        click.echo(text)


def _slugify(text: str) -> str:
    """Simple slugify for filenames."""
    import re
    text = re.sub(r'[^\w\s-]', '', text.lower())
    text = re.sub(r'[\s_]+', '-', text)
    return text.strip("-")[:50]


if __name__ == "__main__":
    main()
