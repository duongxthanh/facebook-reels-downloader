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
python reels.py <channel_name> <channel_reel_url>

# 2) Re-download later from the saved list (skips scraping)
python reels.py <channel_name> --from-csv output/<channel_name>.csv
```
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

## For your Attention
If you are downloading copyrighted content you should respect author's rights and use the content either for personal purposes or for non-commercial needs with proper mention and authorisation from the author.

## Support & Contributions
- Please ⭐️ this repository if this project helped you!
- Contributions of any kind welcome!
