import time
import json
import csv
from pathlib import Path
from seleniumbase import Driver
import yaml
import os
from dotenv import load_dotenv

def load_driver():
    driver = Driver(uc = True)
    return driver

def load_cookies(driver, cookie_file: Path):
    with open(cookie_file, "r") as file:
        cookies = json.load(file)
        for cookie in cookies:
            clean_cookie = {
                "name": cookie["name"],
                "value": cookie["value"],
                "path": cookie.get("path", "/")
            }
            driver.add_cookie(clean_cookie)

def save_data(path: Path, data: dict):
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames = data[0].keys())
        writer.writeheader()
        writer.writerows(data)
    print(f"✅ Data of rows: {len(data)} saved to {path}")    

def load_config(config_path: Path):
    """Loads configuration from a YAML file."""
    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        return config
    except FileNotFoundError:
        print(f"Error: Configuration file '{config_path}' not found.")
        return None
    except yaml.YAMLError as e:
        print(f"Error parsing YAML file: {e}")
        return None

def load_api_credentials():
    load_dotenv()  # Load environment variables from .env file
    api_key = os.getenv("API_KEY")
    base_url = os.getenv("BASE_URL")

    if not api_key:
        raise ValueError("API_KEY not found in environment variables or .env file.")
    if not base_url:
        raise ValueError("BASE_URL not found in environment variables or .env file.")

    return api_key, base_url
