import click

@click.group()
@click.version_option()
def main():
    """claiw: A supercharged agent workflow CLI."""
    pass

@main.command()
def hello():
    """Prints a hello message."""
    click.echo("Hello from claiw!")

if __name__ == "__main__":
    main()
