from pathlib import Path

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By


options = Options()
options.add_argument("--headless=new")
options.add_argument("--window-size=1280,800")
options.add_argument("--no-sandbox")
driver = webdriver.Chrome(options=options)
try:
    driver.get("http://127.0.0.1:8080/login")
    assert "Swift" in driver.title
    assert driver.find_element(By.TAG_NAME, "h1").text == "Welcome to Swift"
    email = driver.find_element(By.CSS_SELECTOR, 'input[autocomplete="email"]')
    password = driver.find_element(By.CSS_SELECTOR, 'input[autocomplete="current-password"]')
    assert email.is_displayed() and password.is_displayed()
    driver.set_window_size(390, 844)
    assert driver.find_element(By.TAG_NAME, "h1").is_displayed()
    driver.save_screenshot(str(Path(__file__).with_name("selenium_mobile.png")))
    print("Selenium desktop/mobile smoke test passed")
finally:
    driver.quit()
