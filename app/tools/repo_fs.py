from pathlib import Path

from agno import Tool


class ReadFile(Tool):
    """Tool for reading file contents from the repository."""

    name = "read_file"
    description = "Read the contents of a file from the repository"
    parameters = {
        "type": "object",
        "properties": {
            "filepath": {
                "type": "string",
                "description": "Path to the file to read"
            }
        },
        "required": ["filepath"]
    }

    async def run(self, filepath: str) -> str:
        """Read and return file contents."""
        try:
            path = Path(filepath)
            if not path.exists():
                return f"Error: File '{filepath}' not found"

            if not path.is_file():
                return f"Error: '{filepath}' is not a file"

            with open(path, encoding='utf-8') as f:
                content = f.read()

            return f"Contents of {filepath}:\n```\n{content}\n```"
        except Exception as e:
            return f"Error reading file: {str(e)}"


class WriteFile(Tool):
    """Tool for writing content to files in the repository."""

    name = "write_file"
    description = "Write content to a file in the repository"
    parameters = {
        "type": "object",
        "properties": {
            "filepath": {
                "type": "string",
                "description": "Path to the file to write"
            },
            "content": {
                "type": "string",
                "description": "Content to write to the file"
            }
        },
        "required": ["filepath", "content"]
    }

    async def run(self, filepath: str, content: str) -> str:
        """Write content to a file."""
        try:
            path = Path(filepath)
            path.parent.mkdir(parents=True, exist_ok=True)

            with open(path, 'w', encoding='utf-8') as f:
                f.write(content)

            return f"Successfully wrote to {filepath}"
        except Exception as e:
            return f"Error writing file: {str(e)}"


class ListDirectory(Tool):
    """Tool for listing directory contents."""

    name = "list_directory"
    description = "List the contents of a directory"
    parameters = {
        "type": "object",
        "properties": {
            "directory": {
                "type": "string",
                "description": "Path to the directory to list",
                "default": "."
            }
        },
        "required": []
    }

    async def run(self, directory: str = ".") -> str:
        """List directory contents."""
        try:
            path = Path(directory)
            if not path.exists():
                return f"Error: Directory '{directory}' not found"

            if not path.is_dir():
                return f"Error: '{directory}' is not a directory"

            items = []
            for item in sorted(path.iterdir()):
                if item.is_dir():
                    items.append(f"📁 {item.name}/")
                else:
                    size = item.stat().st_size
                    items.append(f"📄 {item.name} ({size} bytes)")

            if not items:
                return f"Directory '{directory}' is empty"

            return f"Contents of {directory}:\n" + "\n".join(items)
        except Exception as e:
            return f"Error listing directory: {str(e)}"
