import os
import cv2
import numpy as np
import glob
import time
from PIL import Image, ImageDraw, ImageFont
from typing import Optional, Tuple

from util.adb_util import tap_on_device, ensure_adb_connection, capture_screen

FONT_PATH = "./NotoSansKR-Bold.ttf"
FONT_SIZE = 36
PADDING = 10
TEMPLATE_PATH = "template.png"
SCREENSHOT_PATH = "screen.png"
MATCH_THRESHOLD = 0.7  # 유사도 기준

# 한글 경로 지원
def imread_unicode(path: str) -> np.ndarray:
    """
    한글 경로 지원 이미지 읽기 (RGB)
    :param path: 이미지 파일 경로
    :return: numpy 배열 (H, W, 3)
    """
    with Image.open(path) as img:
        return np.array(img.convert("RGB"))

def imwrite_unicode(path: str, img_np: np.ndarray) -> None:
    """
    한글 경로 지원 이미지 저장
    :param path: 저장할 파일 경로
    :param img_np: numpy 배열 (H, W, 3)
    :return: None
    """
    img = Image.fromarray(img_np)
    img.save(path)

# 템플릿 생성 함수
def create_button_template(
    text: str,
    button_image_dir: str,
    screen_path: str = "screen.png",
    font_path: str = "NotoSansKR-Bold.ttf",
    font_size: int = 36,
    padding: int = 10
) -> tuple[str, float]:
    """
    버튼 텍스트로 여러 스케일의 템플릿을 생성하고, 화면과 가장 유사한 템플릿을 반환
    :param text: 버튼 텍스트
    :param button_image_dir: 템플릿 저장 폴더
    :param screen_path: 유사도 비교용 스크린샷 경로
    :param font_path: 폰트 경로
    :param font_size: 폰트 크기
    :param padding: 여백
    :return: (최적 템플릿 경로, 유사도)
    """
    font = ImageFont.truetype(font_path, font_size)
    dummy_img = Image.new("RGB", (1, 1))
    dummy_draw = ImageDraw.Draw(dummy_img)
    bbox = dummy_draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    extra_right = 8
    extra_bottom = 10
    # 기존 padding을 활용하되, 위/아래 여백을 더 넉넉하게 적용
    extra_top = padding * 2
    extra_bottom = padding * 2 + extra_bottom  # 기존 추가값에 padding을 더함
    img_width = int(text_width + 2 * padding + extra_right)
    img_height = int(text_height + extra_top + extra_bottom)
    img = Image.new("RGB", (img_width, img_height), color=(0, 0, 0))
    draw = ImageDraw.Draw(img)
    pos_x = padding
    pos_y = extra_top  # 텍스트를 더 아래에 위치시키기 위해 top padding 적용
    draw.text((pos_x, pos_y), text, font=font, fill=(255, 255, 255))
    img_np = np.array(img)
    blurred = cv2.GaussianBlur(img_np, (5, 5), 0)

    name_text = text.replace(' ', '_')
    best_similarity = 0
    best_template_path = None
    scales = [i/100 for i in range(50, 151, 5)]

    for scale in scales:
        temp_path = os.path.join(button_image_dir, f"{name_text}_{scale:.2f}.png")
        new_width = int(blurred.shape[1] * scale)
        new_height = int(blurred.shape[0] * scale)
        resized = cv2.resize(blurred, (new_width, new_height), interpolation=cv2.INTER_CUBIC)
        imwrite_unicode(temp_path, resized)
        similarity = find_button_similarity(screen_path, temp_path)
        print(f"  - 스케일 {scale:.2f}: 유사도 {similarity:.4f}")
        if similarity > best_similarity:
            best_similarity = similarity
            best_scale = scale
            best_template_path = temp_path

    # 6. 기존 파일이 없었다면 best_template_path를 그대로 둠
    #    기존 파일이 있었고 유사도 MATCH_THRESHOLD 미만이면 기존 파일 삭제 후 best_template_path만 남김
    #    기존 파일이 있었고 best_similarity가 기존 파일보다 높으면 best_template_path만 남김
    pattern = os.path.join(button_image_dir, f"{name_text}_*.png")
    existing_images = glob.glob(pattern)
    for img_path in existing_images:
        if img_path != best_template_path:
            try:
                os.remove(img_path)
                print(f"🗑️ 기존 파일 삭제: {os.path.basename(img_path)}")
            except Exception as e:
                print(f"⚠️ 파일 삭제 실패: {os.path.basename(img_path)} - {e}")
    if best_template_path is not None:
        # 최종 템플릿을 버튼이름_유사도.png 형식으로 저장
        similarity_str = f"{best_similarity:.2f}"
        final_template_path = os.path.join(button_image_dir, f"{name_text}_{similarity_str}.png")
        if best_template_path != final_template_path:
            os.rename(best_template_path, final_template_path)
            print(f"💾 최적 템플릿 저장: {os.path.basename(final_template_path)} (유사도: {best_similarity:.4f})")
            return final_template_path, best_similarity
        else:
            print(f"💾 최적 템플릿 저장: {os.path.basename(best_template_path)} (유사도: {best_similarity:.4f})")
            return best_template_path, best_similarity
    else:
        raise Exception("템플릿 생성에 실패했습니다.")

# 템플릿 매칭 함수
def find_button_position(screen_path: str, template_path: str) -> Optional[Tuple[int, int]]:
    """
    화면에서 템플릿 이미지와 가장 유사한 위치의 중심 좌표 반환
    :param screen_path: 스크린샷 이미지 경로
    :param template_path: 템플릿 이미지 경로
    :param match_threshold: 유사도 기준(0~1)
    :return: (x, y) 중심 좌표 또는 None
    """
    screen = imread_unicode(screen_path)
    template = imread_unicode(template_path)
    result = cv2.matchTemplate(screen, template, cv2.TM_CCOEFF_NORMED)
    _, max_val, _, max_loc = cv2.minMaxLoc(result)
    print(f"🔍 유사도 {max_val:.4f}")
    if max_val >= MATCH_THRESHOLD:
        h, w = template.shape[:2]
        center_x = max_loc[0] + w // 2
        center_y = max_loc[1] + h // 2
        print(f"✅ 버튼 위치: ({center_x}, {center_y})")
        return center_x, center_y
    else:
        print("❌ 유사도가 기준보다 낮아 버튼 클릭 생략됨")
        return None

def find_button_similarity(screen_path, template_path):
    """템플릿과 화면의 최대 유사도 반환"""
    try:
        screen = imread_unicode(screen_path)
        template = imread_unicode(template_path)
        
        if screen is None or template is None:
            return 0
        
        result = cv2.matchTemplate(screen, template, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, _ = cv2.minMaxLoc(result)
        return max_val
    except Exception as e:
        print(f"유사도 계산 오류: {e}")
        return 0

# 매칭된 영역 추출 함수
def extract_matched_region(screen_path: str, template_path: str, save_path: str = "matched_crop.png") -> str:
    """
    화면에서 템플릿과 매칭된 영역을 잘라 저장
    :param screen_path: 스크린샷 이미지 경로
    :param template_path: 템플릿 이미지 경로
    :param save_path: 잘라 저장할 파일 경로
    :return: 저장된 파일 경로(str)
    """
    screen = imread_unicode(screen_path)
    template = imread_unicode(template_path)
    result = cv2.matchTemplate(screen, template, cv2.TM_CCOEFF_NORMED)
    _, max_val, _, max_loc = cv2.minMaxLoc(result)
    h, w = template.shape[:2]
    x, y = max_loc
    cropped = screen[y:y+h, x:x+w]
    imwrite_unicode(save_path, cropped)
    print(f"[✔] 매칭된 영역을 '{save_path}'로 저장했습니다. (유사도: {max_val:.4f})")
    return save_path 

def 버튼_찾기_클릭(text:str, 화면경로:str = "screen.png", delay:int = 1, must_exist: bool = True):
    # 1. 파일명 처리 (공백→_ 및 유니코드 경로)
    capture_screen(화면경로)
    button_image_dir = "button_image"
    os.makedirs(button_image_dir, exist_ok=True)
    name_text = text.replace(' ', '_')
    pattern = os.path.join(button_image_dir, f"{name_text}_*.png")
    existing_images = glob.glob(pattern)

    best_template_path = None
    best_similarity = 0

    # 2. 기존 이미지들로 화면 검색
    if existing_images:
        print(f"📁 기존 이미지 {len(existing_images)}개 발견")
        for img_path in existing_images:
            similarity = find_button_similarity(화면경로, img_path)
            if similarity > best_similarity:
                best_similarity = similarity
                best_template_path = img_path
            print(f"  - {os.path.basename(img_path)}: 유사도 {similarity:.4f}")

    # 3. 유사도 MATCH_THRESHOLD 이상이면 클릭
    if best_similarity >= MATCH_THRESHOLD:
        print(f"✅ 최종 유사도: {best_similarity:.4f} (기준: {MATCH_THRESHOLD})")
        if best_template_path is not None:
            coords = find_button_position(화면경로, best_template_path)
            if coords:
                tap_on_device(*coords)
                time.sleep(delay)
                return True
        else:
            print("❌ 버튼 위치를 찾을 수 없음")
            if must_exist:
                raise Exception(f"{text} 버튼을 찾지 못했습니다.")
            else:
                print("버튼을 찾지 못했지만 오류를 발생시키지 않고 진행합니다.")            
                return False

    # 4. 기존 이미지가 없거나 유사도 MATCH_THRESHOLD 미만이면 새 템플릿 생성
    print(f"⚠️ 기존 이미지가 없거나 유사도가 낮음 ({best_similarity:.4f}), 새 템플릿 생성")
    best_template_path, best_similarity = create_button_template(text, button_image_dir, 화면경로)

    # 5. 새 템플릿으로 MATCH_THRESHOLD 이상이면 클릭
    if best_similarity >= MATCH_THRESHOLD:
        print(f"✅ 새 템플릿 최종 유사도: {best_similarity:.4f} (기준: {MATCH_THRESHOLD})")
        coords = find_button_position(화면경로, best_template_path)
        if coords:
            tap_on_device(*coords)
            time.sleep(delay)
            return True
        else:
            print("❌ 버튼 위치를 찾을 수 없음")
            if must_exist:
                raise Exception(f"{text} 버튼을 찾지 못했습니다.")
            else:
                print("버튼을 찾지 못했지만 오류를 발생시키지 않고 진행합니다.")            
                return False
    else:
        print(f"❌ 새 템플릿 유사도가 너무 낮음: {best_similarity:.4f}")
        if must_exist:
            raise Exception(f"{text} 버튼을 찾지 못했습니다.")
        else:
            print("버튼을 찾지 못했지만 오류를 발생시키지 않고 진행합니다.")            
            return False
