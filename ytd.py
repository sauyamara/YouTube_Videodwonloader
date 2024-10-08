import os
import shutil
import yt_dlp
import requests
import re
from rich.console import Console
from rich.table import Table
from rich import box
from rich.panel import Panel

# Version of the current script
CURRENT_VERSION = "1.0.3"
UPDATE_URL = "https://raw.githubusercontent.com/sauyamara/YouTube_Videodwonloader/refs/heads/main/ytd.py"

# Create a Rich console object
console = Console()

def get_video_info(url):
    ydl_opts = {'quiet': True, 'no_warnings': True}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(url, download=False)
            return info
        except Exception as e:
            console.print(f"[bold red]Error fetching video information:[/bold red] {str(e)}")
            return None

def get_available_formats(info):
    formats = info['formats']
    return [
        {
            'format_id': f['format_id'],
            'ext': f.get('ext', 'N/A'),
            'resolution': f.get('resolution', 'N/A'),
            'filesize': f.get('filesize') if 'filesize' in f else None
        }
        for f in formats
    ]

def download_content(url, format_id, path='.'):
    ydl_opts = {
        'format': f"{format_id}+bestaudio",  # Download the selected format and best available audio
        'outtmpl': os.path.join(path, '%(title)s.%(ext)s'),  # Save the file in the specified path
        'merge_output_format': 'mp4',  # Ensure video and audio are merged into mp4 format
        'postprocessors': [{
            'key': 'FFmpegVideoConvertor',
            'preferedformat': 'mp4',  # Ensure conversion to MP4 if necessary
        }]
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])
    return ydl.prepare_filename(ydl.extract_info(url, download=False))

def check_for_updates():
    try:
        response = requests.get(UPDATE_URL)
        if response.status_code == 200:
            remote_script = response.text
            remote_version_match = re.search(r'CURRENT_VERSION = "(.*?)"', remote_script)
            if remote_version_match:
                remote_version = remote_version_match.group(1)
                return remote_version  # Return the latest version
            else:
                console.print("[bold red]Could not determine the latest version.[/bold red]")
                return CURRENT_VERSION  # Default to current version if unable to parse
        else:
            console.print(f"[bold red]Failed to check for updates. Status code: {response.status_code}[/bold red]")
            return CURRENT_VERSION  # Default to current version if unable to check
    except Exception as e:
        console.print(f"[bold red]Error checking for updates:[/bold red] {str(e)}")
        return CURRENT_VERSION  # Default to current version on error

def update_script():
    try:
        response = requests.get(UPDATE_URL)
        if response.status_code == 200:
            remote_script = response.text
            with open(__file__, 'w') as f:
                f.write(remote_script)
            console.print("[bold green]Script updated successfully! Please restart the application.[/bold green]")
            exit()
        else:
            console.print(f"[bold red]Failed to update the script. Status code: {response.status_code}[/bold red]")
    except Exception as e:
        console.print(f"[bold red]Error updating the script:[/bold red] {str(e)}")

def main():
    # Check for updates before starting the program
    latest_version = check_for_updates()
    current_version_display = CURRENT_VERSION

    # Determine if the current version is the latest
    if latest_version == CURRENT_VERSION:
        version_message = "You are using the latest version."
    else:
        version_message = f"A newer version ({latest_version}) is available!"

    # Display welcome message with version information
    console.print(Panel(
        f"[bold cyan]YouTube Video Downloader v{current_version_display}[/bold cyan]\n{version_message}",
        title="Welcome",
        title_align="left",
        border_style="cyan",
        padding=(1, 2),
        style="bold"
    ))

    url = console.input("[bold blue]Enter the YouTube video URL or type 'update' to update the script: [/bold blue]")

    if url.lower() == 'update':
        update_script()

    # Get video info and available formats
    info = get_video_info(url)
    if info is None:
        return

    formats = get_available_formats(info)

    # Filter formats to only include those with valid filesize
    valid_formats = [fmt for fmt in formats if fmt['filesize'] is not None]

    # Display available formats in a table
    console.print(f"\nAvailable formats for [bold cyan]{info['title']}[/bold cyan]:\n")
    
    table = Table(title="Available Formats", box=box.SIMPLE)
    table.add_column("Number", justify="center", style="cyan", no_wrap=True)
    table.add_column("Format ID", justify="center", style="cyan", no_wrap=True)
    table.add_column("Extension", justify="center", style="magenta")
    table.add_column("Resolution", justify="center", style="yellow")
    table.add_column("Filesize (MB)", justify="center", style="green")
    
    for index, fmt in enumerate(valid_formats):
        filesize_display = f"{float(fmt['filesize']) / 1024 / 1024:.2f}"
        table.add_row(
            str(index + 1),
            str(fmt['format_id']),
            fmt['ext'],
            fmt['resolution'],
            filesize_display
        )

    console.print(table)

    # Get user choice
    while True:
        try:
            choice = int(console.input("\n[bold blue]Select a format number to download: [/bold blue]")) - 1
            if choice < 0 or choice >= len(valid_formats):
                raise ValueError("Invalid choice, please select a valid format number.")
            selected_format = valid_formats[choice]['format_id']
            break
        except ValueError as e:
            console.print(f"[bold red]{str(e)}[/bold red]")

    # Download the selected format with the highest available audio
    download_path = os.getcwd()
    filename = download_content(url, selected_format, download_path)
    
    console.print(f"\n[bold green]Downloaded:[/bold green] {filename}")
    
    # Check if 'downloads' folder exists and delete it if present
    downloads_folder = 'downloads'
    if os.path.exists(downloads_folder):
        try:
            shutil.rmtree(downloads_folder)
            console.print(f"\n[bold green]Deleted the 'downloads' folder.[/bold green]")
        except Exception as e:
            console.print(f"[bold red]Error deleting the 'downloads' folder:[/bold red] {str(e)}")
    else:
        console.print("\n[bold yellow]No 'downloads' folder found in the current directory.[/bold yellow]")
    
    console.print(Panel("[bold blue]Thank you for using the YouTube Video Downloader![/bold blue]", title="Done", border_style="green"))

if __name__ == '__main__':
    main()
