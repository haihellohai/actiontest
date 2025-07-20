from time import sleep

from util.button_util import 버튼_찾기_클릭
from util.text_util import 텍스트_찾기_클릭
from util.common_util import test_setup, login, start_screen_record, stop_screen_record_and_pull

test_setup()
start_screen_record()
# 버튼_찾기_클릭("qa")
# 버튼_찾기_클릭("Next")
# 버튼_찾기_클릭("게스트 강제 로그인", delay=5)
# 버튼_찾기_클릭("게스트로 시작하기", delay=5, must_exist=False)
# 버튼_찾기_클릭("모두 동의하고 시작", delay=3, must_exist=False)
# 버튼_찾기_클릭("LinkKID", delay=3)
# 버튼_찾기_클릭("로그인", delay=5)
login(login_type="apple")
stop_screen_record_and_pull()
