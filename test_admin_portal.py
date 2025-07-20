from playwright.sync_api import Playwright, sync_playwright
from test_common import *
from datetime import datetime
import os
import json

# 테스트 환경/계정/빌드 정보 상수
TEST_ENV = "QA"
LOGIN_URL = "https://qa.gpp.krafton.dev/admin/namespace"
BUILD_INFO = "SDKTest"

def run_admin_portal_test(playwright: Playwright) -> None:
    """GPP QA 네임스페이스 페이지 테스트 시나리오"""
    # 폴더 준비
    setup_directories()
    
    # 브라우저 설정
    context, page, video_path = setup_browser(playwright)
    
    try:
        # 1. GPP QA 네임스페이스 페이지 접속 테스트
        checklist_access = "GPP QA 네임스페이스 페이지 접속"
        try:
            log("GPP QA 네임스페이스 페이지 접속 시도")
            page.goto(LOGIN_URL)
            page.wait_for_timeout(3000)  # 페이지 로딩 대기
            log(f"접속 후 URL 확인: {page.url}")
            
            if page.url.startswith(LOGIN_URL):
                screenshot_path = take_screenshot(page, checklist_access)
                result(checklist_access, "Pass", "GPP QA 네임스페이스 페이지에 정상적으로 접속함.", screenshot=screenshot_path, video=None)
            else:
                screenshot_path = take_screenshot(page, checklist_access)
                result(checklist_access, "Fail", f"예상 URL이 아님: {page.url}", screenshot=screenshot_path, video=None)
        except Exception as e:
            screenshot_path = take_screenshot(page, checklist_access)
            result(checklist_access, "N/A", f"페이지 접속 중 예외 발생: {e}", screenshot=screenshot_path, video=None)

        # 2. "내 네임스페이스" 텍스트 확인 테스트
        checklist_text = "내 네임스페이스 텍스트 확인"
        try:
            log("내 네임스페이스 텍스트 확인")
            page.wait_for_timeout(2000)  # 추가 대기
            
            # 페이지에서 "내 네임스페이스" 텍스트 찾기
            text_found = page.locator("text=내 네임스페이스").count() > 0
            
            if text_found:
                screenshot_path = take_screenshot(page, checklist_text)
                result(checklist_text, "Pass", "페이지에서 '내 네임스페이스' 텍스트를 정상적으로 확인함.", screenshot=screenshot_path, video=None)
            else:
                log("페이지에서 '내 네임스페이스' 텍스트를 찾을 수 없음")
                screenshot_path = take_screenshot(page, checklist_text)
                result(checklist_text, "Fail", "페이지에서 '내 네임스페이스' 텍스트를 찾을 수 없음", screenshot=screenshot_path, video=None)
        except Exception as e:
            screenshot_path = take_screenshot(page, checklist_text)
            result(checklist_text, "N/A", f"텍스트 확인 중 예외 발생: {e}", screenshot=screenshot_path, video=None)

        # 3. 페이지 제목 확인 테스트
        checklist_title = "페이지 제목 확인"
        try:
            log("페이지 제목 확인")
            title = page.title()
            log(f"페이지 제목: {title}")
            
            if title and len(title.strip()) > 0:
                screenshot_path = take_screenshot(page, checklist_title)
                result(checklist_title, "Pass", f"페이지 제목이 정상적으로 표시됨: {title}", screenshot=screenshot_path, video=None)
            else:
                screenshot_path = take_screenshot(page, checklist_title)
                result(checklist_title, "Fail", "페이지 제목이 비어있거나 표시되지 않음", screenshot=screenshot_path, video=None)
        except Exception as e:
            screenshot_path = take_screenshot(page, checklist_title)
            result(checklist_title, "N/A", f"페이지 제목 확인 중 예외 발생: {e}", screenshot=screenshot_path, video=None)
    
    finally:
        test_results = get_test_results()
        # 브라우저 정리 및 비디오 저장
        video_path = cleanup_browser(context, video_path)
        if video_path and os.path.exists(video_path) and test_results:
            now_str = datetime.now().strftime('%Y%m%d_%H%M%S')
            new_video_name = f"video/Admin_portal_{now_str}.webm"
            try:
                os.rename(video_path, new_video_name)
                video_path = new_video_name
                log(f"비디오 파일명 변경: {video_path}")
            except Exception as e:
                log(f"비디오 파일명 변경 실패: {e}")
            # Admin Portal 시나리오의 결과들에만 비디오 경로 할당
            admin_results = []
            for r in test_results:
                if ('GPP QA 네임스페이스' in r['checklist'] or 
                    'Login with Microsoft' in r['checklist'] or 
                    '내 네임스페이스' in r['checklist']):
                    admin_results.append(r)
            for r in admin_results:
                r['video'] = video_path
            log(f"Admin Portal 시나리오 결과 {len(admin_results)}개에 비디오 경로 할당: {video_path}")
        else:
            log("비디오 파일이 없습니다. 또는 결과가 없습니다.")

def run_example_scenario_test(playwright: Playwright) -> None:
    """Admin Portal 네임스페이스 테스트 시나리오"""
    test_results = get_test_results()
    # 폴더 준비
    setup_directories()
    
    start_idx = len(test_results)
    context, page, video_path = setup_browser(playwright)
    
    try:
        # 1. GPP QA 네임스페이스 페이지 접속
        checklist_access = "GPP QA 네임스페이스 페이지 접속"
        try:
            log("GPP QA 네임스페이스 페이지 접속 시도")
            page.goto(LOGIN_URL)
            page.wait_for_timeout(2000)
            log(f"접속 후 URL 확인: {page.url}")
            screenshot_path = take_screenshot(page, checklist_access)
            if page.url.startswith(LOGIN_URL):
                result(checklist_access, "Pass", "GPP QA 네임스페이스 페이지에 정상적으로 접속함.", screenshot=screenshot_path, video=None)
            else:
                result(checklist_access, "Fail", f"예상 URL이 아님: {page.url}", screenshot=screenshot_path, video=None)
        except Exception as e:
            screenshot_path = take_screenshot(page, checklist_access)
            result(checklist_access, "N/A", f"페이지 접속 중 예외 발생: {e}", screenshot=screenshot_path, video=None)

        # 2. Login with Microsoft 버튼 클릭 (예외 상황은 체크포인트로 남기지 않음)
        try:
            log("Login with Microsoft 버튼 탐색 시도")
            # 버튼이 있으면 클릭, 없으면 예외처리
            if page.locator('button:has-text("Login with Microsoft")').count() > 0:
                log("Login with Microsoft 버튼 발견, 클릭 시도")
                page.get_by_role("button", name="Login with Microsoft").click()
                page.wait_for_timeout(2000)
                screenshot_path = take_screenshot(page, "Login with Microsoft 버튼 클릭")
                result("Login with Microsoft 버튼 클릭", "Pass", "Login with Microsoft 버튼을 클릭함.", screenshot=screenshot_path, video=None)
                
                # 사용자 ID 입력 및 인증 대기
                try:
                    log("사용자 ID 입력 시도")
                    # 이메일 입력 필드 찾기 및 입력
                    email_input = page.locator('input[type="email"], input[name="loginfmt"], input[placeholder*="email"], input[placeholder*="이메일"]').first
                    if email_input.count() > 0:
                        email_input.fill(USER_EMAIL)
                        log(f"사용자 ID 입력 완료: {USER_EMAIL}")
                        
                        # Enter 키 입력
                        email_input.press("Enter")
                        log("Enter 키 입력 완료")
                        
                        # '조직 계정으로 로그인' 텍스트가 나타날 때까지 대기 후 비밀번호 입력
                        try:
                            log("'조직 계정으로 로그인' 텍스트 대기 중...")
                            page.wait_for_selector('text=조직 계정으로 로그인', timeout=15000)
                            log("'조직 계정으로 로그인' 텍스트 감지됨, 비밀번호 입력 시도")
                            password_input = page.locator('input[type="password"]').first
                            if password_input.count() > 0:
                                pw = USER_PASSWORD
                                if len(pw) > 2:
                                    masked_pw = pw[0] + '*' * (len(pw)-2) + pw[-1]
                                elif len(pw) == 2:
                                    masked_pw = pw[0] + '*'
                                else:
                                    masked_pw = '*' * len(pw)
                                log(f"비밀번호 입력 완료: {masked_pw} (마스킹)")
                                password_input.fill(USER_PASSWORD)
                                password_input.press("Enter")
                                log("비밀번호 Enter 키 입력 완료")
                            else:
                                log("비밀번호 입력 필드를 찾을 수 없음")
                        except Exception as e:
                            log(f"비밀번호 입력 단계에서 예외 발생: {e}")

                        # '로그인 요청 승인' 창에서 최대 1분 대기, 사라지면 바로 진행
                        try:
                            log("'로그인 요청 승인' 텍스트 대기 중...")
                            page.wait_for_selector('text=로그인 요청 승인', timeout=20000)
                            log("'로그인 요청 승인' 창 감지됨, 최대 1분 대기(사라질 때까지)")
                            try:
                                page.wait_for_selector('text=로그인 요청 승인', state='detached', timeout=60000)
                                log("'로그인 요청 승인' 창이 사라짐, 다음 단계로 진행")
                            except Exception:
                                log("'로그인 요청 승인' 창이 1분 내에 사라지지 않음, 모든 체크포인트를 N/A 처리")
                                # 모든 체크포인트를 N/A 처리
                                test_results = get_test_results()
                                for r in test_results:
                                    r['value'] = 'N/A'
                                    r['message'] = '로그인 요청 승인 창이 1분 내에 사라지지 않음'
                        except Exception as e:
                            log(f"'로그인 요청 승인' 단계에서 예외 발생: {e}")

                        # '로그인 상태를 유지하시겠습니까?' 텍스트가 보이면 '예' 버튼 클릭
                        try:
                            log("'로그인 상태를 유지하시겠습니까?' 텍스트 대기 중...")
                            page.wait_for_selector('text=로그인 상태를 유지하시겠습니까?', timeout=15000)
                            log("'로그인 상태를 유지하시겠습니까?' 창 감지됨, '예' 버튼 클릭 시도")
                            yes_button = page.get_by_role("button", name="예")
                            if yes_button.count() > 0:
                                yes_button.click()
                                log("'예' 버튼 클릭 완료")
                                # '내 네임스페이스' 텍스트가 나타나는지 검증
                                try:
                                    log("'내 네임스페이스' 텍스트 대기 중...")
                                    page.wait_for_selector('text=내 네임스페이스', timeout=10000)
                                    log("'내 네임스페이스' 텍스트 감지됨, 네임스페이스 검색 및 선택 진행")
                                    # 네임스페이스 하단 검색창에 BUILD_INFO 입력 및 일치 항목 클릭
                                    try:
                                        log("네임스페이스 하단 검색창에 BUILD_INFO 입력 시도")
                                        search_input = page.locator("input[placeholder*='검색'], input[type='search']").first
                                        if search_input.count() > 0:
                                            search_input.fill(BUILD_INFO)
                                            log(f"검색창에 BUILD_INFO 입력 완료: {BUILD_INFO}")
                                            page.wait_for_timeout(1000)
                                            ns_item = page.locator(f"text={BUILD_INFO}").first
                                            if ns_item.count() > 0:
                                                ns_item.click()
                                                log(f"목록에서 일치하는 항목 클릭 완료: {BUILD_INFO}")
                                                screenshot_path = take_screenshot(page, "네임스페이스 준비 완료")
                                                result("네임스페이스 준비 완료", "Pass", f"'{BUILD_INFO}' 네임스페이스 준비 완료", screenshot=screenshot_path, video=None)
                                            else:
                                                screenshot_path = take_screenshot(page, "네임스페이스 준비 실패")
                                                result("네임스페이스 준비 완료", "Fail", f"'{BUILD_INFO}' 네임스페이스 항목을 찾을 수 없음", screenshot=screenshot_path, video=None)
                                                log(f"목록에서 일치하는 항목을 찾을 수 없음: {BUILD_INFO}")
                                                return
                                        else:
                                            screenshot_path = take_screenshot(page, "네임스페이스 준비 실패")
                                            result("네임스페이스 준비 완료", "Fail", "네임스페이스 검색창을 찾을 수 없음", screenshot=screenshot_path, video=None)
                                            log("네임스페이스 검색창을 찾을 수 없음")
                                            return
                                    except Exception as e:
                                        log(f"네임스페이스 검색 및 선택 중 예외 발생: {e}")
                                        screenshot_path = take_screenshot(page, "네임스페이스 준비 실패")
                                        result("네임스페이스 준비 완료", "Fail", f"네임스페이스 검색 및 선택 중 예외 발생: {e}", screenshot=screenshot_path, video=None)
                                        return
                                except Exception:
                                    log("'내 네임스페이스' 텍스트를 찾을 수 없음. 시나리오 중단 및 Fail 처리")
                                    screenshot_path = take_screenshot(page, "내 네임스페이스 텍스트 확인")
                                    result("네임스페이스 준비 완료", "Fail", "'내 네임스페이스' 텍스트를 찾을 수 없음", screenshot=screenshot_path, video=None)
                                    return
                            else:
                                log("'예' 버튼을 찾을 수 없음")
                        except Exception as e:
                            log(f"'로그인 상태를 유지하시겠습니까?' 단계에서 예외 발생: {e}")
                    else:
                        log("이메일 입력 필드를 찾을 수 없음")
                except Exception as e:
                    log(f"사용자 ID/비밀번호 입력 중 예외 발생: {e}")
                
            else:
                log("Login with Microsoft 버튼이 없음. 이미 로그인된 상태일 수 있음. 체크포인트로 남기지 않음.")
        except Exception as e:
            log(f"Login with Microsoft 버튼 클릭 중 예외 발생: {e}")
            # 예외 상황도 체크포인트로 남기지 않고 로그만 남김

        # 바로 내 네임스페이스 확인 단계로 진행

        # 3. 내 네임스페이스 텍스트 확인
        checklist_text = f"{BUILD_INFO} 네임스페이스스 확인"
        try:
            log("내 네임스페이스 텍스트 확인")
            page.wait_for_timeout(3000)
            text_found = page.locator(f"text={BUILD_INFO}").count() > 0
            screenshot_path = take_screenshot(page, checklist_text)
            if text_found:
                result(checklist_text, "Pass", f"페이지에서 '{BUILD_INFO}' 네임스페이스 진입을 확인함.", screenshot=screenshot_path, video=None)
            else:
                log("페이지에서 '내 네임스페이스' 텍스트를 찾을 수 없음")
                result(checklist_text, "Fail", f"페이지에서 '{BUILD_INFO}' 네임스페이스를 확인할 수 없음", screenshot=screenshot_path, video=None)
        except Exception as e:
            screenshot_path = take_screenshot(page, checklist_text)
            result(checklist_text, "N/A", f"텍스트 확인 중 예외 발생: {e}", screenshot=screenshot_path, video=None)
    finally:
        test_results = get_test_results()
        video_path = cleanup_browser(context, video_path)
        if video_path and os.path.exists(video_path) and test_results:
            now_str = datetime.now().strftime('%Y%m%d_%H%M%S')
            new_video_name = f"video/GPP_QA_{now_str}.webm"
            try:
                os.rename(video_path, new_video_name)
                video_path = new_video_name
                log(f"비디오 파일명 변경: {video_path}")
            except Exception as e:
                log(f"비디오 파일명 변경 실패: {e}")
            # GPP QA 시나리오의 결과들에만 비디오 경로 할당
            gpp_results = [r for r in test_results if 'GPP' in r['checklist']]
            for r in gpp_results:
                r['video'] = video_path
            log(f"GPP QA 시나리오 결과 {len(gpp_results)}개에 비디오 경로 할당: {video_path}")
        else:
            log("비디오 파일이 없습니다. 또는 결과가 없습니다.")

if __name__ == "__main__":
    with sync_playwright() as playwright:
        run_example_scenario_test(playwright) 