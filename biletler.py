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

# CEMAL TEST
# sourceAccount = "cemalcandogan@gmail.com"
# sourcePassword = "Covet13po."

# targetAccount = "cemalcandogan@gmail.com"
# targetPassword = "Covet13po."

#  CAN TEST
targetAccount = "candemirel96@gmail.com"
targetPassword = "O123Gelincik"

# betTypes = ["6'lı Ganyan","5'li Ganyan","4'lü Ganyan","3'lü Ganyan","Çifte Bahis","Sıralı İkili Bahis"]
betTypes = ["5'li Ganyan"]
sigara = 20
max_amount_by_race_type = {
    "Ganyan": 99,
    "6'lı Ganyan": 100,
    "Çifte Bahis": 80,
    "Sıralı İkili Bahis": 80
}
min_amount_by_race_type = {
    "Ganyan": 11,
    "6'lı Ganyan": 5,
    "Çifte Bahis": 8,
    "Sıralı İkili Bahis": 80
}
# Normalize hipodrom name
replacements = {
    "ADANA": "Adana",
    "ANTALYA": "Antalya",
    "AVUBELMONT": "Belmont Avustralya",
    "BORELY": "Marseille Borely Fransa",
    "BURSA": "Bursa",
    "CAGNESSUR": "Cagnes Sur Mer Fransa",
    "CHANTILLY": "Chantilly Fransa",
    "CHELMSFORD": "Chelmsford City Birleşik Krallık",
    "DUBAI": "Meydan Dubai",
    "DURBANVILL": "Durbanville Guney Afrika",
    "FAIRVIEW": "Fairview Guney Afrika",
    "GREYVILLE": "Greyville Guney Afrika",
    "GULFSTREAM": "Gulfstream Park ABD",
    "HAPPYVALLE": "Happy Valley Hong Kong",
    "ISTANBUL": "İstanbul",
    "IZMIR": "İzmir",
    "KENILWORTH": "Kenilworth Guney Afrika",
    "KEMPTON": "Kempton Park Birleşik Krallık",
    "LAUNCESTON": "Launceston Avustralya",
    "LAUREL": "Laurel Park ABD",
    "LEMANS": "Le Mans Fransa",
    "LINGFIELD": "Lingfield Birleşik Krallık",
    "LYON": "Lyon la Soie Fransa",
    "MAHONING": "Mahoning Valley ABD",
    "MOONEEVALL": "Moonee Valley Avustralya",
    "NARROGIN": "Narrogin Avustralya",
    "NEWCASTLE": "Newcastle Birleşik Krallık",
    "PAKENHAM": "Pakenham Avustralya",
    "PARADISE": "Turf Paradise ABD",
    "PAU": "Pau Fransa",
    "PERTHASCOT": "Perth Ascot Avustralya",
    "PHILADELPH": "Philadelphia ABD",
    "PINJARRA": "Pinjarra Park Avustralya",
    "PORNICHET": "Pornichet La Baule Fransa",
    "RIYAD": "Riyad Suudi Arabistan",
    "ROGERSDOWN": "Will Rogers Downs ABD",
    "SAINTCLOUD": "Saint Cloud Fransa",
    "SANLIURFA": "Şanlıurfa",
    "SANTAANITA": "Santa Anita Park ABD",
    "SCOTTSVILL": "Scottsville Guney Afrika",
    "SHATIN": "Sha Tin Hong Kong",
    "SOUTHWELL": "Southwell Birleşik Krallık",
    "TOOWOOMBA": "Toowoomba Avustralya",
    "TOULOUSE": "Toulouse Fransa",
    "TURFFONTEI": "Turffontein Guney Afrika",
    "VAAL": "Vaal Guney Afrika",
    "WHAMPTON": "Wolverhampton Birleşik Krallık"

}


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
        "limit": "100",
        "offset": "0,0",
        "order": "desc",
        "status": "played",
    }

    attempts = 0
    while attempts < 3:
        try:
            resp = session.post(url, headers=headers, data=payload)
            resp.raise_for_status()
            json_resp = resp.json()
            save_json_to_file(json_resp, "my-output.json")
            print("Tickets refreshed successfully.")
            return json_resp
        except (requests.ConnectionError, requests.Timeout, ConnectionResetError) as e:
            print(f"Connection error: {e}. Retrying in 5 seconds...")
            attempts += 1
            time.sleep(5)

    print("Failed to refresh tickets after 3 attempts.")


def save_json_to_file(json_resp, filename="response.json"):
    """
    Saves the given JSON object to a file with pretty indentation.
    """
    with open(filename, "w", encoding="utf-8") as f:
        # ensure_ascii=False allows non-ASCII characters to be preserved
        # indent=4 makes the file more readable (pretty-printed)
        json.dump(json_resp, f, ensure_ascii=False, indent=4)

    # print(f"JSON response successfully saved to {filename}")


def load_bilets_from_json(json_file):
    """
    Loads specific coupon data from a JSON file and returns them as a Pandas DataFrame.

    Args:
        json_file (str): Path to the JSON file containing bilets data.

    Returns:
        pd.DataFrame: DataFrame containing filtered coupons data with only specified fields.
    """
    # Define the fields you want to extract from each coupon
    desired_fields = ['id', 'race', 'multiplier', 'atlar', 'hipodrom', 'bet', 'cancelable', 'cost']

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
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--disable-software-rasterizer")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-gpu")  # Crucial for GPU error
    chrome_options.add_argument("--log-level=3")  # Suppresses errors and warnings

    # Initialize the Service object with the path to chromedriver.exe
    service = Service(executable_path="chromedriver.exe")

    # Initialize the Chrome WebDriver with the Service object
    driver = webdriver.Chrome(service=service, options=chrome_options)
    driver.maximize_window()
    return driver


def login_to_site(driver, username, password):
    # Navigate to the login page

    driver.get("https://ebayi.tjk.org")  # Adjust URL if different

    # Initialize WebDriverWait with a 20-second timeout
    wait = WebDriverWait(driver, 2)

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
        time.sleep(1)  # Adjust as needed based on website's response time

        # Call the navigate_to_bahis_yap function to go to 'BAHİS YAP' page


    except Exception as e:
        # On any unexpected error, take a screenshot and exit
        driver.save_screenshot("login_error.png")
        print(f"An error occurred during login: {e}. Screenshot saved as 'login_error.png'. Exiting.")
        driver.quit()
        exit(1)


def close_invalid_race_popup(driver):
    try:
        modal_close_button = driver.find_element(By.XPATH,
                                                 "//div[contains(@class, 'invalid-race')]//button[text()='Tamam']")
        modal_close_button.click()
        print("Closed the invalid race modal.")
        time.sleep(1)  # Let it settle
        return True
    except NoSuchElementException:
        return False


def create_bilet(driver, race, multiplier, atlar, hipodrom, bet):
    try:
        # Step 0: Ensure we are on the main page
        driver.get("https://ebayi.tjk.org")
        print("Navigated to the main page.")

        # Step 1: Click on the 'BAHİS YAP' link with modal check
        max_attempts = 3
        close_invalid_race_popup(driver)
        for attempts in range(1, max_attempts + 1):
            try:
                bahis_yap_link = driver.find_element(By.XPATH,
                                                     "//a[contains(@href, '/bahis-yap-advanced') and contains(text(), 'BAHİS YAP')]")
                bahis_yap_link.click()
                print(f"Clicked on 'BAHİS YAP' link. (Attempt {attempts}/{max_attempts})")
                break  # Success
            except Exception as e:
                if close_invalid_race_popup(driver):
                    print(f"⚠️ Modal closed. Retrying ({attempts}/{max_attempts})...")
                else:
                    print(f"Unexpected click interception: {e}")
            time.sleep(1)

        if attempts == max_attempts:
            print("❌ Failed to click 'BAHİS YAP' after multiple attempts due to modal issues.")
            time.sleep(1)  # short pause before refreshing
            driver.get("https://ebayi.tjk.org")
            return

        # Step 1.5: Clear bilet
        try:
            clear_button = driver.find_element(By.XPATH, "//button[@data-selector='clear-button']")
            clear_button.click()
            print("Clicked on 'Clear Bilet' button.")
        except NoSuchElementException:
            print("Clear Bilet button not found. Continuing without clicking.")

        # time.sleep(1)

        # Step 2: Select Hipodrom
        try:
            dropdown_toggle = driver.find_element(By.CSS_SELECTOR, "a.btn.btn-glossred.dropdown-toggle")
            dropdown_toggle.click()
            print("Clicked on the dropdown toggle to expand the submenu.")

            hipodrom_xpath = f"//a[@class='dropdown-item' and text()='{hipodrom}']"
            hipodrom_element = driver.find_element(By.XPATH, hipodrom_xpath)
            hipodrom_element.click()
            print(f"Selected hipodrom: {hipodrom}")
        except Exception as e:
            print(f"⚠️ Failed to select hipodrom: {e}")
            time.sleep(1)  # short pause before refreshing
            driver.get("https://ebayi.tjk.org")
            return

        # Step 3: Select Bet Type
        try:
            dropdown_toggles = driver.find_elements(By.CSS_SELECTOR, "a.btn.btn-glossred.dropdown-toggle")
            if len(dropdown_toggles) >= 2:
                dropdown_toggles[1].click()
                print("Clicked on the second dropdown toggle")
            else:
                print("Less than two dropdown toggles found.")

            bet_xpath = f'//a[@class="dropdown-item" and text()="{bet}"]'
            bet_element = driver.find_element(By.XPATH, bet_xpath)
            bet_element.click()
            print(f"Selected bet: {bet}")
        except Exception as e:
            print(f"⚠️ Failed to select bet type: {e}")
            time.sleep(1)  # short pause before refreshing
            driver.get("https://ebayi.tjk.org")
            return

        # Step 4: Select Horses
        runs = atlar.split("/")
        for run_index, run_data in enumerate(runs, start=1):
            horses = run_data.split(",")
            for horse_no in horses:
                horse_no = horse_no.strip()
                horse_id = f"run-{run_index}-horse-{horse_no}"
                try:
                    label = driver.find_element(By.XPATH, f"//label[@for='{horse_id}']")
                    driver.execute_script("arguments[0].scrollIntoView(true);", label)
                    actions = ActionChains(driver)
                    actions.move_to_element(label).click().perform()
                    print(f"Selected horse: Run {run_index}, Horse {horse_no}")
                except Exception as e:
                    print(f"⚠️ Failed to select horse {horse_id}: {e}")

        # Step 5: Set Multiplier
        try:
            multiplier_input = driver.find_element(By.XPATH, "//input[@type='number' and @placeholder='Misli']")
            multiplier = max(1, min(multiplier, 3250))
            multiplier_input.clear()  # First try standard clear
            multiplier_input.send_keys(Keys.CONTROL + "a")  # Highlight all text
            multiplier_input.send_keys(Keys.DELETE)  # Delete highlighted text
            multiplier_input.send_keys(str(multiplier))
            print(f"Entered multiplier value: {multiplier}")
        except Exception as e:
            print(f"⚠️ Failed to set multiplier: {e}")
            time.sleep(1)  # short pause before refreshing
            driver.get("https://ebayi.tjk.org")
            return

        # Step 6: Click OYNA
        try:
            button = driver.find_element(By.XPATH, "//button[text()='OYNA']")
            button.click()
            print("Clicked the submit button to create the bilet.")
        except Exception as e:
            print(f"⚠️ Failed to click 'OYNA': {e}")
            time.sleep(1)  # short pause before refreshing
            driver.get("https://ebayi.tjk.org")
            return

        # Step 7: Checkbox & Onayla
        checkbox_appeared = False
        for _ in range(30):
            try:
                label = driver.find_element(By.XPATH, "//label[@for='approveChecksum']")
                driver.execute_script("arguments[0].scrollIntoView(true);", label)
                actions = ActionChains(driver)
                actions.move_to_element(label).click().perform()
                print("Selected the checkbox in the confirmation pop-up.")
                checkbox_appeared = True
                break
            except NoSuchElementException:
                time.sleep(1)

        if not checkbox_appeared:
            print("❌ Checkbox pop-up did not appear.")
            time.sleep(1)  # short pause before refreshing
            driver.get("https://ebayi.tjk.org")
            return

        # Step 8: Onayla
        try:
            approve_button = driver.find_element(By.ID, "approveButton")
            approve_button.click()
            print("Clicked the 'Onayla' button to finalize the bilet.")
        except Exception as e:
            print(f"⚠️ Failed to click 'Onayla': {e}")
            time.sleep(1)
            driver.get("https://ebayi.tjk.org")
            return False  # ❌ Failure

        # Step 9: Return to Main Page
        driver.get("https://ebayi.tjk.org")
        print("✅ Bilet created successfully. Navigated back to the main page.")

        return True  # ✅ Success

    except Exception as e:
        print(f"❌ Unexpected Error in Bilet Creation: {e}")
    driver.get("https://ebayi.tjk.org")
    return False  # ❌ Failure


def create_bilet_faster(driver, race, multiplier, atlar, hipodrom, bet, created_bilets):
    try:
        wait = WebDriverWait(driver, 5)  # Faster wait instead of sleep

        # Ensure bilet is not already created
        bilet_id = f"{hipodrom}_{race}_{bet}_{atlar}_{multiplier}"  # Unique identifier
        if bilet_id in created_bilets:
            print(f"⚠️ Bilet {bilet_id} already created, skipping...")
            return False

        # Step 1: Ensure we are on the 'BAHİS YAP' page
        driver.get("https://ebayi.tjk.org/bahis-yap-advanced")
        print("Navigated to 'BAHİS YAP' page.")

        # Step 1.5: Clear previous selections if any
        try:
            clear_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[@data-selector='clear-button']")))
            clear_button.click()
            print("Clicked on 'Clear Bilet' button.")
        except Exception:
            print("Clear Bilet button not found, continuing.")

        # Step 2: Select Hipodrom
        try:
            dropdown_toggle = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "a.btn.btn-glossred.dropdown-toggle")))
            dropdown_toggle.click()
            hipodrom_element = wait.until(EC.element_to_be_clickable((By.XPATH, f"//a[@class='dropdown-item' and text()='{hipodrom}']")))
            hipodrom_element.click()
            print(f"✅ Selected hipodrom: {hipodrom}")
        except Exception:
            print(f"⚠️ Failed to select hipodrom: {hipodrom}")
            return False

        # Step 3: Select Bet Type
        try:
            dropdown_toggles = driver.find_elements(By.CSS_SELECTOR, "a.btn.btn-glossred.dropdown-toggle")
            if len(dropdown_toggles) >= 2:
                dropdown_toggles[1].click()
            bet_element = wait.until(EC.element_to_be_clickable((By.XPATH, f'//a[@class="dropdown-item" and text()="{bet}"]')))
            bet_element.click()
            print(f"✅ Selected bet: {bet}")
        except Exception:
            print(f"⚠️ Failed to select bet type: {bet}")
            return False

        # Step 4: Select Horses (Bulk Optimization)
        try:
            runs = atlar.split("/")
            for run_index, run_data in enumerate(runs, start=1):
                horse_labels = {label.get_attribute("for"): label for label in driver.find_elements(By.XPATH, f"//label[starts-with(@for, 'run-{run_index}-horse-')]")}
                for horse_no in run_data.split(","):
                    horse_id = f"run-{run_index}-horse-{horse_no.strip()}"
                    if horse_id in horse_labels:
                        driver.execute_script("arguments[0].click();", horse_labels[horse_id])  # JavaScript click for instant response
                        print(f"✅ Selected horse: Run {run_index}, Horse {horse_no}")
                    else:
                        print(f"⚠️ Horse {horse_no} not found in Run {run_index}, skipping.")
        except Exception:
            print("⚠️ Error selecting horses.")

        # Step 5: Set Multiplier
        try:
            multiplier_input = wait.until(EC.element_to_be_clickable((By.XPATH, "//input[@type='number' and @placeholder='Misli']")))
            driver.execute_script("arguments[0].value = '';", multiplier_input)  # Clears value directly
            multiplier_input.send_keys(str(min(max(multiplier, 1), 3250)))  # Ensure within range
            print(f"✅ Entered multiplier value: {multiplier}")
        except Exception:
            print("⚠️ Failed to set multiplier.")
            return False

        # Step 6: Click 'OYNA'
        try:
            button = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[text()='OYNA']")))
            button.click()
            print("✅ Clicked the 'OYNA' button.")
        except Exception:
            print("⚠️ Failed to click 'OYNA'.")
            return False

        # Step 7: Checkbox & Onayla
        checkbox_appeared = False
        for _ in range(30):
            try:
                label = driver.find_element(By.XPATH, "//label[@for='approveChecksum']")
                driver.execute_script("arguments[0].scrollIntoView(true);", label)
                actions = ActionChains(driver)
                actions.move_to_element(label).click().perform()
                print("Selected the checkbox in the confirmation pop-up.")
                checkbox_appeared = True
                break
            except NoSuchElementException:
                time.sleep(1)

        if not checkbox_appeared:
            print("❌ Checkbox pop-up did not appear.")
            time.sleep(1)  # short pause before refreshing
            driver.get("https://ebayi.tjk.org")
            return

        # Step 8: Onayla
        try:
            approve_button = driver.find_element(By.ID, "approveButton")
            approve_button.click()
            print("Clicked the 'Onayla' button to finalize the bilet.")
        except Exception as e:
            print(f"⚠️ Failed to click 'Onayla': {e}")
            time.sleep(1)
            driver.get("https://ebayi.tjk.org")
            return False  # ❌ Failure

        # ✅ SUCCESS: Mark the Bilet as Created
        created_bilets.add(bilet_id)  # Add to memory
        save_created_bilet(bilet_id)  # Save to file
        print(f"🎉 Bilet created successfully! {bilet_id} marked as done.")
        time.sleep(1)
        return True  # ✅ Success

    except Exception as e:
        print(f"❌ Unexpected Error: {e}")
        return False  # ❌ Failure

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


def main_faster():
    # Step 1: Load created bilet IDs
    created_bilets = load_created_bilets()

    # Step 2: Log in via Requests
    session = login_to_ebayi()

    # Step 3: Call /biletlerim to refresh/confirm token
    post_biletlerim(session)

    processed_bilets = set()
    cycle_count = 0  # Track how many cycles we've done

    # Infinite loop to keep checking for new tickets
    while True:
        # 🚨 Restart Selenium after every 5 cycles
        if cycle_count % 10 == 0:
            if cycle_count > 0:
                print(f"\n🔄 Restarting Selenium after {cycle_count} cycles...\n")
                driver.quit()

            driver = setup_selenium()
            login_to_site(driver, targetAccount, targetPassword)

        print(f"\n🔄 [Cycle {cycle_count + 1}] Checking for new tickets...\n")
        post_biletlerim_retrievedata(session)

        bilets = load_bilets_from_json("my-output.json")

        if bilets.empty:
            print(f"\n🚬 No tickets found! Waiting {sigara} seconds...\n")
            for remaining in range(sigara, 0, -1):
                sys.stdout.write(f"\r⏳ Waiting: {remaining} seconds left... ")
                sys.stdout.flush()
                time.sleep(1)

            print("\n✅ Break over! Checking again...\n")
            cycle_count += 1
            continue

        bilets["hipodrom"] = bilets["hipodrom"].replace(replacements)
        # Ensure 'cost' is properly converted to float, invalid values become NaN
        bilets["cost"] = pd.to_numeric(bilets["cost"], errors='coerce').fillna(0)

        # Apply both min and max filters with safe mapping

        bilets = bilets[
            (bilets["bet"].isin(betTypes)) &
            (bilets["cancelable"] == True) &
            (bilets["cost"] <= bilets["bet"].map(max_amount_by_race_type).fillna(float('inf')))
            ]
        # Apply min filter and print count
        bilets = bilets[bilets["cost"] >= bilets["bet"].map(min_amount_by_race_type).fillna(0)]
        bilets = bilets[~bilets["id"].astype(str).isin(created_bilets)]

        no_new_ticket_count = 0

        while no_new_ticket_count < 3:
            found_new_ticket = False

            for index, coupon in bilets.iterrows():
                bilet_id = str(coupon["id"])

                if bilet_id in created_bilets or bilet_id in processed_bilets:
                    continue

                race = coupon["race"]
                multiplier = coupon["multiplier"]
                atlar = coupon["atlar"]
                hipodrom = coupon["hipodrom"]
                bet = coupon["bet"]

                success = create_bilet_faster(driver, race, multiplier, atlar, hipodrom, bet, created_bilets)

                if success:
                    save_created_bilet(bilet_id)
                    created_bilets = load_created_bilets()
                    processed_bilets.add(bilet_id)
                    found_new_ticket = True
                else:
                    print(f"❌ Bilet creation failed for ID {bilet_id}. Skipping.")

            if not found_new_ticket:
                no_new_ticket_count += 1
                print(f"\n🔄 No new tickets found. Attempt {no_new_ticket_count}/3.\n")
            else:
                no_new_ticket_count = 0

            if no_new_ticket_count < 3:
                print("\n✅ Refreshing `my-output.json` to check for new tickets...\n")
                post_biletlerim_retrievedata(session)
                bilets = load_bilets_from_json("my-output.json")
                bilets["hipodrom"] = bilets["hipodrom"].replace(replacements)
                bilets["cost"] = pd.to_numeric(bilets["cost"], errors='coerce')
                bilets = bilets[
                    (bilets["bet"].isin(betTypes)) &
                    (bilets["cancelable"] == True) &
                    (bilets["cost"].astype(float) <= bilets["bet"].map(max_amount_by_race_type).fillna(float('inf')))
                    ]
                bilets = bilets[bilets["cost"] >= bilets["bet"].map(min_amount_by_race_type).fillna(0)]
                bilets = bilets[~bilets["id"].astype(str).isin(created_bilets)]

        print(f"\n🚬 No new tickets! Waiting {sigara} seconds...\n")
        for remaining in range(sigara, 0, -1):
            sys.stdout.write(f"\r⏳ Waiting: {remaining} seconds left... ")
            sys.stdout.flush()
            time.sleep(1)

        print("\n✅ Break over! Checking again...\n")

        cycle_count += 1  # Increment the cycle counter


class CheckboxNotFoundException(Exception):
    pass


if __name__ == "__main__":
    main_faster()
