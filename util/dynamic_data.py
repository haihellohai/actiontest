# util/dynamic_data.py

# 동적으로 사용할 데이터의 초기값을 모두 None으로 설정
_dynamic_data = {
    'record_process': None,
    'record_filename': None,
    'record_device_path': None,

    'env': None,
    'id': None,
    'pw': None,
    'device_type': None,
    'device_info': None,
    
    'build': None,
    'app_package': None,
    'app_activity': None,

    'resize_factor': 0.0,
    'real_screen_width': None,
    'real_screen_height': None
}

def save_data(key, value):
    """
    동적 데이터 저장 함수
    """
    _dynamic_data[key] = value

def load_data(key):
    """
    동적 데이터 불러오기 함수
    """
    return _dynamic_data.get(key)

def get_all_data():
    """
    전체 동적 데이터 dict 반환
    """
    return _dynamic_data 