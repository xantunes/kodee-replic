"""FastMCP server for Kodee Replica."""

import os
import platform
import subprocess
from datetime import datetime
from typing import Any, Dict, List

import httpx
from fastmcp import FastMCP

mcp = FastMCP("kodee-mcp")

# Blocked shell commands for safety
_BLOCKED_COMMANDS = {
    "rm",
    "del",
    "format",
    "fdisk",
    "dd",
    "mkfs",
    "shutdown",
    "reboot",
    "poweroff",
    "halt",
}


def _is_command_safe(command: str) -> bool:
    """Check if a shell command is safe to execute."""
    tokens = command.strip().lower().split()
    if not tokens:
        return False
    return tokens[0] not in _BLOCKED_COMMANDS


@mcp.tool()
def read_file(path: str) -> str:
    """Read the contents of a file at the given path.

    Args:
        path: Absolute or relative path to the file.

    Returns:
        The file contents as a string.
    """
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        return f"Error reading file: {e}"


@mcp.tool()
def write_file(path: str, content: str) -> str:
    """Write content to a file at the given path.

    Args:
        path: Absolute or relative path to the file.
        content: Text content to write.

    Returns:
        Confirmation message or error.
    """
    try:
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return f"File written successfully: {path}"
    except Exception as e:
        return f"Error writing file: {e}"


@mcp.tool()
def list_directory(path: str) -> str:
    """List files and directories at the given path.

    Args:
        path: Directory path to list.

    Returns:
        Newline-separated list of entries.
    """
    try:
        entries = os.listdir(path)
        return "\n".join(entries)
    except Exception as e:
        return f"Error listing directory: {e}"


@mcp.tool()
def search_files(query: str, path: str) -> str:
    """Search for files whose names contain the query string.

    Args:
        query: Substring to search for in file names.
        path: Directory path to search in.

    Returns:
        Newline-separated list of matching file paths.
    """
    try:
        matches: List[str] = []
        for root, _dirs, files in os.walk(path):
            for fname in files:
                if query.lower() in fname.lower():
                    matches.append(os.path.join(root, fname))
        return "\n".join(matches) if matches else "No matching files found."
    except Exception as e:
        return f"Error searching files: {e}"


@mcp.tool()
def get_system_info() -> str:
    """Get basic system information.

    Returns:
        OS name, Python version, and current time.
    """
    os_name = platform.system()
    python_version = platform.python_version()
    current_time = datetime.now().isoformat()
    return f"OS: {os_name}\nPython: {python_version}\nTime: {current_time}"


@mcp.tool()
def run_command(command: str) -> str:
    """Execute a shell command safely.

    Args:
        command: The shell command to run.

    Returns:
        stdout/stderr output or error message.
    """
    if not _is_command_safe(command):
        return f"Error: Command blocked for safety: {command}"
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=30,
        )
        output = result.stdout
        if result.stderr:
            output += f"\n{result.stderr}"
        return output or "Command executed successfully with no output."
    except subprocess.TimeoutExpired:
        return "Error: Command timed out after 30 seconds."
    except Exception as e:
        return f"Error running command: {e}"


@mcp.tool()
async def fetch_url(url: str) -> str:
    """Fetch content from a URL using httpx.

    Args:
        url: The URL to fetch.

    Returns:
        Response text or error message.
    """
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url)
            response.raise_for_status()
            return response.text
    except Exception as e:
        return f"Error fetching URL: {e}"


@mcp.tool()
def search_web(query: str) -> str:
    """Search the web for a query (stub implementation).

    Args:
        query: Search query string.

    Returns:
        Dummy search results.
    """
    return (
        f"Web search results for '{query}':\n"
        f"1. Example result A\n"
        f"2. Example result B\n"
        f"3. Example result C"
    )


@mcp.tool()
def calculate(expression: str) -> str:
    """Safely evaluate a mathematical expression.

    Args:
        expression: Mathematical expression to evaluate, e.g. '2 + 2'.

    Returns:
        Result as a string or error message.
    """
    try:
        allowed_names: Dict[str, Any] = {
            "abs": abs,
            "max": max,
            "min": min,
            "pow": pow,
            "round": round,
        }
        result = eval(expression, {"__builtins__": {}}, allowed_names)
        return str(result)
    except Exception as e:
        return f"Error evaluating expression: {e}"


@mcp.tool()
def get_weather(location: str) -> str:
    """Get dummy weather data for a location.

    Args:
        location: City or location name.

    Returns:
        Dummy weather description.
    """
    return (
        f"The weather in {location} is sunny with a temperature of 25°C "
        f"and light winds."
    )


@mcp.tool()
def send_email(to: str, subject: str, body: str) -> str:
    """Send an email (stub implementation).

    Args:
        to: Recipient email address.
        subject: Email subject.
        body: Email body content.

    Returns:
        Confirmation message.
    """
    return (
        f"Email stub: Would send email to {to} "
        f"with subject '{subject}' and body length {len(body)}."
    )


@mcp.tool()
def create_reminder(title: str, datetime: str) -> str:
    """Create a reminder (stub implementation).

    Args:
        title: Reminder title.
        datetime: Reminder date and time (ISO format preferred).

    Returns:
        Confirmation message.
    """
    return f"Reminder stub: '{title}' scheduled for {datetime}."


if __name__ == "__main__":
    mcp.run()
