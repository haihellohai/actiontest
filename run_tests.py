from playwright.sync_api import sync_playwright
from test_common import *
from test_login_playwright import run_kid_login_test
from test_admin_portal import run_example_scenario_test
import sys


def execute_kid_login_test():
    """1. KID 로그인 테스트를 실행하고 결과를 저장합니다."""
    print("\n=== KID 로그인 테스트 실행 ===")
    reset_test_data()
    video_path = None
    try:
        with sync_playwright() as playwright:
            run_kid_login_test(playwright)
    except Exception as e:
        add_na_checkpoint_on_error(str(e))
    finally:
        build_url = "https://gamma.accounts.krafton.dev/v2/ko/web/login-main?type=last-login"
        test_env = "QA"
        test_results = get_test_results()
        for r in reversed(test_results):
            if r.get('video') and r['video'].startswith('video/'):
                video_path = r['video']
                break
        save_test_results_and_report(build_url, test_env, video_path)
        generate_report_and_open(build_url, test_env, video_path)
        reset_test_data()
        print("KID 로그인 테스트 완료!")

def execute_admin_portal_test():
    """2. Admin Portal 테스트를 실행하고 결과를 저장합니다."""
    print("\n=== Admin Portal 네임스페이스 테스트 실행 ===")
    reset_test_data()
    video_path = None
    try:
        with sync_playwright() as playwright:
            run_example_scenario_test(playwright)
    except Exception as e:
        add_na_checkpoint_on_error(str(e))
    finally:
        build_url = "https://qa.gpp.krafton.dev/admin/namespaces"
        test_env = "QA"
        test_results = get_test_results()
        for r in reversed(test_results):
            if r.get('video') and r['video'].startswith('video/'):
                video_path = r['video']
                break
        save_test_results_and_report(build_url, test_env, video_path)
        generate_report_and_open(build_url, test_env, video_path)
        reset_test_data()
        print("Admin Portal 네임스페이스 테스트 완료!")
        
def add_na_checkpoint_on_error(error_msg):
    # 마지막 체크리스트 3이름을 가져오거나, 없으면 'Unknown'
    test_results = get_test_results()
    last_check = test_results[-1]['checklist'] if test_results else 'Unknown'
    result(last_check, "N/A", f"테스트 중 예외 발생: {error_msg}")


def main():
    
    """메인 테스트 실행 함수"""
    # sys.argv는 프로그램을 실행할 때 전달된 인자들의 리스트입니다.
    # len(sys.argv) > 1 은 인자가 최소 1개 이상 들어왔다는 의미입니다.
    # (예: python run_tests.py 1)
    if len(sys.argv) > 1:
        choice = sys.argv[1]
    else:
        # 인자가 없으면 기존처럼 사용자에게 메뉴를 보여줍니다.
        print("=== 테스트 실행기 ===")
        print("1. KID 로그인 테스트")
        print("2. Admin Portal 네임스페이스 테스트")
        print("3. 모든 테스트 실행")
        print("4. 종료")
        choice = input("\n실행할 테스트를 선택하세요 (1-4): ").strip()
        
   # 사용자의 선택에 따라 분리된 함수를 호출합니다.
    if choice == "1":
        execute_kid_login_test()
    elif choice == "2":
        execute_admin_portal_test()
    elif choice == "3":
        print("\n=== 모든 테스트 실행 ===")
        execute_kid_login_test()
        execute_admin_portal_test()
        print("\n모든 테스트 완료!")
    elif choice == "4":
        if len(sys.argv) == 1: # 터미널에서 직접 실행했을 때만 종료 메시지 출력
            print("테스트 실행기를 종료합니다.")
    else:
        print("잘못된 선택입니다. 1-4 중에서 선택해주세요.")

if __name__ == "__main__":
    main() 