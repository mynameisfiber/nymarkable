#!/bin/env python3

import json
import time
from contextlib import contextmanager
import tempfile
from pathlib import Path
import base64


import click
import requests

import selenium
from selenium.webdriver.common.by import By
from selenium.common.exceptions import (
    WebDriverException,
    ElementClickInterceptedException,
    ElementNotInteractableException,
)
from selenium import webdriver
from PyPDF2 import PdfFileMerger


DRIVER = None
CONFIG_DIR = Path("~/.nymarkable").expanduser()
CONFIG_DIR.mkdir(exist_ok=True)


class NotLoggedIn(Exception):
    pass


@click.group()
def cli():
    pass


@cli.command("login")
def login_cli():
    return login()


@cli.command("create-edition")
@click.argument("output-file", type=click.Path(dir_okay=False, writable=True))
@click.option("--section", multiple=True, type=str, default=None)
def create_edition_cli(output_file, section):
    with tempfile.TemporaryDirectory(dir=CONFIG_DIR) as tempdir:
        articles = login_and_download(Path(tempdir), allow_sections=section)
        merge_pdfs(articles, output_file)


@cli.command("update-device")
@click.option("--device-ip", default="10.11.99.1", type=str)
@click.option("--filename", default="nytimes.pdf")
@click.option("--section", multiple=True, type=str, default=None)
def update_device(device_ip, filename, section):
    with tempfile.TemporaryDirectory(dir=CONFIG_DIR) as tempdir:
        tempdir = Path(tempdir)
        articles = login_and_download(tempdir, allow_sections=section)
        merge_pdfs(articles, tempdir / "output.pdf")
        headers = {
            "Origin": f"http://{device_ip}",
            "Accept": "*/*",
            "Referer": f"http://{device_ip}/",
            "Connection": "keep-alive",
        }
        files = {
            "file": (
                f"file=@{filename};filename={filename};type=application/pdf",
                (tempdir / "output.pdf").open("rb"),
            ),
        }
        requests.post(f"http://{device_ip}/upload", headers=headers, files=files)


@cli.command("sections")
def list_sections_cli():
    with create_driver(headless=True) as driver:
        sections = load_edition_list_sections(driver)
        for section in sections:
            section_title = section.find_element(
                By.CLASS_NAME, "accordion-section-header-text"
            ).text
            click.echo(section_title)


@contextmanager
def create_driver(headless=False):
    global DRIVER
    if DRIVER is not None:
        yield DRIVER
        return
    chrome_options = webdriver.ChromeOptions()
    profile_dir = CONFIG_DIR / "browser_profile/"
    chrome_options.add_argument(f"user-data-dir={profile_dir}/")

    settings = {
        "recentDestinations": [
            {
                "id": "Save as PDF",
                "origin": "local",
                "account": "",
            }
        ],
        "selectedDestinationId": "Save as PDF",
        "version": 2,
    }
    prefs = {
        "printing.print_preview_sticky_settings.appState": json.dumps(settings),
    }
    chrome_options.add_argument("start-maximized")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option("useAutomationExtension", False)
    chrome_options.add_experimental_option("prefs", prefs)
    chrome_options.add_argument("kiosk-printing")
    chrome_options.add_argument("enable-print-browser")
    chrome_options.add_argument("window-size=1920,1080")
    if headless:
        chrome_options.add_argument("--headless")

    try:
        DRIVER = webdriver.Chrome(chrome_options=chrome_options)
        yield DRIVER
        DRIVER.quit()
    except WebDriverException as e:
        if (
            e.msg == "unknown error: failed to write prefs file"
            or e.msg == "unknown error: cannot create default profile directory"
            or "user-data-dir" in e.msg
        ):
            raise Exception(
                "Could not write chromium profile. Make sure chromium can "
                f"write to {CONFIG_DIR}. This may happen if you installed "
                "chromium with snap without setting --devmode."
            )
        raise e
    finally:
        DRIVER = None


def login():
    print("logging in")
    with create_driver(headless=False) as driver:
        driver.get("https://app.nytimes.com/")
        while True:
            if is_logged_in(driver):
                print("Sucessfully logged in")
                return
            try:
                _ = driver.window_handles
            except selenium.common.exceptions.WebDriverException:
                break
            time.sleep(1)


def is_logged_in(driver):
    cookies = driver.get_cookies()
    if not any(c["name"] == "NYT-S" for c in cookies):
        return False
    return True


def driver_click(driver, element):
    driver.execute_script("arguments[0].click();", element)


def load_edition_list_sections(driver):
    driver.get("https://app.nytimes.com/")
    if not is_logged_in(driver):
        raise NotLoggedIn
    time.sleep(5)
    try:
        download = driver.find_element(
            By.XPATH, '//div[@class = "overlay"]/h2[text() = "Click to Read"]'
        )
        print("Downoading edition")
        download.click()
        time.sleep(3)
    except selenium.common.exceptions.NoSuchElementException:
        pass
    
    sections = driver.find_elements(
        By.CLASS_NAME,
        "accordion-section",
    )
    return sections


def download_pages(article_dir, allow_sections=None):
    with create_driver(headless=True) as driver:
        sections = load_edition_list_sections(driver)
        article_num = 0
        article_pdfs = []
        for section in sections:
            section_title = section.find_element(
                By.CLASS_NAME, "accordion-section-header-text"
            ).text
            if allow_sections and section_title not in allow_sections:
                print("Skipping section:", section_title)
                continue
            section.click()
            time.sleep(2)
            headlines = section.find_elements(By.CLASS_NAME, "headline")
            for headline in headlines:
                article_filename = article_dir / (
                    f"{article_num:04d}_"
                    f"{section_title.replace('/', '_')}_"
                    f"{headline.text.replace('/', '_')}.pdf"
                )
                try:
                    headline.click()
                    print("Article Filename:", article_filename)
                except (
                    ElementClickInterceptedException,
                    ElementNotInteractableException,
                ):
                    print("Skipping headline:", headline.text)
                    continue
                time.sleep(1)
                print_pdf(driver, article_filename)
                article_pdfs.append(
                    {"filename": article_filename, "headline": headline.text}
                )
                article_num += 1
    return article_pdfs


def print_pdf(driver, output):
    pdf = driver.execute_cdp_cmd("Page.printToPDF", {"printBackground": True})
    with open(output, "wb") as fd:
        fd.write(base64.b64decode(pdf["data"]))


def merge_pdfs(articles, output):
    merger = PdfFileMerger()
    for article in articles:
        merger.append(str(article["filename"].resolve()), bookmark=article["headline"])
    merger.write(str(output))
    merger.close()


def login_and_download(article_dir, allow_sections=None):
    while True:
        print("Attempting")
        try:
            return download_pages(article_dir, allow_sections=allow_sections)
            break
        except NotLoggedIn:
            login()


if __name__ == "__main__":
    cli()
