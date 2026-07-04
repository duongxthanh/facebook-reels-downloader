"""
facebook-reels-downloader
Download all reels from a Facebook channel/page with a single command.

Usage:
    python reels.py <channel_name> <channel_reel_url>
    python reels.py <channel_name> --from-csv output/<channel_name>.csv

Notes:
- Facebook only shows a few reels to logged-out users. The script opens Chrome
  and pauses so you can log in manually, then it scrolls and collects every reel.
- Selenium 4.6+ auto-manages chromedriver (Selenium Manager); no manual download.
"""
import csv
import os
import subprocess
import sys
from time import sleep


def download_from_csv(channel, csv_path):
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
        "--output", os.path.join(output_dir, "%(id)s.%(ext)s"),
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

    os.makedirs("output", exist_ok=True)
    csv_path = os.path.join("output", f"{channel}.csv")
    with open(csv_path, "w", newline="") as f:
        writer = csv.writer(f)
        for href in sorted(seen):
            writer.writerow([href])
    print(f"Saved {len(seen)} reel URL(s) to {csv_path}")
    return csv_path


def main():
    if len(sys.argv) < 3:
        print("Usage:")
        print("  python reels.py <channel_name> <channel_reel_url>")
        print("  python reels.py <channel_name> --from-csv <path_to_csv>")
        sys.exit(1)

    channel = sys.argv[1]

    if sys.argv[2] == "--from-csv":
        if len(sys.argv) < 4:
            print("Please provide the CSV path: python reels.py <channel> --from-csv <path>")
            sys.exit(1)
        csv_path = sys.argv[3]
        if not os.path.isfile(csv_path):
            print(f"CSV not found: {csv_path}")
            sys.exit(1)
    else:
        url = sys.argv[2]
        csv_path = scrape_reel_urls(channel, url)

    download_from_csv(channel, csv_path)


if __name__ == "__main__":
    main()
