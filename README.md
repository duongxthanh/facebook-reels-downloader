# facebook-reels-downloader
Download all reels on channel with a single command.


Facebook Reels Downloader is simple script written with Python that let you download and save your favorite Facebook reels to your computer in HD(High Defination) quality or in SD(Standard Defination) quality.

Depending upon the available quality of the video, downloader extracts HD quality and SD quality video links. You can choose to download whichever you want. However, in some cases, the only quality available is SD.

All the videos will be in MPEG-4 Part 14 (MP4 😉) format.

![fb_v](demo.gif)

## Clone & Configure
```
# clone the repo
$ git clone https://github.com/duongxthanh/facebook-reels-downloader.git

# change the working directory to facebook-reels-downloader
$ cd facebook-reels-downloader

# install the requirements (use the SAME python you will run the script with)
$ python -m pip install -r requirements.txt
```
> Chromedriver is downloaded automatically by Selenium Manager (selenium >= 4.6),
> so you do **not** need to install chromedriver manually.

## Usage
```
# 1) Collect reels from a channel and download them
#    ALWAYS put the URL in quotes (Facebook URLs contain "&").
python reels.py <channel_name> "<channel_reel_url>"

# 2) Re-download later from the saved list (skips scraping)
python reels.py <channel_name> --from-csv output/<channel_name>.csv

# 3) No arguments: the script asks for the name and the URL.
#    Pasting at the prompt is always safe - the shell never sees it.
python reels.py
```

### Quote the URL
A Facebook channel link usually looks like
`https://www.facebook.com/profile.php?id=61554746552594&sk=reels_tab`. The `&` is
a **shell operator**, so an unquoted URL never reaches the script:

| Shell | What happens without quotes |
|---|---|
| PowerShell | refuses to run: *"The ampersand (&) character is not allowed"* |
| cmd.exe | silently cuts the URL at the `&` and tries to run the rest as a command |
| bash / zsh | cuts the URL and puts the command in the background |

Quotes fix all three:
```
python reels.py jireel "https://www.facebook.com/profile.php?id=61554746552594&sk=reels_tab"
python reels.py jireel "https://www.facebook.com/jireel/reels"
```
If a cut-off URL still gets through, the script now detects it, warns you, and
puts the reels tab back before scraping.

### What happens when it runs
A Chrome window opens on the channel page. **Log in to Facebook in that window**
so you can see *all* reels (logged-out users only see the first page), then press
Enter in the terminal to start collecting. The login is remembered for next time.
Reel URLs are saved to `output/<channel_name>.csv` and the videos to
`output/<channel_name>/`.

## Troubleshooting
- **`ModuleNotFoundError: No module named 'selenium'`** — you installed the
  packages into a different Python than the one running the script. Install with
  the same interpreter: `python -m pip install -r requirements.txt` (or
  `python3 -m pip ...`). Check which one you're on with `python -c "import sys; print(sys.executable)"`.
- **`[WinError 2] The system cannot find the file specified`** after
  *"Reached the bottom of the page."* — this was caused by `yt-dlp` not being on
  PATH. Fixed: the script now calls yt-dlp via `python -m yt_dlp`. Pull the latest
  version.
- **Only the first page of reels is downloaded** — you were not logged in.
  Log in when the Chrome window opens, then press Enter to continue.
- **It freezes during download** — fixed. `yt-dlp` output no longer fills a pipe
  that was never read. Pull the latest version. Broken/removed reels are now
  skipped automatically (`-i`).
- **`The ampersand (&) character is not allowed`** (PowerShell), or the URL gets
  cut at the `&` (cmd.exe, bash) — the URL was not quoted. Use
  `python reels.py <channel> "<url>"`, or run `python reels.py` with no arguments
  and paste the URL at the prompt.
- **`... is not recognized as the name of a cmdlet`** — the `python reels.py <channel>`
  part is missing from the command; you ran the bare URL.
- **`Not a Facebook URL`** — the argument order is `<channel_name>` first, then the URL.

## For your Attention
If you are downloading copyrighted content you should respect author's rights and use the content either for personal purposes or for non-commercial needs with proper mention and authorisation from the author.

## Tests
```
python -m unittest discover -s tests -v
```
No extra dependencies; the URL handling is covered by plain `unittest`.

## Support & Contributions
- Please ⭐️ this repository if this project helped you!
- Contributions of any kind welcome!
