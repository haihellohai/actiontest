import os
import subprocess
import time
import datetime
import psutil
from PIL import Image
from typing import Optional, Tuple

from dotenv import load_dotenv
from util.dynamic_data import load_data, save_data

def get_env_or_raise(key: str) -> str:
    value = os.getenv(key)
    if value is None:
        raise RuntimeError(f"환경변수 '{key}'가 설정되어 있지 않습니다.")
    return value

EMAIL = get_env_or_raise("id")
save_data('id', EMAIL)
PASSWORD = get_env_or_raise("pw")
save_data('pw', PASSWORD)
ENV = get_env_or_raise("env")
save_data('env', ENV)
BUILD = get_env_or_raise("build")
save_data('build', BUILD)

from util.adb_util import tap_on_device, ensure_adb_connection, capture_screen
from util.button_util import 버튼_찾기_클릭
# 텍스트_찾기_클릭, 텍스트_찾기, print_all_ocr_text를 사용하는 함수 내부에서만 import하도록 변경
from util.dynamic_data import save_data, load_data

if BUILD == "Unreal" or "UE":
    app_package = "com.Krafton.gpp.sdk.ue.sample"
    app_activity= "com.epicgames.ue4.SplashActivity"
elif BUILD == "Unity" or "unity":
    app_package = "com.Krafton.gpp.sdk.sample"
    app_activity= "com.epicgames.ue4.SplashActivity"

# 1) 에뮬레이터가 실행 중인지 확인
def is_emulator_running() -> bool:
    """
    Google Play 게임즈 개발자 에뮬레이터가 실행 중인지 확인
    :return: 실행 중 여부
    """
    print("[DEBUG] 함수 이름: is_emulator_running")
    print("[DEBUG] 에뮬레이터가 실행 중인지 확인합니다.")
    for proc in psutil.process_iter(['pid', 'name']):
        try:
            # 실제 프로세스명 반영
            if 'crosvm' in proc.info['name']:
                print("[DEBUG] 에뮬레이터가 실행 되어있습니다.")
                return True
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    print("[DEBUG] 에뮬레이터가 실행 되어있지 않습니다.")
    return False

# 2) 에뮬레이터와 ADB 연결 시도
def ensure_adb_connection(port: int = 6520):
    """
    연결된 디바이스가 없으면 adb connect localhost:{port}로 연결을 시도
    :param port: 에뮬레이터 포트 (기본 6520)
    :return: 연결 성공 여부
    """
    print("[DEBUG] 함수 이름: ensure_adb_connection")
    print("[DEBUG] 에뮬레이터에 ADB를 연결합니다.")
    # 1. 현재 연결된 디바이스 확인
    result = subprocess.run(["adb", "devices"], capture_output=True, text=True)
    lines = result.stdout.strip().splitlines()
    devices = [line for line in lines[1:] if line.strip() and "device" in line]
    if devices:
        print(f"[DEBUG] ADB 연결 디바이스 확인: {devices}")
        # Show taps(터치 이펙트) 활성화
        subprocess.run(["adb", "shell", "settings", "put", "system", "show_touches", "1"], capture_output=True, text=True)
        #subprocess.run(["adb", "shell", "settings", "put", "system", "pointer_location", "1"], capture_output=True, text=True)
        print(f"[DEBUG] ADB 터치 이펙트 활성화 완료")
        return True
    # 2. 연결 시도
    print(f"[DEBUG] 연결된 디바이스가 없어 adb connect localhost:{port} 시도")
    connect_result = subprocess.run(["adb", "connect", f"localhost:{port}"], capture_output=True, text=True)
    print(connect_result.stdout.strip())
    # 3. 다시 확인
    result = subprocess.run(["adb", "devices"], capture_output=True, text=True)
    lines = result.stdout.strip().splitlines()
    devices = [line for line in lines[1:] if line.strip() and "device" in line]
    if devices:
        print(f"[DEBUG] 연결 성공: {devices}")
        subprocess.run(["adb", "shell", "settings", "put", "system", "show_touches", "1"], capture_output=True, text=True)
        #subprocess.run(["adb", "shell", "settings", "put", "system", "pointer_location", "1"], capture_output=True, text=True)
        print(f"[DEBUG] ADB 터치 이펙트 활성화 완료")
        return True
    raise Exception("[ERROR] adb connect 실패")

# 3. 에뮬레이터 실행 - 아마 안될듯
def start_emulator():
    """
    Google Play 게임즈 개발자 에뮬레이터 실행
    """
    print("[DEBUG] 함수 이름: start_emulator")
    print("[DEBUG] 에뮬레이터를 실행합니다.")
    try:
        # Google Play 게임즈 에뮬레이터 실행 명령어 (실제 경로에 맞게 수정 필요)
        emulator_path = r"C:\Program Files\Google\Play Games Developer Emulator\Bootstrapper.exe"
        subprocess.Popen([emulator_path], shell=True)
        print("[DEBUG] Google Play 게임즈 개발자 에뮬레이터 실행 명령 전송")
    except Exception as e:
        print(f"[ERROR] 에뮬레이터 실행 실패: {e}")
        raise Exception("Google Play 게임즈 개발자 에뮬레이터 실행에 실패했습니다.")

# 4. 에뮬레이터 실행 대기
def wait_for_emulator_startup(timeout_seconds: int = 60):
    """
    에뮬레이터가 실행될 때까지 대기
    :param timeout_seconds: 최대 대기 시간(초)
    :return: 실행 성공 여부
    """
    print("[DEBUG] 함수 이름: wait_for_emulator_startup")
    print("[DEBUG] 에뮬레이터가 실행되는 것을 대기합니다. 최대 60초")
    start_time = time.time()
    while time.time() - start_time < timeout_seconds:
        if is_emulator_running():
            print("[INFO] Google Play 게임즈 개발자 에뮬레이터가 실행되었습니다.")
            time.sleep(10)
            return
        time.sleep(2)  # 2초마다 확인
    raise Exception(f"에뮬레이터가 {timeout_seconds}초 동안 실행되지 않았습니다.")

# 5. 앱 실행 여부 확인
def check_app_running() -> bool:
    """
    앱이 현재 실행 중이거나 백그라운드에 존재하는지 확인
    앱이 백그라운드에서 실행 중이면 강제 종료하고 False를 반환
    (모바일 디바이스에서는 pidof 사용, 에뮬레이터는 기존 로직 유지)
    :param app_package: 앱 패키지명 (예: com.Krafton.gpp.sdk.ue.sample)
    :return: 실행 여부 (True: 포그라운드 실행 중, False: 완전히 종료됨)
    """
    print("[DEBUG] 함수 이름: check_app_running")
    print(f"[DEBUG] {app_package}가 실행 중인지 확인합니다.")

    device_type = load_data('device_type')
    device_info = load_data('device_info')
    adb_base = ["adb"]
    if device_type == "device" and device_info:
        adb_base += ["-s", device_info]

        # ✅ 모바일 기기: dumpsys + pidof 조합으로 포그라운드 + 백그라운드 확인
        try:
            result = subprocess.run(
                adb_base + ["shell", "dumpsys", "activity", "activities"],
                capture_output=True, text=True
            )
            if "topResumedActivity" in result.stdout or "mResumedActivity" in result.stdout:
                resumed_lines = [
                    line for line in result.stdout.splitlines()
                    if "topResumedActivity" in line or "mResumedActivity" in line
                ]
                for line in resumed_lines:
                    if app_package in line:
                        print(f"[DEBUG] 현재 포커스 앱이 {app_package}입니다.")
                        return True
        except Exception as e:
            print(f"[ERROR] dumpsys 실행 실패: {e}")

        try:
            pidof_result = subprocess.run(
                adb_base + ["shell", "pidof", app_package],
                capture_output=True, text=True
            )
            if pidof_result.returncode == 0 and pidof_result.stdout.strip():
                print(f"[DEBUG] {app_package} 프로세스가 백그라운드에 존재합니다. 강제 종료합니다.")
                # 앱 강제 종료
                force_stop_result = subprocess.run(
                    adb_base + ["shell", "am", "force-stop", app_package],
                    capture_output=True, text=True
                )
                if force_stop_result.returncode == 0:
                    print(f"[DEBUG] {app_package} 강제 종료 완료.")
                else:
                    print(f"[ERROR] {app_package} 강제 종료 실패: {force_stop_result.stderr}")
                return False
        except Exception as e:
            print(f"[ERROR] pidof 실행 실패: {e}")

        print(f"[DEBUG] {app_package}가 실행 중이지 않습니다.")
        return False

    else:
        # ✅ 에뮬레이터 또는 기타 환경: 기존 방식 유지 (dumpsys + ps)
        try:
            result = subprocess.run(
                adb_base + ["shell", "dumpsys", "activity", "activities"],
                capture_output=True, text=True
            )
            if result.returncode == 0:
                if app_package in result.stdout:
                    print(f"[DEBUG] {app_package}가 실행 중입니다.")
                    return True
                else:
                    # ps로 백업 확인
                    ps_result = subprocess.run(
                        adb_base + ["shell", "ps"],
                        capture_output=True, text=True
                    )
                    if ps_result.returncode == 0 and app_package in ps_result.stdout:
                        print(f"[DEBUG] {app_package} 프로세스가 백그라운드에 존재합니다. 강제 종료합니다.")
                        # 앱 강제 종료
                        force_stop_result = subprocess.run(
                            adb_base + ["shell", "am", "force-stop", app_package],
                            capture_output=True, text=True
                        )
                        if force_stop_result.returncode == 0:
                            print(f"[DEBUG] {app_package} 강제 종료 완료.")
                        else:
                            print(f"[ERROR] {app_package} 강제 종료 실패: {force_stop_result.stderr}")
                        return False
        except Exception as e:
            print(f"[ERROR] adb 명령 실행 실패: {e}")

        print(f"[DEBUG] {app_package}가 실행 중이지 않습니다.")
        return False

# 6. 앱 실행
def start_app():
    """
    앱을 실행 (에뮬레이터는 am start, 모바일 디바이스는 monkey 방식)
    :return: 앱 실행 여부
    """
    print("[DEBUG] 함수 이름: start_app")
    print(f"[DEBUG] {app_package}를 실행 시도합니다.")

    device_type = load_data('device_type')
    device_info = load_data('device_info')
    adb_base = ["adb"]
    if device_info:
        adb_base += ["-s", device_info]

    try:
        if device_type == "device":
            # ✅ 실제 디바이스: monkey 방식 (exported 제한 없음)
            print("[INFO] 실제 디바이스에서 monkey 방식으로 앱 실행 중...")
            result = subprocess.run(
                adb_base + [
                    "shell", "monkey",
                    "-p", app_package,
                    "-c", "android.intent.category.LAUNCHER", "1"
                ],
                capture_output=True, text=True
            )
        else:
            # ✅ 에뮬레이터: 기존 방식 유지
            print("[INFO] 에뮬레이터 환경에서 am start 방식으로 앱 실행 중...")
            result = subprocess.run(
                adb_base + [
                    "shell", "am", "start",
                    "-n", f"{app_package}/{app_activity}"
                ],
                capture_output=True, text=True
            )

        # 실행 결과 확인
        if result.returncode == 0:
            print("[INFO] 앱 실행 완료.")
            time.sleep(5)
        else:
            print(f"[ERROR] 앱 실행 실패: {result.stderr}")
            raise Exception("앱 실행에 실패했습니다.")

    except Exception as e:
        print(f"[ERROR] 앱 실행 중 예외 발생: {e}")
        raise

# 7. 앱 종료
def quit_app(process_name: str = "crosvm"):
    """
    앱을 종료
    :process_name: 프로세스 이름
    """
    print("[DEBUG] 함수 이름: quit_app")
    print(f"[DEBUG] 프로세스 네임({process_name})이 실행 중인지 확인합니다.")
    if check_app_running():
        for proc in psutil.process_iter(['pid', 'name', 'exe']):
            try:
                if proc.info['name'] == 'crosvm.exe':
                    proc.terminate()
                    try:
                        proc.wait(timeout=5)
                        print(f"[SUCCESS] 정상 종료됨: {proc.info['name']} (PID: {proc.pid})")
                    except psutil.TimeoutExpired:
                        print(f"[WARN] 종료 대기 시간 초과. 강제 종료 시도: {proc.info['name']} (PID: {proc.pid})")
                        proc.kill()
                        print(f"[FORCE] 강제 종료됨: {proc.info['name']} (PID: {proc.pid})")

            except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
                print(f"[ERROR] 프로세스 접근 실패 (PID: {proc.pid}) - {e}")     

def get_adb_devices():
    result = subprocess.run(['adb', 'devices'], capture_output=True, text=True)
    lines = result.stdout.strip().split('\n')[1:]  # 첫 줄은 헤더
    devices = []
    for line in lines:
        if line.strip():
            serial, status = line.split()
            if serial.startswith('emulator-'):
                device_type = 'emulator'
            else:
                device_type = 'device'
            devices.append({'serial': serial, 'type': device_type, 'status': status})
    save_data('device_type', status)
    save_data('device_info', serial)
    return devices

def start_screen_record(
    filename_prefix: str = "record",
    device_serial: Optional[str] = None,
    bit_rate: int = 8000000,
    size: Optional[str] = None
) -> Optional[Tuple[subprocess.Popen, str, str]]:
    """
    ADB를 통해 Android 기기 화면 녹화를 백그라운드에서 시작합니다.

    :param filename_prefix: 파일 이름 접두어 (타임스탬프가 자동 추가됨)
    :param device_serial: ADB 디바이스 시리얼 넘버 (옵션)
    :param bit_rate: 비디오 비트레이트 (기본: 8Mbps)
    :param size: 해상도 지정 문자열 예: "1080x2400" (옵션)
    :return: (subprocess.Popen 객체, 파일 이름, 디바이스 내 저장 경로)
    """
    # 타임스탬프 기반 파일명 생성
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    record_filename = f"{filename_prefix}_{timestamp}.mp4"
    device_path = f"/sdcard/{record_filename}"

    # ADB 명령어 구성
    cmd = ["adb"]
    if device_serial:
        cmd += ["-s", device_serial]
    cmd += ["shell", "screenrecord", f"--bit-rate={bit_rate}"]
    if size:
        cmd += [f"--size={size}"]
    cmd += [device_path]

    # 녹화 프로세스 실행 (백그라운드)
    record_process = subprocess.Popen(cmd)
    save_data('record_process', record_process)
    save_data('record_filename', record_filename)
    save_data('record_device_path', device_path)

    if record_process.returncode != 0:
        print(f"[ERROR] screenrecord 명령 실패: {record_process.stderr}")
        return None

    return (record_process, record_filename, device_path)

def stop_screen_record_and_pull(
    local_dir: str = ".",
) -> str:
    """
    실행 중인 화면 녹화를 종료하고, 기기에서 PC로 영상을 가져옵니다.

    :param process: start_screen_record()에서 반환된 subprocess.Popen 객체
    :param device_path: 기기 내 저장 경로 (예: /sdcard/record_20250708_175955.mp4)
    :param local_dir: PC로 저장할 디렉토리 경로 (기본: 현재 폴더)
    :param device_serial: 디바이스 시리얼 넘버 (선택)
    :return: 로컬에 저장된 영상 파일 경로
    """
    process = load_data('record_process')
    if process is None:
        raise Exception("녹화 프로세스 정보가 없습니다. start_screen_record()가 정상적으로 실행되었는지 확인하세요.")
    device_path = load_data('record_device_path')
    if not device_path:
        raise Exception("녹화 파일 경로 정보가 없습니다. start_screen_record()가 정상적으로 실행되었는지 확인하세요.")
    device_serial = load_data('device_info')
    # 1. 녹화 종료
    process.terminate()
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()

    # 2. 로컬 저장 경로 생성
    filename = os.path.basename(device_path)
    local_path = os.path.join(local_dir, filename)

    # 3. ADB pull 실행
    cmd = ["adb"]
    if device_serial:
        cmd += ["-s", device_serial]
    cmd += ["pull", device_path, local_path]

    subprocess.run(cmd, check=True)

    return local_path

def test_setup(port: int = 6520):
    """
    테스트 준비 단계: 에뮬레이터 실행 확인, ADB 연결, Show taps(터치 이펙트) 활성화, 앱 실행
    :param port: 에뮬레이터 포트 (기본 6520)
    :param app_package: 앱 패키지명
    :param app_activity: 앱 메인 액티비티명
    :return: 연결 및 설정 성공 여부
    """
    devices = get_adb_devices()
    print(f"[DEBUG] 연결된 ADB 디바이스: {devices}")
    
    if not devices:
        print("[ERROR] ADB 디바이스가 없습니다.")
        raise Exception("ADB 디바이스가 없습니다.")
    if len(devices) > 1:
        print(f"[ERROR] 여러 개의 ADB 디바이스가 연결되어 있습니다: {devices}")
        raise Exception("여러 개의 ADB 디바이스가 연결되어 있습니다. 하나만 연결해주세요.")

    device = devices[0]
    if device['type'] == 'emulator':
        if not is_emulator_running():
            start_emulator()
            wait_for_emulator_startup()
        ensure_adb_connection()

    if not check_app_running():
        start_app()
        #앱 로딩이 있어서 활성화 여부를 확인하는게 필요할듯
    save_real_screen_size()

def send_keys(key_value:str):
    KEYCODE_MAP = {
    "Tab": 61,
    "Enter": 66,
    "Back": 4,
    "Del": 67,
    "Delete": 67,
    "Home": 3,
    "Menu": 82,
    "Up": 19,
    "Down": 20,
    "Left": 21,
    "Right": 22,
    "Space": 62,
    "Escape": 111,
    "Search": 84,
    "Camera": 27,
    "VolumeUp": 24,
    "VolumeDown": 25,
    "Power": 26
    }
    if key_value in KEYCODE_MAP:
        keycode = KEYCODE_MAP[key_value]
        print(f"입력 키: {key_value} (KEYCODE {keycode})")
        subprocess.run(["adb", "shell", "input", "keyevent", str(keycode)])
    else:
        # 일반 문자열로 간주 → adb text
        #encoded = key_value.replace(" ", "%s").replace("&", "%26").replace(":", "%3A")
        print(f"입력 텍스트: {key_value}")
        subprocess.run(["adb", "shell", "input", "text", key_value])


def swipe_direction(
    direction: str,
    x: int = 540,
    y_center: int = 1000,
    distance: int = 600,  # 기본값 600으로 변경
    duration: int = 800,
):
    direction = direction.lower()
    device_serial = load_data('device_info')
    if direction == "up":
        x1, y1, x2, y2 = x, y_center, x, y_center - distance
    elif direction == "down":
        x1, y1, x2, y2 = x, y_center, x, y_center + distance
    elif direction == "left":
        x1, y1, x2, y2 = x, y_center, x - distance, y_center
    elif direction == "right":
        x1, y1, x2, y2 = x, y_center, x + distance, y_center
    else:
        raise ValueError("direction must be one of: up, down, left, right")

    cmd = ["adb"]
    if device_serial:
        cmd += ["-s", device_serial]
    cmd += ["shell", "input", "swipe", str(x1), str(y1), str(x2), str(y2), str(duration)]

    subprocess.run(cmd)

def swipe_until_text_found(
    text: str,
    direction: str = "up",
    max_swipes: int = 5,
    delay: float = 0.5,
    **swipe_kwargs
) -> bool:
    """
    특정 텍스트가 화면에 나타날 때까지 최대 max_swipes번 스와이프하며 찾기
    :param text: 찾을 텍스트
    :param direction: 스와이프 방향 (기본: up)
    :param max_swipes: 최대 스와이프 횟수
    :param delay: 각 스와이프 후 대기 시간(초)
    :param swipe_kwargs: swipe_direction에 전달할 추가 인자
    :return: 찾으면 True, 못 찾으면 False
    """
    for attempt in range(max_swipes):
        # 텍스트_찾기_클릭, 텍스트_찾기, print_all_ocr_text를 사용하는 함수 내부에서만 import하도록 변경
        from util.text_util import 텍스트_찾기_클릭, 텍스트_찾기, print_all_ocr_text
        found = 텍스트_찾기(text, must_exist=False)
        if found:
            print(f"[✔] '{text}' 텍스트를 {attempt+1}회 만에 찾았습니다.")
            return True
        swipe_direction(direction, **swipe_kwargs)
        time.sleep(delay)
    print(f"[✖] 최대 {max_swipes}회 스와이프에도 '{text}' 텍스트를 찾지 못했습니다.")
    return False

def login(login_type="email", email=None, password=None):
    """
    다양한 로그인 방식을 지원하는 공통 로그인 함수.
    현재는 'email' 타입만 지원하며, Playwright page 객체를 사용해 로그인한다.
    :param page: Playwright page 객체
    :param login_type: 로그인 방식 (기본값 'email')
    :param email: 이메일 주소
    :param password: 비밀번호
    """
    from util.text_util import 텍스트_찾기_클릭, 텍스트_찾기, print_all_ocr_text
    if login_type == "email":
        if not 버튼_찾기_클릭("Krafton ID로 로그인", must_exist=False, delay=3):
            텍스트_찾기_클릭("Krafton ID", 5)
        if 텍스트_찾기("로그인했던", must_exist=False):
            swipe_until_text_found("다른 계정으로")
            텍스트_찾기_클릭("다른 계정으로") #여기가 문제.. 좌표 문제?
            # 버튼_찾기_클릭("다른 계정으로 로그인")
        time.sleep(5)
        send_keys("Tab")
        send_keys(EMAIL)
        send_keys("Tab")
        send_keys(PASSWORD)
        send_keys("Enter")
        time.sleep(10)
        if 텍스트_찾기("*계정*선택*"):
            텍스트_찾기_클릭("Lv.*")
            swipe_direction('up')
            swipe_direction('up')
            버튼_찾기_클릭('연결')
            time.sleep(3)
            swipe_direction('up')
            버튼_찾기_클릭('선택')
            time.sleep(3)
            # swipe_until_text_found("연결")
        
        버튼_찾기_클릭("모두 동의하고 시작", delay=3, must_exist=False)
        if 텍스트_찾기("GENERAL_SUCCESS"): #검증 포인트
            버튼_찾기_클릭("닫기")
            return True
            
    elif login_type == "Facebook" or login_type == "facebook":
        텍스트_찾기_클릭("Facebook*", 5)
        텍스트_찾기_클릭("*으로 계속", 5)
        if 텍스트_찾기("*계정*선택*", must_exist=False):
            텍스트_찾기_클릭("Lv.*")
            swipe_direction('up')
            swipe_direction('up')
            버튼_찾기_클릭('연결')
            time.sleep(3)
            swipe_direction('up')
            버튼_찾기_클릭('선택')
            time.sleep(3)

    elif login_type == "google" or login_type == "Google":
        if 텍스트_찾기(EMAIL, must_exist=False):
            버튼_찾기_클릭("이 계정으로 플레이")
        else:
            텍스트_찾기_클릭("Google", 5)
            텍스트_찾기_클릭(EMAIL)
            if 텍스트_찾기("*계정*선택*", must_exist=False):
                텍스트_찾기_클릭("Lv.*")
                swipe_direction('up')
                swipe_direction('up')
                버튼_찾기_클릭('연결')
                time.sleep(3)
                swipe_direction('up')
                버튼_찾기_클릭('선택')
                time.sleep(3)
        버튼_찾기_클릭("모두 동의하고 시작", delay=3, must_exist=False)
        if 텍스트_찾기("GENERAL_SUCCESS"): #검증 포인트
            버튼_찾기_클릭("닫기")
            return True
            
    elif login_type == "Apple" or login_type == "apple":
        텍스트_찾기_클릭("Apple", 5)
        send_keys(EMAIL)
        send_keys("Enter")
        send_keys(PASSWORD)
        send_keys("Enter")
        
    elif login_type == "Discord" or login_type == "discord":
        텍스트_찾기_클릭("Discord*", 5)

def save_real_screen_size():
    """
    adb shell wm size 명령으로 실제 화면 해상도를 dynamic_data에 저장
    """
    import re
    import subprocess
    from util.dynamic_data import save_data
    result = subprocess.run(["adb", "shell", "wm", "size"], capture_output=True, text=True)
    match = re.search(r'Physical size: (\d+)x(\d+)', result.stdout)
    if match:
        width, height = int(match.group(1)), int(match.group(2))
        save_data('real_screen_width', width)
        save_data('real_screen_height', height)
        print(f"[INFO] 실제 화면 해상도: {width}x{height} 저장 완료")
        return width, height
    else:
        print("[ERROR] adb shell wm size 결과에서 해상도를 찾지 못했습니다.")
        return None, None