import pytesseract
import cv2
import numpy as np
from PIL import Image
import subprocess
import os

# 1. 스크린샷 캡처
def capture_screen(filename="screen.png"):
    subprocess.run("adb exec-out screencap -p > screen.png", shell=True)

# 2. 이미지에서 OCR 수행 + 'qa' 텍스트 탐색 + 위치 추출
def find_text_coordinates(image_path, target_text="qa"):
    img = cv2.imread(image_path)
    d = pytesseract.image_to_data(img, lang='kor', output_type=pytesseract.Output.DICT)

    for i, word in enumerate(d['text']):
        if word.lower() == target_text.lower():
            x, y, w, h = d['left'][i], d['top'][i], d['width'][i], d['height'][i]
            center_x = x + w // 2
            center_y = y + h // 2
            print(f"[✔] Found '{target_text}' at ({center_x}, {center_y})")
            return (center_x, center_y)

    print(f"[✖] '{target_text}' not found on screen.")
    return None

def print_all_ocr_text(image_path):
    img = cv2.imread(image_path)
    text = pytesseract.image_to_string(img, lang='Kor')
    print("OCR로 인식된 전체 텍스트:\n")
    print(text)

# 3. ADB 클릭
def tap_via_adb(x, y):
    subprocess.run(f"adb shell input tap {x} {y}", shell=True)

# 전체 실행 흐름
def test_click_qa_button():
    capture_screen()
    coords = find_text_coordinates("screen.png", "")
    if coords:
        tap_via_adb(*coords)
    else:
        print("Test failed: QA 버튼이 화면에 보이지 않습니다.")

# 실행
test_click_qa_button()
print_all_ocr_text("screen.png")
