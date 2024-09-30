from selenium import webdriver
from selenium.webdriver.common.by import By
from time import sleep
import os
import subprocess
import csv
import sys

# Initialize the WebDriver
# Ensure the chromedriver is in the system path or provide the absolute path
driver = webdriver.Chrome()  # Update if needed, e.g., webdriver.Chrome(executable_path='/path/to/chromedriver')
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

# Extract reel URLs
a_elements = driver.find_elements(By.CSS_SELECTOR, 'a')

# Create a chanel output directory (cross-platform)
output_dir = os.path.join("output", chanel)
os.makedirs(output_dir, exist_ok=True)

# Save the extracted URLs to a CSV file
csv_path = os.path.join("output", f"{chanel}.csv")
with open(csv_path, "w") as f:
    writer = csv.writer(f)
    for element in a_elements:
        href = element.get_attribute('href')
        if href and '/reel/' in href:
            writer.writerow([href.split('/?s=')[0]])

f.close()
driver.quit()

# Bulk download reels with yt-dlp
args = ["yt-dlp", "-f", "best", "-a", csv_path, "--output", os.path.join(output_dir, "%(id)s.%(ext)s")]
process = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
for line in iter(lambda: process.stdout.readline(), b''):
    print(line.decode("utf-8"))

process.wait()
