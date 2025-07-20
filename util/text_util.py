import pytesseract
import cv2
import numpy
import time
from PIL import Image
import os
from . import button_util
from . import common_util
from util.dynamic_data import save_data, load_data
from util.adb_util import tap_on_device, ensure_adb_connection, capture_screen

import re

# 2. 이미지에서 OCR 수행 + 'qa' 텍스트 탐색 + 위치 추출
def find_text_coordinates(
    image_path: str,
    target_text: str,
    y_offset_ratio: float = 0.6,
    similarity_threshold: float = 0.8,
    preprocess_steps=None
):
    import re

    def normalize(text):
        return re.sub(r"[^a-zA-Z0-9가-힣]+", "", text).lower()

    def is_pattern(text):
        return "*" in text or "." in text

    def get_box(i, j, d):
        x1 = min(d['left'][i+k] for k in range(j+1))
        y1 = min(d['top'][i+k] for k in range(j+1))
        x2 = max(d['left'][i+k] + d['width'][i+k] for k in range(j+1))
        y2 = max(d['top'][i+k] + d['height'][i+k] for k in range(j+1))
        return (x1, y1, x2, y2)

    def levenshtein_distance(str1, str2):
        if len(str1) < len(str2):
            return levenshtein_distance(str2, str1)
        if len(str2) == 0:
            return len(str1)
        previous_row = list(range(len(str2) + 1))
        for i, c1 in enumerate(str1):
            current_row = [i + 1]
            for j, c2 in enumerate(str2):
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row
        return previous_row[-1]

    def similarity_ratio(str1, str2):
        if not str1 and not str2:
            return 1.0
        distance = levenshtein_distance(str1, str2)
        max_len = max(len(str1), len(str2))
        return 1 - (distance / max_len) if max_len > 0 else 1.0

    # y_offset_ratio 범위 체크
    if not (0.0 <= y_offset_ratio <= 1.0):
        print(f"[WARN] y_offset_ratio {y_offset_ratio}는 0~1 범위를 벗어났습니다. 기본값 0.6으로 대체합니다.")
        y_offset_ratio = 0.6

    if preprocess_steps is None:
        preprocess_steps = [
            {'invert': False, 'threshold': False, 'resize': 1.0},
            {'invert': True,  'threshold': False, 'resize': 2.0},
            {'invert': True,  'threshold': True,  'resize': 2.0}
        ]

    for idx, step in enumerate(preprocess_steps):
        temp_path = f"screen_pre_{idx}.png"
        preprocess_for_ocr(
            input_path=image_path,
            output_path=temp_path,
            apply_threshold=step.get('threshold', False),
            invert=step.get('invert', True),
            resize_factor=step.get('resize', 1.0)
        )
        img = cv2.imread(temp_path)
        if img is None:
            if os.path.exists(temp_path):
                os.remove(temp_path)
            continue
        h, w = img.shape[:2]
        print(f"[DEBUG] (step {idx}) OCR 입력 이미지 해상도: {w}x{h} (가로x세로)")
        real_w = load_data('real_screen_width')
        real_h = load_data('real_screen_height')
        print(f"[DEBUG] (step {idx}) 실제 화면 해상도: {real_w}x{real_h} (가로x세로)")

        # --- 회전 보정 조건 개선 ---
        need_rotation = False
        if real_w is not None and real_h is not None:
            # 더 정밀한 회전 판단
            if abs(w - real_h) < 50 and abs(h - real_w) < 50:
                print("[INFO] 이미지와 디바이스 해상도가 90도 회전된 상태로 판단 (정밀 조건)")
                need_rotation = True
            scale_x = real_w / float(w)
            scale_y = real_h / float(h)
            print(f"[DEBUG] 스케일 팩터: scale_x={scale_x:.3f}, scale_y={scale_y:.3f}")
            if scale_x > 4.0 or scale_y > 4.0:
                print(f"[WARN] OCR 입력 이미지와 실제 해상도 차이가 너무 큽니다. (scale_x={scale_x:.2f}, scale_y={scale_y:.2f}) 리사이즈 배율을 확인하세요.")
        else:
            print("[WARN] 실제 해상도 정보 없음. resize_factor만 사용")
            scale_x = scale_y = load_data('resize_factor') or 1.0

        d = pytesseract.image_to_data(img, lang="kor+eng", output_type=pytesseract.Output.DICT)
        n = len(d['text'])
        matched_candidates = []
        for i in range(n):
            if not d['text'][i].strip():
                continue
            for j in range(0, 6):
                if i + j >= n:
                    break
                segment = d['text'][i:i+j+1]
                if all(not word.strip() for word in segment):
                    continue
                joined = ''.join(segment)
                cleaned = normalize(joined)
                norm_target = normalize(target_text)
                if is_pattern(target_text):
                    pattern = re.escape(norm_target).replace(r"\*", ".*")
                    if re.search(pattern, cleaned, re.IGNORECASE):
                        matched_candidates.append((get_box(i, j, d), 1.0, "pattern"))
                else:
                    if cleaned == norm_target:
                        matched_candidates.append((get_box(i, j, d), 1.0, "exact"))
                    else:
                        similarity = similarity_ratio(cleaned, norm_target)
                        print(f"[DEBUG] 유사도 비교: '{cleaned}' vs '{norm_target}' → 유사도: {similarity:.3f}")
                        if similarity >= similarity_threshold:
                            print(f"[INFO] 유사도 매칭: '{cleaned}' ≈ '{norm_target}' (유사도: {similarity:.3f})")
                            matched_candidates.append((get_box(i, j, d), similarity, "similarity"))
        if matched_candidates:
            best_candidate = max(matched_candidates, key=lambda x: x[1])
            matched_boxes = [best_candidate[0]]
            print(f"[INFO] (step {idx}) 최고 매칭 선택: 유사도 {best_candidate[1]:.3f} ({best_candidate[2]} 매칭)")
            min_x = min(box[0] for box in matched_boxes)
            min_y = min(box[1] for box in matched_boxes)
            max_x = max(box[2] for box in matched_boxes)
            max_y = max(box[3] for box in matched_boxes)
            image_center_x = (min_x + max_x) / 2
            bbox_height = max(max_y - min_y, 1)
            image_center_y = (min_y + max_y) / 2

            # --- 회전 보정 적용 ---
            if need_rotation:
                image_center_x, image_center_y = image_center_y, w - image_center_x

            center_x = int(image_center_x * scale_x)
            center_y = int(image_center_y * scale_y)

            # --- 좌표가 해상도 초과 시 강제 회전 보정 ---
            if real_w is not None and real_h is not None and (center_x > real_w or center_y > real_h):
                print("[WARN] 좌표가 화면 해상도를 벗어납니다. 회전 보정 강제 적용합니다.")
                image_center_x, image_center_y = image_center_y, w - image_center_x
                center_x = int(image_center_x * scale_x)
                center_y = int(image_center_y * scale_y)

            # --- ADB 좌표 클램핑 ---
            if real_w is not None and real_h is not None:
                center_x = min(max(center_x, 0), real_w - 1)
                center_y = min(max(center_y, 0), real_h - 1)

            print(f"[DEBUG] (step {idx}) 이미지 좌표: ({image_center_x:.1f}, {image_center_y:.1f})")
            print(f"[DEBUG] (step {idx}) 변환된 디바이스 좌표: ({center_x}, {center_y}) (y_offset_ratio={y_offset_ratio})")
            print(f"[✔] (step {idx}) Found '{target_text}' at merged center ({center_x}, {center_y}) [scale_x={scale_x:.3f}, scale_y={scale_y:.3f} 적용]")
            if os.path.exists(temp_path):
                os.remove(temp_path)
            return (center_x, center_y, target_text)
        else:
            print(f"[INFO] (step {idx}) '{target_text}'를 찾지 못함.")
        if os.path.exists(temp_path):
            os.remove(temp_path)
    print(f"[✖] 모든 전처리 단계에서 '{target_text}'를 찾지 못했습니다.")
    return None

# def print_all_ocr_text(image_path:str = "screen.png") -> str:
#     img = cv2.imread(image_path)
#     # text = pytesseract.image_to_string(img, "Kor+Eng")
#     text = pytesseract.image_to_data(img, "Kor+Eng", output_type=pytesseract.Output.DICT)
#     print("OCR로 인식된 전체 텍스트:\n")
#     return text

def print_all_ocr_text(image_path: str = "screen.png") -> str:
    img = cv2.imread(image_path)
    if img is None:
        raise FileNotFoundError(f"이미지 파일을 찾을 수 없습니다: {image_path}")
    
    d = pytesseract.image_to_data(img, lang="kor+eng", output_type=pytesseract.Output.DICT)
    words = [t for t in d['text'] if t.strip()]
    print("OCR로 인식된 전체 텍스트:\n")
    result = " ".join(words)
    print(result)
    return result

def preprocess_for_ocr(
    input_path: str = "screen.png",
    output_path: str = "screen.png",
    apply_threshold: bool = False,
    invert: bool = True,
    resize_factor: float = 2.0
) -> numpy.ndarray:
    """
    OCR용으로 이미지 전처리 (Grayscale + Invert + Optional Thresholding)
    
    :param input_path: 원본 이미지 경로
    :param output_path: 저장할 전처리 이미지 경로
    :param apply_threshold: adaptive threshold 적용 여부
    :param invert: 색 반전 여부 (흰글씨+검정배경 → 검정글씨+흰배경)
    :param resize_factor: 이미지 확대 배율 (OCR 정확도 향상)
    :return: 전처리된 이미지 객체 (cv2.Mat)
    """
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"파일이 존재하지 않습니다: {input_path}")
    
    # 이미지 로드 및 Grayscale
    img = cv2.imread(input_path)
    if img is None:
        raise FileNotFoundError(f"이미지 파일을 열 수 없습니다: {input_path}")
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # 색 반전
    if invert:
        gray = cv2.bitwise_not(gray)

    # Adaptive Thresholding (선택)
    if apply_threshold:
        gray = cv2.adaptiveThreshold(
            gray, 255,
            cv2.ADAPTIVE_THRESH_MEAN_C,
            cv2.THRESH_BINARY,
            15, 10
        )

    # Resize 확대 (옵션)
    if resize_factor > 4.0:
        print(f"[WARN] resize_factor가 너무 큽니다({resize_factor}). 3.0으로 자동 조정합니다.")
        resize_factor = 3.0
    if resize_factor != 1.0:
        gray = cv2.resize(
            gray, None,
            fx=resize_factor, fy=resize_factor,
            interpolation=cv2.INTER_CUBIC
        )

    # 파일 저장
    cv2.imwrite(output_path, gray)
    print(f"[✔] 전처리 이미지 저장 완료: {output_path}")
    save_data('resize_factor', resize_factor)
    return gray

def 텍스트_찾기(text:str, must_exist: bool = True, 화면경로="screen.png") -> bool:
    """
    OCR로 텍스트 찾기
    :text: 찾는 텍스트 정보 (와일드카드*처리 가능, 포함된 텍스트 찾기 가능)
    :must_exist: 해당 텍스트가 없을 때 Exception 발생 여부
    :화면 경로: 캡쳐를 진행하고 찾을 이미지 파일 이름
    :return: 텍스트 찾기 결과(bool)
    """
    print("함수 이름: 텍스트_찾기")
    common_util.capture_screen(화면경로)
    result = find_text_coordinates(화면경로, text)
    if result:
        x, y, _ = result
        print(f"[INFO] 찾은은 OCR 단어: '{_}'")
        return True
    else:
        print(f"❌ {text} 텍스트를 찾지 못했습니다.")
        if must_exist:
            print(print_all_ocr_text)
            raise Exception(f"{text} 텍스트를 찾지 못했습니다.")

        else:
            return False

def 텍스트_찾기_클릭(text:str, delay:int = 1,  must_exist: bool = True, 화면경로="screen.png") -> bool:
    """
    OCR로 텍스트 찾고 클릭하기기
    :text: 찾는 텍스트 정보 (와일드카드*처리 가능, 포함된 텍스트 찾기 가능)
    :delay: 텍스트 클릭 후 대기(초)
    :must_exist: 해당 텍스트가 없을 때 Exception 발생 여부
    :화면 경로: 캡쳐를 진행하고 찾을 이미지 파일 이름
    :return: 텍스트 찾기 결과(bool)
    """
    print("함수 이름: 텍스트_찾기_클릭")
    common_util.capture_screen(화면경로)
    result = find_text_coordinates(화면경로, text)
    if result:
        x, y, _ = result
        print(f"[INFO] 클릭한 OCR 단어: '{_}'")
        common_util.tap_on_device(x, y)
        time.sleep(delay)
        return True
    else:
        print("❌ {text} 텍스트를 찾지 못했습니다.")
        if must_exist:
            raise Exception(f"{text} 텍스트를 찾지 못했습니다.")
        else:
            return False
