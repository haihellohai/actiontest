from playwright.sync_api import Playwright
import re
from datetime import datetime
import json
from generate_report import save_report_html
import webbrowser
import os
import glob

# 전역 변수 (모든 테스트에서 공유)
_test_results = []
_logs = []

def get_test_results():
    """test_results를 안전하게 반환합니다."""
    global _test_results
    return _test_results

def get_logs():
    """logs를 안전하게 반환합니다."""
    global _logs
    return _logs

def set_test_results(results):
    """test_results를 안전하게 설정합니다."""
    global _test_results
    _test_results = results

def set_logs(logs):
    """logs를 안전하게 설정합니다."""
    global _logs
    _logs = logs

# 폴더 준비
def setup_directories():
    """테스트에 필요한 폴더들을 생성합니다."""
    os.makedirs('screenshots', exist_ok=True)
    os.makedirs('video', exist_ok=True)
    os.makedirs('reports', exist_ok=True)

def log(message):
    """로그 메시지를 기록합니다."""
    global _logs
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] {message}"
    _logs.append(log_entry)
    print(log_entry)

def result(checklist: str, value: str, message: str, screenshot=None, video=None):
    """테스트 결과를 기록합니다."""
    global _test_results
    _test_results.append({
        "checklist": checklist,
        "value": value,
        "message": message,
        "screenshot": screenshot,
        "video": video
    })
    log(f"[체크리스트] {checklist}")
    log(f"[결과] {checklist} - {value}")
    log(f"[메시지] {message}")
    log("-" * 60)

def take_screenshot(page, checklist_name):
    """스크린샷을 찍고 경로를 반환합니다."""
    screenshot_path = f"screenshots/{checklist_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
    page.screenshot(path=screenshot_path)
    return screenshot_path

def setup_browser(playwright: Playwright):
    """지정된 크롬 프로필을 사용해 브라우저를 설정하고 비디오 녹화를 시작합니다."""
    log("테스트 시작 (지정된 크롬 프로필 사용)")
    user_data_dir = r"C:\Users\newhite\AppData\Local\Google\Chrome\User Data\Profile 2"
    context = playwright.chromium.launch_persistent_context(
        user_data_dir,
        headless=False,
        # 필요시 viewport, args 등 추가 옵션
    )
    log("Persistent Chrome 컨텍스트 생성 (기존 프로필 사용)")
    page = context.pages[0] if context.pages else context.new_page()
    log("새 페이지 오픈")
    video_path = None  # launch_persistent_context는 기본적으로 비디오 녹화 미지원
    return context, page, video_path

def cleanup_browser(browser, context, video_path):
    """브라우저를 정리하고 비디오 파일을 찾습니다."""
    log("테스트 종료, 브라우저 세션 종료")
    
    # 비디오 파일 찾기 및 저장
    try:
        # 컨텍스트를 닫으면 비디오 파일이 생성됩니다
        context.close()
        browser.close()
        
        # 비디오 파일 찾기 (Playwright가 자동으로 생성한 파일명)
        video_files = glob.glob("video/*.webm")
        if video_files:
            # 가장 최근 파일을 사용
            latest_video = max(video_files, key=os.path.getctime)
            video_path = latest_video
            # 가장 최근 체크리스트 이름 가져오기
            from test_common import get_test_results
            test_results = get_test_results()
            checklist_name = test_results[-1]['checklist'] if test_results else 'Unknown'
            log(f"비디오 파일 저장됨: {checklist_name} ({video_path})")
        else:
            video_path = None
            log("비디오 파일을 찾을 수 없습니다.")
    except Exception as e:
        log(f"비디오 파일 처리 중 오류: {e}")
        video_path = None
        context.close()
        browser.close()
    
    return video_path

def save_test_results():
    """테스트 결과와 로그만 저장합니다."""
    global _test_results, _logs
    # 로그에 이전 결과 출력하지 않음
    with open("test_results.json", "w", encoding="utf-8") as f:
        json.dump(_test_results, f, ensure_ascii=False, indent=2)
    with open("logs.json", "w", encoding="utf-8") as f:
        json.dump(_logs, f, ensure_ascii=False, indent=2)

def generate_report_and_open(build_url, test_env, video_path):
    """리포트 생성 및 브라우저 열기"""
    global _test_results, _logs
    try:
        os.makedirs('reports', exist_ok=True)  # reports 폴더 보장
        report_file = save_report_html(_test_results, _logs, build_number=build_url, test_env=test_env, video_path=video_path)
        log(f"HTML 리포트가 {report_file}로 저장되었습니다.")
        abs_report_path = os.path.abspath(report_file)
        webbrowser.open(f"file:///{abs_report_path}")
        return report_file
    except Exception as e:
        log(f"[에러] 리포트 생성 중 예외 발생: {e}")
        # 예외 발생 시 최소한의 리포트라도 생성
        try:
            with open("reports/failed_report.html", "w", encoding="utf-8") as f:
                f.write(f"<html><body><h1>리포트 생성 실패</h1><p>예외: {e}</p></body></html>")
            log("임시 리포트(리포트 생성 실패) 저장됨: reports/failed_report.html")
        except Exception as e2:
            log(f"[치명적 에러] 임시 리포트 생성도 실패: {e2}")
        return None

def reset_test_data():
    """테스트 데이터를 완전히 초기화합니다."""
    global _test_results, _logs
    _test_results = []
    _logs = []
    # 기존 파일들도 삭제하여 완전 초기화
    with open("test_results.json", "w", encoding="utf-8") as f:
        json.dump([], f)
    with open("logs.json", "w", encoding="utf-8") as f:
        json.dump([], f)

def is_masked_email_valid(original, masked):
    """마스킹된 이메일이 올바른지 검증합니다."""
    match = re.match(r"(.)(\*+)(.)@(.+)", masked)
    if not match:
        return False
    first, stars, last, domain = match.groups()
    if not (original.startswith(first) and original.split('@')[1] == domain):
        return False
    original_local = original.split('@')[0]
    
    if not (original_local[0] == first and original_local[-1] == last):
        return False
    if len(stars) == len(original_local) - 2:
        return True
    return False

def save_test_results_and_report(build_url, test_env, video_path):
    """테스트 결과 저장 + 리포트 자동 생성 (이전 결과 보존용)"""
    save_test_results()
    from generate_report import save_report_html
    save_report_html(get_test_results(), get_logs(), build_number=build_url, test_env=test_env, video_path=video_path)

# ... existing code ...
# (184줄 이후 for r in parsed_reports: ~ report_rows += ... 블록 전체 삭제)
# ... existing code ... 