import json
import os
import sys
import time
from datetime import date, datetime

import requests
import logging
from selenium import webdriver
from selenium.common import NoSuchElementException, StaleElementReferenceException, TimeoutException
from selenium.webdriver import ActionChains, Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

import pandas as pd

# ACCOUNT-DATA
sourceAccount = "kumsalkarauzum97@gmail.com"
sourcePassword = "Kumsalkara."

targetAccount = "cemalcandogan@gmail.com"
targetPassword = "Covet13po."
betTypes = ["5'li Ganyan","4'lü Ganyan","Çifte Bahis"]
sigara = 60
def login_to_ebayi():
    """
    Step 1: Log in to ebayi.tjk.org (POST /giris) with user, pass, keep_login.
    Returns a requests.Session() that should be authenticated if successful.
    """
    session = requests.Session()

    # Login URL
    login_url = "https://ebayi.tjk.org/giris"

    # Hardcoded headers from DevTools (minus the HTTP/2 pseudo-headers).
    # You'll need a valid Cookie with 'cs=...' if the server requires the CSRF token to match.
    headers = {
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Accept-Encoding": "gzip, deflate, br, zstd",
        "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7",
        "Cache-Control": "no-cache",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "Origin": "https://ebayi.tjk.org",
        "Pragma": "no-cache",
        "Referer": "https://ebayi.tjk.org/",
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/131.0.0.0 Safari/537.36"
        ),
        # Example: The CSRF token from DevTools (must match the 'cs=' cookie below)
        "X-CSRF-TOKEN": "b84bb1b32e7c...example...",
        "X-Requested-With": "XMLHttpRequest",
        # Cookie copied from DevTools, must contain 'cs=...'
        "Cookie": (
            "eBayi_ga=GA1.3.14903...; "
            "cs=b84bb1b32e7c...example...; "  # must match the X-CSRF-TOKEN
        ),
    }
    # VOLKAN ABİ
    # login_payload = {
    #     "user": "16681200240",
    #     "pass": "Alya2592.",
    #     "keep_login": "true"
    # }

    # The login form data
    login_payload = {
        "user": sourceAccount,
        "pass": sourcePassword,
        "keep_login": "true"
    }

    # Send the login request
    resp = session.post(login_url, headers=headers, data=login_payload)

    print("Login status code:", resp.status_code)
    try:
        print("Login response JSON:", resp.json())
    except ValueError:
        print("Login response text:", resp.text)

    # After this, session.cookies should have any new cookies set by the server
    print("Cookies after login:", session.cookies.get_dict())

    return session

def post_biletlerim(session):
    """
    Step 2: Call POST /biletlerim with minimal data (Content-Length: 3, etc.).
    This often updates or confirms the CSRF token in the session,
    allowing /biletlerim/retrievedata to succeed.
    """
    url = "https://ebayi.tjk.org/biletlerim"

    # We retrieve the current 'cs' cookie from our session (if any).
    # If the server updated it after login, it might be different now.
    current_csrf_token = session.cookies.get("cs")

    headers = {
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Accept-Encoding": "gzip, deflate, br, zstd",
        "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7",
        "Cache-Control": "no-cache",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "Origin": "https://ebayi.tjk.org",
        "Pragma": "no-cache",
        "Referer": "https://ebayi.tjk.org/hesabim/oturum-gecmisim",
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/131.0.0.0 Safari/537.36"
        ),
        # We set the CSRF token to whatever we have in session cookies now
        "X-CSRF-TOKEN": current_csrf_token if current_csrf_token else "",
        "X-Requested-With": "XMLHttpRequest"
    }

    # The request body is only 3 bytes in DevTools. Possibly it's an empty form or "nil".
    # We'll assume it's just an empty dict or minimal data:
    data = {}

    resp = session.post(url, headers=headers, data=data)
    print("POST /biletlerim -> status code:", resp.status_code)
    print("Response text:", resp.text)

    # Check cookies again—maybe the server updates 'cs' again
    print("Cookies after /biletlerim:", session.cookies.get_dict())
    return resp

def post_biletlerim_retrievedata(session):
    """
    Step 3: Finally call POST /biletlerim/retrievedata with the correct CSRF token
    and any required form data (type=..., date=...).
    """
    url = "https://ebayi.tjk.org/biletlerim/retrievedata"

    # Get the latest CSRF token from cookies again
    current_csrf_token = session.cookies.get("cs")

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "X-CSRF-TOKEN": current_csrf_token if current_csrf_token else "",
        "X-Requested-With": "XMLHttpRequest",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "Referer": "https://ebayi.tjk.org/biletlerim"
    }
    today_str = date.today().strftime("%Y-%m-%d")
    payload = {
        #   "startdate": "2024-12-22",
        "enddate": today_str,
        "limit": "50",
        "offset": "0,0",
        "order": "desc",
        "status": "played",
    }

    resp = session.post(url, headers=headers, data=payload)
    print("POST /biletlerim/retrievedata -> status:", resp.status_code)

    try:
        json_resp = resp.json()
        print("Retrieved data JSON:", json_resp)
        save_json_to_file(json_resp, "my-output.json")
    except ValueError:
        print("Response text (not JSON):", resp.text)

    return resp

def save_json_to_file(json_resp, filename="response.json"):
    """
    Saves the given JSON object to a file with pretty indentation.
    """
    with open(filename, "w", encoding="utf-8") as f:
        # ensure_ascii=False allows non-ASCII characters to be preserved
        # indent=4 makes the file more readable (pretty-printed)
        json.dump(json_resp, f, ensure_ascii=False, indent=4)

    print(f"JSON response successfully saved to {filename}")

def load_bilets_from_json(json_file):
    """
    Loads specific coupon data from a JSON file and returns them as a Pandas DataFrame.

    Args:
        json_file (str): Path to the JSON file containing bilets data.

    Returns:
        pd.DataFrame: DataFrame containing filtered coupons data with only specified fields.
    """
    # Define the fields you want to extract from each coupon
    desired_fields = ['id', 'race', 'multiplier', 'atlar', 'hipodrom', 'bet', 'cancelable']

    try:
        with open(json_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Safely extract 'coupons' from the nested structure
        coupons = data.get('data', {}).get('coupons', [])

        if not coupons:
            logging.warning("No coupons found in the provided JSON file.")
            return pd.DataFrame()  # Return an empty DataFrame

        # Filter each coupon to include only the desired fields
        filtered_coupons = []
        for coupon in coupons:
            filtered_coupon = {field: coupon.get(field, None) for field in desired_fields}
            filtered_coupons.append(filtered_coupon)

        # Convert the list of filtered coupons to a Pandas DataFrame
        df_coupons = pd.DataFrame(filtered_coupons)
        logging.info(f"Loaded and filtered {len(df_coupons)} coupons from '{json_file}'.")

        return df_coupons

    except FileNotFoundError:
        logging.error(f"The file '{json_file}' does not exist.")
        return pd.DataFrame()

    except json.JSONDecodeError:
        logging.error(f"The file '{json_file}' is not a valid JSON.")
        return pd.DataFrame()

    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")
        return pd.DataFrame()

def setup_selenium():
    """
    Configures and returns a Selenium WebDriver (Chrome) in headless mode.
    Assumes chromedriver.exe is in the same directory as this script.
    """
    chrome_options = Options()

    # Enable headless mode
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")  # Disable GPU acceleration
    chrome_options.add_argument("--disable-extensions")  # Disable browser extensions
    chrome_options.add_argument("--disable-software-rasterizer")  # Software rasterization
    chrome_options.add_argument("--no-sandbox")  # Recommended for headless mode
    chrome_options.add_argument("--disable-dev-shm-usage")  # Prevent issues with /dev/shm on Linux

    # Initialize the Service object with the path to chromedriver.exe
    service = Service(executable_path="chromedriver.exe")

    # Initialize the Chrome WebDriver with the Service object
    driver = webdriver.Chrome(service=service, options=chrome_options)
    driver.maximize_window()
    return driver


def login_to_site(driver, username, password):
    """
    Logs into the website using Selenium by filling out the login form
    and navigates to 'BAHİS YAP'.

    Args:
        driver (webdriver.Chrome): Selenium WebDriver instance.
        username (str): Username for login.
        password (str): Password for login.

    Returns:
        None
    """
    # Navigate to the login page
    driver.get("https://ebayi.tjk.org")  # Adjust URL if different

    # Initialize WebDriverWait with a 20-second timeout
    wait = WebDriverWait(driver, 20)

    try:
        # Wait until the username field is present
        username_field = wait.until(EC.presence_of_element_located((By.NAME, "login-user")))

        # Locate the password field
        try:
            password_field = driver.find_element(By.NAME, "login-password")
        except NoSuchElementException:
            # Try alternative name if 'login-password' doesn't work
            password_field = driver.find_element(By.NAME, "login-pass")

        # Fill in the username and password
        username_field.clear()
        username_field.send_keys(username)

        password_field.clear()
        password_field.send_keys(password)

        # Locate and click the login button
        try:
            login_button = driver.find_element(By.ID, "login-submit-btn")
        except NoSuchElementException:
            # If no ID, try another locator strategy, such as by XPath
            login_button = driver.find_element(By.XPATH, "//button[contains(text(), 'GİRİŞ')]")

        login_button.click()
        print("Clicked the login button.")

        # Optional: Wait for a short duration to let the page load
        time.sleep(3)  # Adjust as needed based on website's response time

        # Call the navigate_to_bahis_yap function to go to 'BAHİS YAP' page


    except Exception as e:
        # On any unexpected error, take a screenshot and exit
        driver.save_screenshot("login_error.png")
        print(f"An error occurred during login: {e}. Screenshot saved as 'login_error.png'. Exiting.")
        driver.quit()
        exit(1)

def create_bilet(driver, race, multiplier, atlar, hipodrom, bet):
    """
    Navigates to the 'BAHİS YAP' page, expands the dropdown, and selects the specified hipodrom.
    """
    try:
        # Step 0: Ensure we are on the main page
        driver.get("https://ebayi.tjk.org")
        print("Navigated to the main page.")
        try:
            clear_button = driver.find_element(By.XPATH, "//button[@data-selector='clear-button']")
            clear_button.click()
            print("Clicked on 'Clear Bilet' button.")
        except NoSuchElementException:
            print("Clear Bilet button not found. Continuing without clicking.")


        # Step 1: Click on the 'BAHİS YAP' link
        bahis_yap_link = driver.find_element(By.XPATH,
                                             "//a[contains(@href, '/bahis-yap-advanced') and contains(text(), 'BAHİS YAP')]")
        bahis_yap_link.click()
        print("Clicked on 'BAHİS YAP' link.")

        # Wait for the page to load
        time.sleep(2)

        # Step 2: Locate and click the dropdown toggle to expand it
        dropdown_toggle = driver.find_element(By.CSS_SELECTOR, "a.btn.btn-glossred.dropdown-toggle")
        dropdown_toggle.click()
        print("Clicked on the dropdown toggle to expand the submenu.")

        # # Wait briefly to ensure the dropdown menu is displayed
        # time.sleep(2)

        # Step 3: Locate the specific <a> element containing the desired hipodrom name
        hipodrom_xpath = f"//a[@class='dropdown-item' and text()='{hipodrom}']"
        hipodrom_element = driver.find_element(By.XPATH, hipodrom_xpath)

        # Click the hipodrom link
        hipodrom_element.click()
        print(f"Selected hipodrom: {hipodrom}")

        # Wait for any subsequent page or elements to load after selection
        # time.sleep(2)

        # Step 4: Locate and click the dropdown toggle for race type
        # Locate the specific anchor using its class and text
        dropdown_toggles = driver.find_elements(By.CSS_SELECTOR, "a.btn.btn-glossred.dropdown-toggle")
        if len(dropdown_toggles) >= 2:
            dropdown_toggles[1].click()
            print("Clicked on the second dropdown toggle")
        else:
            print("Less than two dropdown toggles found.")
        # Wait briefly to ensure the dropdown menu is displayed
        # time.sleep(2)

        # Step 5: Locate the specific <a> element containing the desired race type (bet)
        bet_xpath = f'//a[@class="dropdown-item" and text()="{bet}"]'
        bet_element = driver.find_element(By.XPATH, bet_xpath)

        # Click the bet link
        bet_element.click()
        print(f"Selected bet: {bet}")

        # Step 6: Locate and select atlar data
        # Parse the 'atlar' data
        runs = atlar.split("/")  # Split into runs
        for run_index, run_data in enumerate(runs, start=1):
            horses = run_data.split(",")  # Split horse numbers for this run
            for horse_no in horses:
                horse_no = horse_no.strip()  # Remove any extra spaces
                horse_id = f"run-{run_index}-horse-{horse_no}"  # Construct the input ID

                try:
                    # Locate the label associated with the checkbox
                    label = driver.find_element(By.XPATH, f"//label[@for='{horse_id}']")

                    # Scroll the label into view
                    driver.execute_script("arguments[0].scrollIntoView(true);", label)

                    # Click the label using ActionChains
                    actions = ActionChains(driver)
                    actions.move_to_element(label).click().perform()
                    print(f"Selected horse: Run {run_index}, Horse {horse_no}")

                except NoSuchElementException:
                    print(f"Label for checkbox with ID '{horse_id}' not found. Skipping this horse.")
                except Exception as e:
                    print(f"Could not interact with label for '{horse_id}': {e}")

        # Step 7: Enter Multiplier data
        multiplier_input = driver.find_element(
            By.XPATH, "//input[@type='number' and @placeholder='Misli']"
        )

        # Validate the multiplier value
        multiplier = max(1, min(multiplier, 3250))  # Clamp multiplier between 1 and 3250

        # Clear the input field before entering the value
        try:
            multiplier_input.clear()  # First try standard clear
            multiplier_input.send_keys(Keys.CONTROL + "a")  # Highlight all text
            multiplier_input.send_keys(Keys.DELETE)  # Delete highlighted text
        except Exception:
            # Use JavaScript as a fallback if .clear() doesn't work
            driver.execute_script("arguments[0].value = '';", multiplier_input)

        # Enter the multiplier value
        multiplier_input.send_keys(str(multiplier))
        print(f"Entered multiplier value: {multiplier}")

        # Step 8: Locate and click the submit button
        button = driver.find_element(By.XPATH, "//button[text()='OYNA']")
        button.click()
        print("Clicked the submit button to create the bilet.")

        # Step 9: Wait for the checkbox in the pop-up (retry mechanism)
        checkbox_appeared = False
        wait_time = 30  # Maximum wait time (seconds)
        check_interval = 1  # Check every 1 second

        for _ in range(wait_time // check_interval):  # Loop to keep checking
            try:
                label = driver.find_element(By.XPATH, "//label[@for='approveChecksum']")
                driver.execute_script("arguments[0].scrollIntoView(true);", label)
                actions = ActionChains(driver)
                actions.move_to_element(label).click().perform()
                print("Selected the checkbox in the confirmation pop-up.")
                checkbox_appeared = True
                break  # Exit loop once checkbox is found and clicked
            except NoSuchElementException:
                print("Waiting for the confirmation pop-up checkbox to appear...")
                time.sleep(check_interval)  # Wait and retry
            except Exception as e:
                print(f"Unexpected error while waiting for checkbox: {e}")
                return  # Return to main loop on any unexpected error

        if not checkbox_appeared:
            print("Error: Checkbox did not appear after waiting. Skipping this ticket and moving to the next one.")
            return  # Simply return to continue with the next ticket in the main loop

        # Scroll the label into view
        driver.execute_script("arguments[0].scrollIntoView(true);", label)

        # Step 10: Locate and click the 'Onayla' button
        approve_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "approveButton"))
        )
        approve_button.click()
        print("Clicked the 'Onayla' button to finalize the bilet.")

        # Navigate back to the main page
        driver.get("https://ebayi.tjk.org")
        print("Navigated back to the main page.")


    except NoSuchElementException as e:
        print(f"NoSuchElementException: {e}")
        driver.quit()
        exit(1)

    except Exception as e:
        print(f"An unexpected error occurred during navigation: {e}")
        driver.quit()
        exit(1)


def load_created_bilets():
    """Loads the list of created bilet IDs from a file."""
    if os.path.exists("created_bilets.json"):
        with open("created_bilets.json", "r", encoding="utf-8") as f:
            try:
                return set(json.load(f))  # Load as a set for fast lookups
            except json.JSONDecodeError:
                return set()  # Handle empty or corrupt file
    return set()


def save_created_bilet(bilet_id):
    """Saves a new bilet ID to the created_bilets.json file."""
    created_bilets = load_created_bilets()
    created_bilets.add(bilet_id)  # Add new ID

    with open("created_bilets.json", "w", encoding="utf-8") as f:
        json.dump(list(created_bilets), f, ensure_ascii=False, indent=4)  # Save as a list

# def main():
#     # Step 1: Load created bilet IDs
#     created_bilets = load_created_bilets()
#
#     # Step 2: Log in via Requests
#     session = login_to_ebayi()
#
#     # Step 3: Call /biletlerim to refresh/confirm token
#     post_biletlerim(session)
#     post_biletlerim_retrievedata(session)
#
#     # Step 4: Load bilets from JSON
#     bilets = load_bilets_from_json("my-output.json")
#
#     if bilets.empty:
#         print("No coupons to process. Exiting.")
#         return
#
#     # Filter only "5'li Ganyan" and other selected bet types
#     bilets = bilets[bilets["bet"].isin(betTypes) & (bilets["cancelable"] == True)]
#
#     # Step 5: Remove duplicates by filtering already created bilets
#     bilets = bilets[~bilets["id"].astype(str).isin(created_bilets)]
#
#     # Normalize hipodrom names
#     replacements = {
#         "GULFSTREAM": "Gulfstream Park ABD",
#         "SANLIURFA": "Şanlıurfa",
#         "ISTANBUL": "İstanbul",
#         "WHAMPTON": "Wolverhampton Birleşik Krallık",
#         "ANTALYA": "Antalya",
#         "PHILADELPH": "Philadelphia ABD",
#         "VAAL": "Vaal Guney Afrika",
#         "PARADISE": "Turf Paradise ABD",
#         "CAGNESSUR": "Cagnes Sur Mer Fransa",
#         "MAHONING": "Mahoning Valley ABD",
#         "SOUTHWELL": "Southwell Birleşik Krallık"
#     }
#     bilets["hipodrom"] = bilets["hipodrom"].replace(replacements)
#
#     # Step 6: Set up Selenium
#     driver = setup_selenium()
#
#     try:
#         # Step 7: Log in via Selenium
#         login_to_site(driver, "cemalcandogan@gmail.com", "Covet13po.")
#
#         # Track processed tickets and consecutive empty refreshes
#         processed_bilets = set()
#         no_new_ticket_count = 0
#
#         while no_new_ticket_count < 3:  # Stop after 3 consecutive empty refreshes
#             found_new_ticket = False  # Track if any new tickets were processed
#
#             for index, coupon in bilets.iterrows():
#                 bilet_id = str(coupon["id"])  # Ensure it's a string
#
#                 # Check if already created
#                 if bilet_id in created_bilets or bilet_id in processed_bilets:
#                     continue  # Skip already processed tickets
#
#                 # Extract required fields
#                 race = coupon["race"]
#                 multiplier = coupon["multiplier"]
#                 atlar = coupon["atlar"]
#                 hipodrom = coupon["hipodrom"]
#                 bet = coupon["bet"]
#
#                 # Process the bilet
#                 create_bilet(driver, race, multiplier, atlar, hipodrom, bet)
#
#                 # Save newly created bilet
#                 save_created_bilet(bilet_id)
#
#                 # Mark bilet as processed in this session
#                 processed_bilets.add(bilet_id)
#                 created_bilets.add(bilet_id)  # Ensure it doesn't reappear after refresh
#                 found_new_ticket = True
#
#             if not found_new_ticket:
#                 no_new_ticket_count += 1
#                 print(f"\n🔄 No new tickets found. Attempt {no_new_ticket_count}/3.\n")
#             else:
#                 no_new_ticket_count = 0  # Reset counter if new tickets found
#
#             if no_new_ticket_count < 3:
#                 print("\n✅ Refreshing `my-output.json` to check for new tickets...\n")
#                 post_biletlerim_retrievedata(session)
#                 bilets = load_bilets_from_json("my-output.json")
#
#                 # Reapply hipodrom replacements and bet type filtering
#                 bilets["hipodrom"] = bilets["hipodrom"].replace(replacements)
#                 bilets = bilets[bilets["bet"].isin(betTypes) & (bilets["cancelable"] == True)]
#
#                 # Ensure no duplicates are reprocessed
#                 bilets = bilets[~bilets["id"].astype(str).isin(created_bilets)]
#
#         print("\n🚪 No new tickets found for 3 consecutive refreshes. Exiting.\n")
#
#     finally:
#         # Step 9: Close the browser
#         driver.quit()
#         print("All coupons processed and browser closed.")

def new_main():
    # Step 1: Load created bilet IDs
    created_bilets = load_created_bilets()

    # Step 2: Log in via Requests
    session = login_to_ebayi()

    # Step 3: Call /biletlerim to refresh/confirm token
    post_biletlerim(session)

    # Step 4: Set up Selenium
    driver = setup_selenium()
    login_to_site(driver, "cemalcandogan@gmail.com", "Covet13po.")

    # Normalize hipodrom names
    replacements = {
        "ANTALYA": "Antalya",
        "BURSA": "Bursa",
        "CAGNESSUR": "Cagnes Sur Mer Fransa",
        "CHELMSFORD": "Chelmsford City Birleşik Krallık",
        "FAIRVIEW": "Fairview Guney Afrika",
        "GULFSTREAM": "Gulfstream Park ABD",
        "ISTANBUL": "İstanbul",
        "IZMIR": "İzmir",
        "MAHONING": "Mahoning Valley ABD",
        "MOONEEVALL": "Moonee Valley Avustralya",
        "PARADISE": "Turf Paradise ABD",
        "PAKENHAM": "Pakenham Avustralya",
        "PHILADELPH": "Philadelphia ABD",
        "SANLIURFA": "Şanlıurfa",
        "SOUTHWELL": "Southwell Birleşik Krallık",
        "TURFFONTEI": "Turffontein Guney Afrika",
        "VAAL": "Vaal Guney Afrika",
        "WHAMPTON": "Wolverhampton Birleşik Krallık"
    }

    # Infinite loop to keep checking for new tickets
    while True:
        # 🟢 Always refresh my-output.json at the start of each cycle!
        print("\n🔄 Yeni biletler kontrol ediliyor...\n")
        post_biletlerim_retrievedata(session)

        # Step 5: Load bilets from JSON
        bilets = load_bilets_from_json("my-output.json")

        # Apply filters
        bilets["hipodrom"] = bilets["hipodrom"].replace(replacements)
        bilets = bilets[bilets["bet"].isin(betTypes) & (bilets["cancelable"] == True)]
        bilets = bilets[~bilets["id"].astype(str).isin(created_bilets)]  # Remove duplicates

        if bilets.empty:
            print(f"\n🚬 Bilet Yok! Sigara Molası: {sigara // 60} dakika...\n")
            for remaining in range(sigara, 0, -1):
                sys.stdout.write(f"\r⏳ Bekleniyor: {remaining} saniye kaldı... ")
                sys.stdout.flush()
                time.sleep(1)

            print("\n✅ Süre doldu! Tekrar kontrol ediliyor...\n")
            continue  # Restart loop

        # Track processed tickets and consecutive empty refreshes
        processed_bilets = set()
        no_new_ticket_count = 0

        while no_new_ticket_count < 3:  # Stop after 3 consecutive empty refreshes
            found_new_ticket = False  # Track if any new tickets were processed

            for index, coupon in bilets.iterrows():
                bilet_id = str(coupon["id"])  # Ensure it's a string

                # Check if already created
                if bilet_id in created_bilets or bilet_id in processed_bilets:
                    continue  # Skip already processed tickets

                # Extract required fields
                race = coupon["race"]
                multiplier = coupon["multiplier"]
                atlar = coupon["atlar"]
                hipodrom = coupon["hipodrom"]
                bet = coupon["bet"]

                # Process the bilet
                try:
                    create_bilet(driver, race, multiplier, atlar, hipodrom, bet)
                except CheckboxNotFoundException as e:
                    print(f"⚠️ {e} — Moving to the next ticket.")
                    driver.get("https://ebayi.tjk.org")  # Optional, reset back to home
                    continue  # Skip this ticket and move to the next one

                # Save newly created bilet
                save_created_bilet(bilet_id)

                # Mark bilet as processed in this session
                processed_bilets.add(bilet_id)
                created_bilets.add(bilet_id)  # Ensure it doesn't reappear after refresh
                found_new_ticket = True

            if not found_new_ticket:
                no_new_ticket_count += 1
                print(f"\n🔄 No new tickets found. Attempt {no_new_ticket_count}/3.\n")
            else:
                no_new_ticket_count = 0  # Reset counter if new tickets found

            if no_new_ticket_count < 3:
                print("\n✅ Refreshing `my-output.json` to check for new tickets...\n")
                post_biletlerim_retrievedata(session)
                bilets = load_bilets_from_json("my-output.json")

                # Reapply filters
                bilets["hipodrom"] = bilets["hipodrom"].replace(replacements)
                bilets = bilets[bilets["bet"].isin(betTypes) & (bilets["cancelable"] == True)]
                bilets = bilets[~bilets["id"].astype(str).isin(created_bilets)]

        print(f"\n🚬 Bilet Yok! Sigara Molası: {sigara // 60} dakika...\n")
        for remaining in range(sigara, 0, -1):
            sys.stdout.write(f"\r⏳ Bekleniyor: {remaining} saniye kaldı... ")
            sys.stdout.flush()
            time.sleep(1)

        print("\n✅ Süre doldu! Tekrar kontrol ediliyor...\n")

class CheckboxNotFoundException(Exception):
    pass
if __name__ == "__main__":
    new_main()
