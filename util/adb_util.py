import os
import subprocess
import time
from PIL import Image
from util.dynamic_data import load_data, save_data

def capture_screen(
    path: str = "screen.png",
    adb_path: str = "adb",
) -> bool:
    """
    에뮬레이터 또는 모바일 기기 화면을 캡처하여 저장
    :param path: 저장할 파일 경로
    :param adb_path: adb 실행 파일 경로 또는 명령어
    :return: 성공 여부(bool)
    """
    from util.adb_util import ensure_adb_connection
    if not ensure_adb_connection():
        print("[ERROR] ADB 디바이스 연결 실패. 스크린샷 캡처를 건너뜁니다.")
        raise Exception("ADB 연결에 실패했습니다.")

    if os.path.exists(path):
        os.remove(path)

    device_type = load_data('device_type')
    device_info = load_data('device_info')

    adb_base = [adb_path]
    if device_type == "device" and device_info:
        adb_base += ["-s", device_info]
        temp_remote_path = "/sdcard/__temp_screen__.png"
        print("[INFO] 모바일 기기 감지됨. 안전한 screencap 방식으로 처리합니다.")
        subprocess.run(adb_base + ["shell", "screencap", "-p", temp_remote_path])
        subprocess.run(adb_base + ["pull", temp_remote_path, path])
        subprocess.run(adb_base + ["shell", "rm", temp_remote_path])
    else:
        print("[INFO] 에뮬레이터 감지됨. exec-out 방식으로 처리합니다.")
        adb_cmd = adb_base + ["exec-out", "screencap", "-p"]
        with open(path, "wb") as f:
            proc = subprocess.run(adb_cmd, stdout=f)
        print(f"[DEBUG] adb 실행 결과: {proc.returncode}")

    try:
        with Image.open(path) as img:
            img.verify()
        return True
    except Exception:
        raise Exception("스크린샷이 저장되었지만 손상되었거나 열 수 없습니다.")

def tap_on_device(x, y):
    subprocess.run(f"adb shell input tap {x} {y}", shell=True)
    print(f"[✔] ADB 클릭 수행: ({x}, {y})")

def ensure_adb_connection(port: int = 6520):
    print("[DEBUG] 함수 이름: ensure_adb_connection")
    print("[DEBUG] 에뮬레이터에 ADB를 연결합니다.")
    result = subprocess.run(["adb", "devices"], capture_output=True, text=True)
    lines = result.stdout.strip().splitlines()
    devices = [line for line in lines[1:] if line.strip() and "device" in line]
    if devices:
        print(f"[DEBUG] ADB 연결 디바이스 확인: {devices}")
        subprocess.run(["adb", "shell", "settings", "put", "system", "show_touches", "1"], capture_output=True, text=True)
        print(f"[DEBUG] ADB 터치 이펙트 활성화 완료")
        return True
    print(f"[DEBUG] 연결된 디바이스가 없어 adb connect localhost:{port} 시도")
    connect_result = subprocess.run(["adb", "connect", f"localhost:{port}"], capture_output=True, text=True)
    print(connect_result.stdout.strip())
    result = subprocess.run(["adb", "devices"], capture_output=True, text=True)
    lines = result.stdout.strip().splitlines()
    devices = [line for line in lines[1:] if line.strip() and "device" in line]
    if devices:
        print(f"[DEBUG] 연결 성공: {devices}")
        subprocess.run(["adb", "shell", "settings", "put", "system", "show_touches", "1"], capture_output=True, text=True)
        print(f"[DEBUG] ADB 터치 이펙트 활성화 완료")
        return True
    raise Exception("[ERROR] adb connect 실패") 