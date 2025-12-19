#!/usr/bin/env python3

"""Unzip the tipitaka translation database."""

import os
import zipfile
from pathlib import Path
import requests
from rich.progress import Progress

from tools.paths import ProjectPaths
from tools.printer import printer as pr


def download_latest_release():
    """Download the latest release zip file from GitHub."""
    pr.info("Downloading latest release from GitHub...")

    # GitHub API URL to get the latest release
    api_url = "https://api.github.com/repos/digitalpalidictionary/tipitaka-translation-db/releases/latest"
    download_url = None

    try:
        # Get the latest release info
        response = requests.get(api_url, timeout=10)
        response.raise_for_status()
        release_data = response.json()

        # Find the zip asset in the release
        for asset in release_data.get("assets", []):
            if asset["name"] == "tipitaka-translation-data.db.zip":
                download_url = asset["browser_download_url"]
                break

        if not download_url:
            raise Exception("Could not find zip file in latest release")

        return download_url

    except Exception as e:
        pr.error(f"Error getting latest release: {e}")
        return None


def ensure_zip_exists():
    """Ensure the zip file exists, downloading it if necessary."""
    pth = ProjectPaths()

    if not pth.tipitaka_translation_db_tarball.exists():
        pr.info("Tipitaka translation zip not found")
        pr.info("Downloading from GitHub releases...")

        download_url = download_latest_release()
        if not download_url:
            raise Exception("Failed to get download URL")

        # Download the file with optimized settings
        try:
            # Use a larger chunk size for better performance (1MB chunks)
            chunk_size = 1024 * 1024  # 1MB

            response = requests.get(download_url, stream=True, timeout=60)
            response.raise_for_status()

            total_size = int(response.headers.get("content-length", 0))
            pr.info(
                f"Downloading {total_size / (1024 * 1024):.1f} MB with {chunk_size / 1024:.0f}KB chunks..."
            )

            # Create directory if it doesn't exist
            pth.tipitaka_translation_db_dir.mkdir(parents=True, exist_ok=True)

            with open(pth.tipitaka_translation_db_tarball, "wb") as f:
                with Progress() as progress:
                    task = progress.add_task("", total=total_size)
                    for chunk in response.iter_content(chunk_size=chunk_size):
                        if chunk:  # filter out keep-alive new chunks
                            f.write(chunk)
                            progress.update(task, advance=len(chunk))

            pr.info("Download complete.")

        except Exception as e:
            pr.error(f"Error downloading file: {e}")
            raise


def unzip_file(zip_path: Path, destination_dir: Path):
    """
    Unzip a file to the destination directory.
    """
    pr.green(f"unzipping {zip_path.name}")

    if not zip_path.exists():
        raise FileNotFoundError(f"Zip file not found: {zip_path}")

    destination_dir.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(zip_path, "r") as zip_ref:
        zip_ref.extractall(destination_dir)

    pr.yes("ok")


def main():
    """Extract the Tipitaka translation DB."""
    pr.tic()
    pr.title("unzip tipiṭaka translations db")
    pth = ProjectPaths()

    try:
        # Ensure zip file exists
        ensure_zip_exists()

        # Unzip the file
        unzip_file(
            zip_path=pth.tipitaka_translation_db_tarball,
            destination_dir=pth.tipitaka_translation_db_dir,
        )

    except Exception as e:
        pr.error("An error occurred during extraction")
        pr.error(str(e))

    pr.toc()


if __name__ == "__main__":
    main()
