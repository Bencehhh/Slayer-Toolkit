from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait  
from selenium.webdriver.support import expected_conditions as EC
import time

# You need selenium and webdriver to be installed and the whole folder is opened in visual studio code, otherwise code wont work!
# I recommend using Python 3.10+ for best performance.
# Type this in the console "pip install selenium","pip install webdriver" to install selenium and webdriver
# This code automated user search and it's quite fast!
# Made by BenXiadous (Bencehhh)!

# CONFIGURATIONS 
INPUT_FILE = "usernames.txt"  # List of usernames which need to be searched
OUTPUT_FILE = "roblox_user_ids.txt"  # Output file for ID's
LOGIN_URL = "https://www.roblox.com/login"
SEARCH_URL_TEMPLATE = "https://www.roblox.com/search/users?keyword="
USERNAME = "USERNAME"  # Put your alt's username and password here, make sure it doesn't have 2 step.
PASSWORD = "PASSWORD"  # You can use burner accounts too lol, works with any account

# Read usernames
with open(INPUT_FILE, "r") as f:
    SEARCH_TERMS = [line.strip() for line in f if line.strip()]

# WebDriver initialization
driver = webdriver.Chrome()

try:
    # Logging into Roblox
    print("Navigating to the login page...")
    driver.get(LOGIN_URL)
    time.sleep(3)

    # Accept cookies (optional) DONT TOUCH!
    try:
        accept_cookies_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//button[text()='Accept All']"))
        )
        accept_cookies_button.click()
    except Exception:
        print("No cookies prompt. Continuing.")

    # Load login page
    username_field = WebDriverWait(driver, 20).until(
        EC.presence_of_element_located((By.ID, "login-username"))
    )
    password_field = driver.find_element(By.ID, "login-password")
    login_button = driver.find_element(By.ID, "login-button")

    username_field.send_keys(USERNAME)
    password_field.send_keys(PASSWORD)
    login_button.click()
    time.sleep(5)

    # Checkup
    if "login" in driver.current_url:
        raise Exception("Login failed!")

    print("Login successful!")

    # Read input file
    with open(OUTPUT_FILE, "w") as output_file:
        for search_term in SEARCH_TERMS:
            # SEARCH
            search_url = f"{SEARCH_URL_TEMPLATE}{search_term}"
            driver.get(search_url)
            print(f"Searching for: {search_term}")
            time.sleep(3)

            try:
                # Get search results
                user_cards = WebDriverWait(driver, 10).until(
                    EC.presence_of_all_elements_located(
                        (By.XPATH, "//li[contains(@class, 'player-item')]")
                    )
                )
                print(f"Found {len(user_cards)} results for {search_term}.")

                # Look for search queries
                for user_card in user_cards:
                    try:
                        # Get username and User ID's
                        username_tag = user_card.find_element(
                            By.XPATH, ".//div[@class='text-overflow avatar-card-label ng-binding ng-scope']"
                        )
                        username = username_tag.text.strip()

                        if search_term.lower() in username.lower():
                            # Get Profile URL ID
                            profile_link = user_card.find_element(
                                By.XPATH, ".//a[@class='avatar-card-link']"
                            ).get_attribute("href")
                            user_id = profile_link.split("/")[-2]  # Numerical ID

                            print(f"Found user: {username}, ID: {user_id}")
                            output_file.write(f"{search_term}: {user_id}\n")
                            output_file.flush()

                    except Exception as e:
                        print(f"Error processing card: {e}")
                        continue

            except Exception as e:
                print(f"No results or error for {search_term}: {e}")
                continue

except Exception as e:
    print(f"An error occurred: {e}")

finally:
    driver.quit()
    print("Browser closed.")
