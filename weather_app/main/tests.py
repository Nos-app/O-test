# from django.test import TestCase
from selenium import webdriver
from selenium.webdriver.common.by import By
import pytest
from loguru import logger
import time
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

logger.add("logs/logs.log", level="DEBUG", format="{time} {message}")

url_for_open = "http://127.0.0.1:8000/"


@pytest.fixture
def driver():
    driver = webdriver.Chrome()
    yield driver
    driver.quit()


class WeathersPage:
    """Пусть будет объект страницы"""

    def __init__(self, driver):
        """инициализация драйвера"""
        self.driver = driver

    def open(self, url):
        """Функция открытия сраницы с прокидывнием в неё url"""
        self.driver.get(url)

    def find_element_by_css(self, selector):
        """метод поиска элемента по css селектору"""
        return self.driver.find_element(By.CSS_SELECTOR, f".{selector}")

    def find_link(self, text):
        """Метод поиска просто ссылки по тексту"""
        link = self.driver.find_element(By.XPATH, f".//a[contains(text(), '{text}')]")
        return link

    def find_element_with_text(self, text):
        """метод поиска элемента по тексту"""
        return self.driver.find_element(By.XPATH, f"//*[contains(text(), '{text}')]")

    def find_element_by_id(self, id):
        """Поиск элемента по id"""
        partners = self.driver.find_element(By.ID, id)
        return partners

    def find_element_by_tag(self, tag):
        """Поиск элемента по id"""
        partners = self.driver.find_element(By.TAG_NAME, tag)
        return partners


# Тесты
def test_wheather_page_open(driver):
    wheather_page = WeathersPage(driver)
    wheather_page.open(url_for_open)
    current_url = driver.current_url
    expected_url = "http://127.0.0.1:8000/"
    head_wheather_page = wheather_page.find_element_with_text(
        "Узнай погоду в любом городе"
    )
    if current_url == expected_url and head_wheather_page:
        logger.info("Открытие страницы успешно, заглавие найдено")
    else:
        logger.error(
            f"Что-то пошло не так! Ожидаемый URL: {expected_url}, текущий URL: {current_url} Заглавие - {head_wheather_page} тест провален"
        )
    assert current_url == expected_url and head_wheather_page, "что-то пошло не так!!!"


def test_get_wheather(driver):
    wheather_page = WeathersPage(driver)
    wheather_page.open(url_for_open)
    text_input = driver.find_element(By.ID, "cityInput")
    text_input.click()
    time.sleep(2)
    text_input.send_keys("Москва")
    time.sleep(2)
    send_button = wheather_page.find_element_by_tag("button")
    send_button.click()
    time.sleep(2)
    wheather_block = wheather_page.find_element_with_text("Прогноз на ближайшее время:")
    additional_element = wheather_page.find_element_with_text("°C")
    if wheather_block and additional_element:
        logger.info("Погода найдена, тест №2 пройден")
    else:
        logger.error(
            "Тест №2 провален, элементы страницы указывающие погоду не найдены"
        )
    assert wheather_block and additional_element, "Тест №2 провален"


def test_check_cookie_last_city(driver):
    wheather_page = WeathersPage(driver)
    wheather_page.open(url_for_open)
    text_input = driver.find_element(By.ID, "cityInput")
    text_input.click()
    time.sleep(2)
    text_input.send_keys("Москва")
    time.sleep(2)
    send_button = wheather_page.find_element_by_tag("button")
    send_button.click()
    time.sleep(2)
    driver.back()
    time.sleep(1)
    head_last_serch_of_city = wheather_page.find_element_with_text(
        "Последние города в которых Вы смотрели погоду"
    )
    last_city_block = wheather_page.find_element_by_id("city")
    if head_last_serch_of_city and last_city_block:
        logger.info(
            "История из куки файлов найдена, елементы добавлены на страницу, тест №3 пройден"
        )
    else:
        logger.error("Тест №3 провален, История из куки файлов не найдена")
    assert head_last_serch_of_city and last_city_block, "Тест №3 провален"
