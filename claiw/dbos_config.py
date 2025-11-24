from dbos import DBOS, DBOSConfig

def get_dbos_config() -> DBOSConfig:
    return {
        'name': 'claiw-runtime',
        'system_database_url': 'sqlite:///dbostest.sqlite', 
        'log_level': 'WARNING',
    }

def configure_dbos():
    """Configure DBOS without launching it."""
    # This sets the singleton config so agents can register themselves
    DBOS(config=get_dbos_config())

def launch_dbos():
    """Launch the runtime (must happen AFTER agents are imported)."""
    DBOS.launch()
