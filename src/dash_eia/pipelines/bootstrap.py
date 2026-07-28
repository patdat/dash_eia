from dash_eia.config.paths import WorkspacePaths


def run(paths: WorkspacePaths) -> int:
    for directory in paths.required_directories:
        directory.mkdir(parents=True, exist_ok=True)
    return 0
