from getpass import getpass
import os
import traceback
import click


def prompt_password(prompt: str):
    """Prompt the user for a hidden password"""
    return os.getenv("PASSWORD") or getpass(prompt)


def prompt(prompt: str):
    """Prompt the user for input"""
    return click.prompt(click.style(prompt, fg="bright_white"), type=str)


def info(message: str, *rest):
    """Display an informational message to the console"""
    for r in rest:
        message += f" {r}"
    click.echo(click.style("\n" + message, fg="green", bold=True))


def error(message: str | Exception, *rest, debug: bool = False):
    """Display an error message to the console"""
    if isinstance(message, Exception):
        message = str(message)
    for r in rest:
        message += f" {r}"
    click.echo(click.style(message + "\n", fg="red", bold=True))
    if debug and isinstance(message, Exception):
        click.echo("\n" + "".join(traceback.format_exception(None, message, message.__traceback__)))


def log(message: str, *rest, file=None):
    """Log a message to the console"""
    for r in rest:
        message += f" {r}"

    click.echo(click.style(message, bold=True), file=file)


def debug(message: str, *rest):
    """Log a debug message to the console"""
    for r in rest:
        message += f" {r}"

    click.echo(click.style(message, bold=True, fg="yellow"))


def box(*lines: str, block: bool = False):
    """Display a message in a box, optionally blocking until the user presses Enter"""
    if not lines:
        return

    # Handle multiline strings
    alllines = []
    for line in lines:
        alllines.extend(line.split("\n"))
    lines = alllines

    w = max(map(len, lines)) + 4
    click.echo("\n┏" + "━" * w + "┓")
    for line in lines:
        click.echo(f"┃  {line.ljust(w - 4)}  ┃")
    if block:
        click.echo("Press Enter to continue")
    click.echo("┗" + "━" * w + "┛\n")

    if block:
        input()
