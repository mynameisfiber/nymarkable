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
from selenium import webdriver
from PyPDF2 import PdfFileMerger


DRIVER = None


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
def create_edition_cli(output_file):
    with tempfile.TemporaryDirectory() as tempdir:
        articles = login_and_download(Path(tempdir))
        merge_pdfs(articles, output_file)


@cli.command("update-device")
@click.option("--device-ip", default="10.11.99.1", type=str)
@click.option("--filename", default="nytimes.pdf")
def update_device(device_ip, filename):
    with tempfile.TemporaryDirectory() as tempdir:
        tempdir = Path(tempdir)
        articles = login_and_download(tempdir)
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


@contextmanager
def create_driver(headless=False):
    global DRIVER
    if DRIVER is not None:
        yield DRIVER
        return
    chrome_options = webdriver.ChromeOptions()
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
    chrome_options.add_experimental_option("prefs", prefs)
    chrome_options.add_argument("--kiosk-printing")
    chrome_options.add_argument("--enable-print-browser")
    chrome_options.add_argument("user-data-dir=./browser_profile/")
    chrome_options.add_argument("window-size=1920,1080")
    if headless:
        chrome_options.add_argument("--headless")

    DRIVER = webdriver.Chrome(chrome_options=chrome_options)
    yield DRIVER
    DRIVER.quit()
    DRIVER = None


def login():
    print("logging in")
    with create_driver() as driver:
        driver.get("https://app.nytimes.com/")
        while True:
            print("waiting for browser to close")
            try:
                _ = driver.window_handles
            except selenium.common.exceptions.WebDriverException:
                break
            time.sleep(1)


def driver_click(driver, element):
    driver.execute_script("arguments[0].click();", element)


def download_pages(article_dir):
    with create_driver(headless=True) as driver:
        driver.get("https://app.nytimes.com/")
        cookies = driver.get_cookies()
        if not any(c["name"] == "NYT-S" for c in cookies):
            raise NotLoggedIn
        time.sleep(5)
        try:
            download = driver.find_element(
                By.XPATH, '//div[@class = "overlay"]/h2[text() = "Click to Read"]'
            )
            print("Downoading edition")
            download.click()
            time.sleep(5)
        except selenium.common.exceptions.NoSuchElementException:
            pass

        sections = driver.find_elements(
            By.CLASS_NAME,
            "accordion-section",
        )
        article_num = 0
        article_pdfs = []
        for section in sections:
            section.click()
            time.sleep(1)
            section_title = section.find_element(
                By.CLASS_NAME, "accordion-section-header-text"
            ).text
            headlines = section.find_elements(By.CLASS_NAME, "headline")
            for headline in headlines:
                article_filename = (
                    article_dir
                    / f"{article_num:04d}_{section_title.replace('/', '_')}_{headline.text.replace('/', '_')}.pdf"
                )
                try:
                    headline.click()
                    print("Article Filename:", article_filename)
                except (
                    selenium.common.exceptions.ElementClickInterceptedException,
                    selenium.common.exceptions.ElementNotInteractableException,
                ):
                    print("Skipping headline:", headline.text)
                    continue
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


def login_and_download(article_dir):
    while True:
        print("Attempting")
        try:
            return download_pages(article_dir)
            break
        except NotLoggedIn:
            login()


if __name__ == "__main__":
    cli()
