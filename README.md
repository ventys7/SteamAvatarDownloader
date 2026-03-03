# SteamAvatarDownloader

A Python utility to download any Steam user's profile picture in the highest available resolution, with an optional AI-powered 4x upscaling feature.

⚠️ Important Disclaimer
- Project Status: This repository is no longer maintained. No further updates or bug fixes will be provided. Feel free to fork and modify it.
- Platform: This script has been tested and verified only on macOS.
- AI Requirements: Automatic installation of the AI upscaler (Real-ESRGAN) is only supported for macOS and Windows.

✨ Features
- Smart Search: Accepts Vanity IDs, SteamID64, or full Profile URLs.
- Bilingual Interface: Support for both Italian and English.
- AI Upscaling: Integrated with Real-ESRGAN to provide 4x resolution enhancement (realesrgan-x4plus model).
- Auto-Installer: Can automatically download and set up the necessary AI binaries if they are missing.
- Organized Saving: Avatars are automatically named after the user and saved to ~/Pictures/SteamAvatars.

🛠 Requirements
- Python 3.x.
- No external Python libraries are strictly required (uses standard libraries like urllib, html.parser, and subprocess).
- Real-ESRGAN (Optional): For the AI features. The script can attempt to install this for you.

🚀 How to Use | Run the script:
- python3 steamavatardownloader.py

- Choose Language: Type it for Italian or en for English.
- AI Setup: When asked, decide if you want to enable AI upscaling. If you say yes and it's not found, the script will offer to download it for you.
- Enter Profile: Paste the Steam URL or ID of the target profile.
- Check Output: Your images will be waiting in your system's Pictures/SteamAvatars folder.

📝 Technical Details
- Scraping Logic: The script first tries to fetch data via Steam's XML interface (?xml=1) for the rawest image link. If that fails, it falls back to a custom HTML parser.
- Sanitization: Usernames are sanitized to ensure they are valid filenames on your OS.
- Upscaling: If enabled, the script runs a subprocess command to the Real-ESRGAN binary, applying the realesrgan-x4plus model to the downloaded file.
