from playwright.sync_api import Playwright, sync_playwright
import re
from test_common import *
from datetime import datetime
import os
from dotenv import load_dotenv

EMAIL = os.getenv("id")
PASSWORD = os.getenv("pw")
ENV = os.getenv("env")
BUILD = os.getenv("build")

def run_kid_login_test(playwright: Playwright) -> None:
    """KID 로그인 테스트 시나리오"""
    test_results = get_test_results()
    # 폴더 준비
    setup_directories()
    
    start_idx = len(test_results)
    context, page, video_path = setup_browser(playwright)
    
    try:
        # 1. KID QA 로그인 체크리스트
        checklist_login = "KID QA 로그인"
        try:
            log("로그인 페이지 접속 시도")
            page.goto("https://gamma.accounts.krafton.dev/v2/ko/web/login-main?type=last-login")
            log("이메일 입력 시도")
            page.get_by_placeholder("이메일").fill(EMAIL)
            log("비밀번호 입력 시도")
            page.get_by_placeholder("비밀번호").fill(PASSWORD)
            log("로그인 버튼 클릭 시도")
            page.get_by_role("button", name="로그인").click()
            page.wait_for_timeout(3000)
            log(f"로그인 후 URL 확인: {page.url}")
            if page.url.startswith("https://gamma.accounts.krafton.dev/"):
                screenshot_path = take_screenshot(page, checklist_login)
                result(checklist_login, "Pass", "로그인 페이지에서 정상적으로 로그인 시도함.", screenshot=screenshot_path, video=None)
            else:
                screenshot_path = take_screenshot(page, checklist_login)
                result(checklist_login, "Fail", f"로그인 후 예상 URL이 아님: {page.url}", screenshot=screenshot_path, video=None)
        except Exception as e:
            screenshot_path = take_screenshot(page, checklist_login)
            result(checklist_login, "N/A", f"로그인 테스트 중 예외 발생: {e}", screenshot=screenshot_path, video=None)

        # 2. KID 로그인 마스킹 이메일 검증
        checklist_mask = "KID 로그인 마스킹 이메일 검증"
        try:
            log("마스킹 이메일 검증 대기 및 HTML 파싱")
            page.wait_for_timeout(2000)
            content = page.content()
            masked_email = None
            match = re.search(r'[a-zA-Z0-9]\*+\d?@[a-zA-Z0-9.-]+', content)
            if match:
                masked_email = match.group(0)
                log(f"마스킹 이메일 추출: {masked_email}")
                if is_masked_email_valid(EMAIL, masked_email):
                    screenshot_path = take_screenshot(page, checklist_mask)
                    result(checklist_mask, "Pass", f"마스킹 이메일이 올바름: {masked_email}", screenshot=screenshot_path, video=None)
                else:
                    screenshot_path = take_screenshot(page, checklist_mask)
                    result(checklist_mask, "Fail", f"마스킹 이메일이 잘못됨: {masked_email}", screenshot=screenshot_path, video=None)
            else:
                log("마스킹 이메일을 찾지 못함")
                screenshot_path = take_screenshot(page, checklist_mask)
                result(checklist_mask, "N/A", "마스킹 이메일을 찾지 못함", screenshot=screenshot_path, video=None)
        except Exception as e:
            screenshot_path = take_screenshot(page, checklist_mask)
            result(checklist_mask, "N/A", f"마스킹 이메일 테스트 중 예외 발생: {e}", screenshot=screenshot_path, video=None)
    
    finally:
        test_results = get_test_results()

        video_path = cleanup_browser(context, video_path)
        if video_path and os.path.exists(video_path) and test_results:
            now_str = datetime.now().strftime('%Y%m%d_%H%M%S')
            new_video_name = f"video/KID_login_{now_str}.webm"
            try:
                os.rename(video_path, new_video_name)
                video_path = new_video_name
                log(f"비디오 파일명 변경: {video_path}")
            except Exception as e:
                log(f"비디오 파일명 변경 실패: {e}")
            # KID 로그인 시나리오의 결과들에만 비디오 경로 할당
            kid_results = [r for r in test_results if 'KID' in r['checklist']]
            for r in kid_results:
                r['video'] = video_path
            log(f"KID 로그인 시나리오 결과 {len(kid_results)}개에 비디오 경로 할당: {video_path}")
        else:
            log("비디오 파일이 없습니다. 또는 결과가 없습니다.")

if __name__ == "__main__":
    with sync_playwright() as playwright:
        run_kid_login_test(playwright)