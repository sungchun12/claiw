import logging
from rich.logging import RichHandler

def setup_logging(level: str = "INFO", verbose: bool = False):
    """
    Configures the application logging to use Rich for beautiful, ergonomic output.
    """
    if verbose:
        level = "DEBUG"

    # Configure the root logger
    logging.basicConfig(
        level=level,
        format="%(message)s",
        datefmt="[%X]",
        handlers=[
            RichHandler(
                rich_tracebacks=True,  # Pretty print exceptions
                markup=True,           # Allow rich markup in logs
                show_path=True,        # Show file path (ergonomic for debugging)
                show_time=True         # Show timestamp
            )
        ],
        force=True  # Override any existing configuration (important for DBOS compatibility)
    )
    
    # Optional: Suppress overly verbose libraries if needed
    # logging.getLogger("some_noisy_lib").setLevel(logging.WARNING)

    # 👇 Add this to silence DBOS startup noise
    if not verbose:
        logging.getLogger("dbos").setLevel(logging.WARNING)
