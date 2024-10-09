import yt_dlp
import os
import shutil
import requests
import re
import sys
from rich.console import Console
from rich.table import Table
from rich import box
from rich.panel import Panel

# Version of the current script
CURRENT_VERSION = "1.1.7"
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
    if 'formats' not in info:
        console.print("[bold red]No available formats found for this video.[/bold red]")
        return None

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
        'format': f"{format_id}+bestaudio",
        'outtmpl': os.path.join(path, '%(title)s.%(ext)s'),
        'merge_output_format': 'mp4',
        'postprocessors': [{
            'key': 'FFmpegVideoConvertor',
            'preferedformat': 'mp4',
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
                return remote_version
            else:
                console.print("[bold red]Could not determine the latest version.[/bold red]")
                return CURRENT_VERSION
        else:
            console.print(f"[bold red]Failed to check for updates. Status code: {response.status_code}[/bold red]")
            return CURRENT_VERSION
    except Exception as e:
        console.print(f"[bold red]Error checking for updates:[/bold red] {str(e)}")
        return CURRENT_VERSION

def update_script():
    try:
        response = requests.get(UPDATE_URL)
        if response.status_code == 200:
            remote_script = response.text
            with open(__file__, 'w') as f:
                f.write(remote_script)
            console.print("[bold green]Script updated successfully! Restarting the application...[/bold green]")
            python = sys.executable
            os.execl(python, python, *sys.argv)
        else:
            console.print(f"[bold red]Failed to update the script. Status code: {response.status_code}[/bold red]")
    except Exception as e:
        console.print(f"[bold red]Error updating the script:[/bold red] {str(e)}")

def get_playlist_info(playlist_url):
    ydl_opts = {
        'extract_flat': True,
        'quiet': False,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            playlist_info = ydl.extract_info(playlist_url, download=False)
            return playlist_info
        except Exception as e:
            console.print(f"[bold red]An error occurred while fetching playlist info:[/bold red] {e}")
            return None

def display_videos(playlist_info):
    console.print("Available videos:")
    table = Table(title="Video List", box=box.ROUNDED)
    table.add_column("Index", style="cyan", no_wrap=True)
    table.add_column("Title", style="green")
    table.add_column("URL", style="blue")

    for index, entry in enumerate(playlist_info['entries'], start=1):
        title = entry['title']
        video_url = entry['url']
        table.add_row(
            str(index),
            title,
            video_url
        )

    console.print(table)

def parse_selection(selection, total_videos):
    selected_indices = set()
    ranges = selection.split(',')
    for r in ranges:
        if '-' in r:
            start, end = map(int, r.split('-'))
            selected_indices.update(range(start - 1, min(end, total_videos)))
        else:
            selected_indices.add(int(r) - 1)
    return sorted(selected_indices)

def display_formats(formats):
    if not formats:
        console.print("[bold red]No formats available.[/bold red]")
        return None

    table = Table(title="Available Formats", box=box.ROUNDED)
    table.add_column("Index", style="cyan", no_wrap=True)
    table.add_column("Format ID", style="magenta")
    table.add_column("Extension", style="green")
    table.add_column("Resolution", style="yellow")
    table.add_column("File Size", style="cyan")

    for index, fmt in enumerate(formats, start=1):
        filesize = f"{fmt['filesize'] / (1024 * 1024):.2f} MB" if fmt['filesize'] else "N/A"
        table.add_row(
            str(index),
            fmt['format_id'],
            fmt['ext'],
            fmt['resolution'],
            filesize
        )

    console.print(table)
    return formats

def select_format(formats):
    while True:
        try:
            choice = int(console.input("[bold green]Select a format (enter the index): [/bold green]"))
            if 1 <= choice <= len(formats):
                return formats[choice - 1]['format_id']
            else:
                console.print("[bold red]Invalid choice. Please try again.[/bold red]")
        except ValueError:
            console.print("[bold red]Invalid input. Please enter a number.[/bold red]")

def get_common_formats(videos):
    common_formats = None
    for video in videos:
        video_info = get_video_info(video['url'])  # Assuming each video has a 'url' key
        formats = get_available_formats(video_info)
        
        if not formats:
            console.print(f"[bold red]Video {video['id']} is unavailable or deleted.[/bold red]")
            continue
        
        # Filter out formats where 'filesize' is None or 'N/A'
        formats = [fmt for fmt in formats if fmt['filesize'] is not None and fmt['filesize'] != 'N/A']
        
        if common_formats is None:
            common_formats = formats
        else:
            # Keep only formats that are common across all videos
            format_ids = {fmt['format_id'] for fmt in common_formats}
            common_formats = [fmt for fmt in formats if fmt['format_id'] in format_ids]

    if common_formats:
        return common_formats
    else:
        console.print("[bold red]No common formats available for selected videos.[/bold red]")
        return []

import os
import platform

def clear_screen():
    """Clears the terminal screen based on the operating system."""
    os.system('cls' if platform.system() == 'Windows' else 'clear')

def main():
     # Clear the screen when the application starts
    clear_screen() 
    latest_version = check_for_updates()
    current_version_display = CURRENT_VERSION

    version_message = "You are using the latest version." if latest_version == CURRENT_VERSION else f"A newer version ({latest_version}) is available!"

    console.print(Panel(
        f"[bold cyan]YouTube Video Downloader v{current_version_display}[/bold cyan]\n{version_message}",
        title="Welcome",
        title_align="left",
        border_style="cyan",
        padding=(1, 2),
        style="bold"
    ))

    url = console.input("[bold green]Enter the video or playlist URL (or type 'update' to update the script): [/bold green]")

    # Check for update command
    if url.lower() == 'update':
        update_script()
        
        return

    # Determine if the URL is a playlist or a video
    if 'playlist' in url:
        # Handle playlist download
        playlist_info = get_playlist_info(url)

        if not playlist_info:
            console.print("[bold red]Could not retrieve playlist information.[/bold red]")
            return

        display_videos(playlist_info)

        selection = console.input("[bold green]Enter video numbers to download (comma-separated or ranges, e.g., 1,2,4-6): [/bold green]")
        total_videos = len(playlist_info['entries'])
        selected_indices = parse_selection(selection, total_videos)

        if not selected_indices:
            console.print("[bold red]No valid selections made. Exiting.[/bold red]")
            return

        console.print(f"[bold blue]Selected videos: {', '.join(str(i + 1) for i in selected_indices)}[/bold blue]")

        common_formats = get_common_formats([playlist_info['entries'][i] for i in selected_indices])

        if common_formats:
            console.print(f"\nCommon formats available for selected videos:\n")
            display_formats(common_formats)

            # Ask user to select format
            selected_format = select_format(common_formats)

            # Download each selected video
            for index in selected_indices:
                video_url = playlist_info['entries'][index]['url']
                download_content(video_url, selected_format)

            console.print("[bold green]All selected videos have been downloaded successfully![/bold green]")
        else:
            console.print("[bold red]No common formats available for the selected videos.[/bold red]")
    
    else:
        # Handle single video download
        video_info = get_video_info(url)

        if not video_info:
            console.print("[bold red]Could not retrieve video information.[/bold red]")
            return

        formats = get_available_formats(video_info)
        valid_formats = [fmt for fmt in formats if fmt['filesize'] is not None]

        console.print(f"\nAvailable formats for [bold cyan]{video_info['title']}[/bold cyan]:\n")
        display_formats(valid_formats)

        # Get user choice
        selected_format = select_format(valid_formats)

        # Download the selected format
        download_path = os.getcwd()
        filename = download_content(url, selected_format, download_path)
        console.print(f"[bold green]Download completed! Saved to {filename}[/bold green]")


if __name__ == "__main__":
    main()
