"""
facebook-reels-downloader
Download all reels from a Facebook channel/page with a single command.

Usage:
    python reels.py <channel_name> "<channel_reel_url>"
    python reels.py <channel_name> --from-csv output/<channel_name>.csv
    python reels.py                 # interactive, paste the URL when asked

Add --dated-filenames to any of the above to name each downloaded file
"DDMMYYYY_<channel_name>_<id>.<ext>" instead of just "<id>.<ext>", which makes
files from many channels sortable by upload date and site once collected
together.

Notes:
- ALWAYS wrap the URL in quotes. Facebook profile links contain "&", which every
  shell treats as an operator (PowerShell refuses to run, cmd.exe and bash cut
  the URL in half). Quotes make the shell hand the whole URL to Python.
- Facebook only shows a few reels to logged-out users. The script opens Chrome
  and pauses so you can log in manually, then it scrolls and collects every reel.
- Selenium 4.6+ auto-manages chromedriver (Selenium Manager); no manual download.
"""
import csv
import os
import subprocess
import sys
from time import sleep
from urllib.parse import parse_qsl, urlparse, urlunparse

# Hosts we accept as a Facebook channel. Anything else is almost certainly a typo.
FACEBOOK_HOSTS = ("facebook.com", "fb.com")

# Path segments that already point at reels, so we must not rewrite the URL.
REELS_SEGMENTS = {"reel", "reels", "videos"}

USAGE = """Usage:
  python reels.py <channel_name> "<channel_reel_url>"
  python reels.py <channel_name> --from-csv <path_to_csv>
  python reels.py                          (interactive - just paste the URL)

Add --dated-filenames to name files "DDMMYYYY_<channel_name>_<id>.<ext>"
instead of just "<id>.<ext>" - useful for sorting reels from many channels
by upload date and site once they are collected in one place.

Keep the URL inside quotes. Facebook URLs contain "&", and an unquoted "&" is
consumed by the shell before Python ever sees it:
  PowerShell : "The ampersand (&) character is not allowed"
  cmd.exe    : the URL is silently cut at the "&"
  bash/zsh   : the URL is cut and the command is put in the background

Examples:
  python reels.py jireel "https://www.facebook.com/profile.php?id=61554746552594&sk=reels_tab"
  python reels.py jireel "https://www.facebook.com/jireel/reels"
  python reels.py jireel "https://www.facebook.com/jireel/reels" --dated-filenames
"""

# Flag: name downloaded files "DDMMYYYY_<channel>_<id>.<ext>" instead of "<id>.<ext>".
DATED_FILENAMES_FLAG = "--dated-filenames"

TRUNCATED_URL_WARNING = """
WARNING: the URL you passed ends right after the profile id, which is what a
shell leaves behind when it eats an unquoted "&" (the "&sk=reels_tab" part is
missing). Continuing with the reels tab added back automatically.

Next time, put the URL in quotes:
  python reels.py <channel_name> "<url>"
"""


def _clean_url(url):
    """Strip whitespace and any quote characters the shell left in the string."""
    # Users paste URLs still wrapped in the quotes they typed, and cmd.exe users
    # are told to escape as ...id=1"&"sk=... - both leave stray quotes in argv.
    # A quote is never valid in an un-encoded URL, so dropping all of them is safe.
    return url.strip().replace('"', "").replace("'", "").strip()


def normalize_channel_url(url):
    """Return a URL pointing at the channel's reels tab.

    Repairs the two things that go wrong in practice: stray quotes from shell
    escaping, and a profile URL whose "&sk=reels_tab" was eaten by the shell.
    Raises ValueError if the string is not a Facebook URL.
    """
    url = _clean_url(url)
    if not url:
        raise ValueError("No URL given.")
    if "://" not in url:
        url = "https://" + url

    parts = urlparse(url)
    host = parts.netloc.lower().split(":")[0]
    if not any(host == h or host.endswith("." + h) for h in FACEBOOK_HOSTS):
        raise ValueError(f"Not a Facebook URL: {url}")

    path, query = parts.path, parts.query
    segments = [s for s in path.split("/") if s]
    lowered = {s.lower() for s in segments}

    # Already a reels URL, or the user picked a tab on purpose - leave it alone.
    if lowered & REELS_SEGMENTS or "sk" in {k.lower() for k, _ in parse_qsl(query)}:
        return urlunparse(parts)

    if segments and segments[0].lower() in ("profile.php", "people"):
        # Profile-style URL: the reels tab is a query parameter.
        query = f"{query}&sk=reels_tab" if query else "sk=reels_tab"
    elif len(segments) == 1:
        # Vanity page like /jireel: the reels tab is a path.
        path = f"/{segments[0]}/reels"

    return urlunparse((parts.scheme, parts.netloc, path, parts.params, query, parts.fragment))


def looks_shell_truncated(url):
    """True if the URL looks like a profile link that lost its "&..." to the shell."""
    url = _clean_url(url)
    if "://" not in url:
        url = "https://" + url
    parts = urlparse(url)
    if not parts.query:
        return False
    keys = [k.lower() for k, _ in parse_qsl(parts.query)]
    return parts.path.lower().endswith("/profile.php") and keys == ["id"]


def _prompt(label):
    """Read one line from the user. Nothing here goes through a shell."""
    try:
        return input(label).strip()
    except EOFError:
        return ""


def build_filename_template(channel, dated=False):
    """Return the yt-dlp filename template (just the file part, no directory).

    dated=True names files "DDMMYYYY_<channel>_<id>.<ext>" so reels from many
    channels can be sorted by upload date and site once collected together.
    Falls back to "NA" for the date if yt-dlp/Facebook has no upload date for
    a given reel, so a missing field can never crash the download.
    """
    if not dated:
        return "%(id)s.%(ext)s"
    # "%" is a template escape character in yt-dlp output templates, so a
    # channel name containing one (e.g. "100% Real Page") must be doubled up
    # or it would corrupt the template instead of appearing literally.
    safe_channel = channel.replace("%", "%%")
    return f"%(upload_date>%d%m%Y|NA)s_{safe_channel}_%(id)s.%(ext)s"


def download_from_csv(channel, csv_path, dated=False):
    """Download every reel URL listed in csv_path with yt-dlp."""
    output_dir = os.path.join("output", channel)
    os.makedirs(output_dir, exist_ok=True)

    # Run yt-dlp as a module of the CURRENT interpreter. This avoids the Windows
    # "[WinError 2] The system cannot find the file specified" error that happens
    # when the yt-dlp console script isn't on PATH (common with Store Python).
    args = [
        sys.executable, "-m", "yt_dlp",
        "-f", "best",
        "-i",                       # skip broken/removed reels and keep going
        "-a", csv_path,             # batch file of URLs
        "--output", os.path.join(output_dir, build_filename_template(channel, dated)),
    ]
    # Merge stderr into stdout so a full stderr pipe can never deadlock (freeze).
    process = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    for line in iter(process.stdout.readline, b""):
        print(line.decode("utf-8", errors="replace"), end="")
    process.wait()
    return process.returncode


def scrape_reel_urls(channel, url):
    """Open the channel in Chrome, let the user log in, scroll, and save reel URLs."""
    from selenium import webdriver
    from selenium.webdriver.common.by import By

    options = webdriver.ChromeOptions()
    # Persist the Facebook login between runs so you only sign in once.
    profile_dir = os.path.abspath(os.path.join("output", ".chrome-profile"))
    options.add_argument(f"--user-data-dir={profile_dir}")

    driver = webdriver.Chrome(options=options)
    driver.maximize_window()
    driver.get(url)
    sleep(3)

    # Close the login pop-up if it shows, so the page is usable. Don't crash if
    # the button isn't there (Facebook changes this markup often).
    try:
        driver.find_element(By.XPATH, "//div[@aria-label='Close']").click()
    except Exception:
        pass

    # Facebook hides most reels from logged-out users, which is why previously the
    # script only saw the first page. Pause here for a manual login.
    print("\nIf you are not logged in, log in to Facebook in the opened Chrome")
    print("window so you can see ALL reels. When the page is ready, come back here.")
    input("Press Enter to start scrolling and collecting reels... ")

    # Scroll to the bottom repeatedly to lazy-load every reel.
    scroll_steps = 100
    scroll_interval = 4
    prev_scroll_position = -1
    for _ in range(scroll_steps):
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        sleep(scroll_interval)
        curr_scroll_position = driver.execute_script("return window.pageYOffset;")
        if curr_scroll_position == prev_scroll_position:
            print("Reached the bottom of the page.")
            break
        prev_scroll_position = curr_scroll_position

    # Collect unique reel URLs.
    seen = set()
    for element in driver.find_elements(By.CSS_SELECTOR, "a"):
        href = element.get_attribute("href")
        if href and "/reel/" in href:
            seen.add(href.split("/?s=")[0])
    driver.quit()

    if not seen:
        print("No reels found on that page. Check that the URL opens the Reels")
        print("tab of the channel and that you were logged in before pressing Enter.")

    os.makedirs("output", exist_ok=True)
    csv_path = os.path.join("output", f"{channel}.csv")
    with open(csv_path, "w", newline="") as f:
        writer = csv.writer(f)
        for href in sorted(seen):
            writer.writerow([href])
    print(f"Saved {len(seen)} reel URL(s) to {csv_path}")
    return csv_path


def main():
    args = sys.argv[1:]

    if args and args[0] in ("-h", "--help"):
        print(USAGE)
        return 0

    # --dated-filenames can appear anywhere; pull it out before the rest of the
    # positional-argument parsing below, which doesn't need to know about it.
    dated = DATED_FILENAMES_FLAG in args
    args = [a for a in args if a != DATED_FILENAMES_FLAG]

    # Re-download mode: python reels.py <channel> --from-csv <path>
    if len(args) >= 2 and args[1] == "--from-csv":
        if len(args) < 3:
            print("Please provide the CSV path: python reels.py <channel> --from-csv <path>")
            return 1
        csv_path = _clean_url(args[2])
        if not os.path.isfile(csv_path):
            print(f"CSV not found: {csv_path}")
            return 1
        return download_from_csv(args[0], csv_path, dated=dated)

    if len(args) >= 2:
        channel, raw_url = args[0], args[1]
        if looks_shell_truncated(raw_url):
            print(TRUNCATED_URL_WARNING)
    else:
        # Interactive mode. What you paste here never passes through the shell,
        # so "&" and every other special character arrive intact.
        print(USAGE)
        print("Nothing to do yet - let's fill it in (paste is safe here).\n")
        channel = args[0] if args else _prompt("Channel name (output folder): ")
        raw_url = _prompt("Channel reels URL: ")
        if not channel or not raw_url:
            print("\nA channel name and a URL are both required.")
            return 1

    try:
        url = normalize_channel_url(raw_url)
    except ValueError as exc:
        print(f"Error: {exc}\n")
        print(USAGE)
        return 1

    if url != _clean_url(raw_url):
        print(f"Using URL: {url}")

    csv_path = scrape_reel_urls(channel, url)
    return download_from_csv(channel, csv_path, dated=dated)


if __name__ == "__main__":
    sys.exit(main())
