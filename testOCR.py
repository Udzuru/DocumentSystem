import os
import re
from pdf2image import convert_from_path
import pytesseract
from pytrovich.enums import NamePart, Gender, Case
from pytrovich.maker import PetrovichDeclinationMaker

# Укажите путь к Tesseract
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
maker = PetrovichDeclinationMaker()

# Шаг 1: Преобразование PDF в изображения
def pdf_to_images(pdf_path):
    images = convert_from_path(pdf_path,poppler_path = r"D:\Release-24.08.0-0\poppler-24.08.0\Library\bin")
    return images

# Шаг 2: Распознавание текста с помощью Tesseract
def ocr_images(images):
    text = ""
    for image in images:
        text += pytesseract.image_to_string(image, lang='rus') + "\n"
    return text


# Шаг 3: Поиск имен
def find_names(text, names_list):
    found_names = []
    for name in names_list:
        name1=maker.make(NamePart.LASTNAME, Gender.MALE, Case.ACCUSATIVE, "Мустафин")  # Винительный 
        name2=maker.make(NamePart.LASTNAME, Gender.MALE, Case.DATIVE, "Мустафин")  # Дательный
        name3=maker.make(NamePart.LASTNAME, Gender.MALE, Case.GENITIVE, "Мустафин")  # Родительный 
        name4=maker.make(NamePart.LASTNAME, Gender.MALE, Case.INSTRUMENTAL, "Мустафин")  # Творительный
        name5=maker.make(NamePart.LASTNAME, Gender.MALE, Case.PREPOSITIONAL, "Мустафин")  # Предложный
        if re.search(r'\b' + re.escape(name) + r'\b', text) or re.search(r'\b' + re.escape(name1) + r'\b', text) or re.search(r'\b' + re.escape(name2) + r'\b', text) or re.search(r'\b' + re.escape(name3) + r'\b', text) or re.search(r'\b' + re.escape(name4) + r'\b', text) or re.search(r'\b' + re.escape(name5) + r'\b', text):
            found_names.append(name)
    return found_names


def find_names_all(names_list,pdf_path):

# Преобразование PDF в изображения
    images = pdf_to_images(pdf_path)

# Распознавание текста
    text = ocr_images(images)

# Поиск имен
    found_names = find_names(text, names_list)

    return found_names
