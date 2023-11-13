from selenium import webdriver
from selenium.webdriver.common.by import By
from time import sleep
import subprocess
import csv
import sys

# Initialize the WebDriver
driver = webdriver.Chrome()
driver.maximize_window()

# Open the webpage
chanel = sys.argv[1]
url = sys.argv[2]
driver.get(url)

# Close pop-up login
sleep(5)
element = driver.find_element(By.XPATH, "//div[@aria-label='Close']")
element.click()

# Define the number of scrolling steps and scroll interval
scroll_steps = 100  # Adjust as needed
scroll_interval = 4  # Adjust as needed

# Set an initial scroll position
prev_scroll_position = 0

# Scroll to the bottom multiple times
for _ in range(scroll_steps):
    # Scroll down
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

    # Wait for the page to load new content (you may need to adjust the time)
    sleep(scroll_interval)

    # Get the current scroll position
    curr_scroll_position = driver.execute_script("return window.pageYOffset;")

    # If the scroll position remains the same, you've likely reached the bottom
    if curr_scroll_position == prev_scroll_position:
        print("Reached the bottom of the page.")
        break

    prev_scroll_position = curr_scroll_position

# Extract reel urls
a_elements = driver.find_elements(By.CSS_SELECTOR, 'a')

# Create a chanel output dir
args = ["mkdir", "-p", f"output/{chanel}"]
subprocess.run(args)

with open(f"output/{chanel}.csv", "w") as f:
  writer = csv.writer(f)
  for element in a_elements:
      href = element.get_attribute('href')
      if href and '/reel/' in href:
          writer.writerow([href.split('/?s=')[0]])

f.close()
driver.quit()

# Bulk download reels with yt-dlp
args = ["yt-dlp", "-f", "best", "-a", f"output/{chanel}.csv", "--output", f"output/{chanel}/%(id)s.%(ext)s"]
process = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
for line in iter(lambda: process.stdout.readline(), b''):
    print(line.decode("utf-8"))

process.wait()
