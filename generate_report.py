# pyright: reportUndefinedVariable=false
# type: ignore
import json
from datetime import datetime
import os
import re

BUILD_ENV = "QA"
build_url = "https://your-web-url.example.com"  # 실제 URL로 교체

def save_report_html(test_results, logs, filename="test_report.html", build_number="-", test_env="-", video_path=None):
    # 테스트 수행 시점 (YYYYMMDD_HHMMSS)
    now_dt = datetime.now()
    now = now_dt.strftime("%Y-%m-%d %H:%M:%S")
    now_for_filename = now_dt.strftime("%Y%m%d_%H%M%S")
    env_for_filename = test_env.replace(' ', '_')
    
    # Pass 비율 계산 (파일명용)
    total = len([r for r in test_results if r['value'] in ['Pass', 'Fail']])
    passed = len([r for r in test_results if r['value'] == 'Pass'])
    pass_ratio_val = (passed/total*100) if total > 0 else 0
    pass_ratio_filename = f"{pass_ratio_val:.0f}%" if total > 0 else "0%"
    
    if filename == "test_report.html":
        filename = f"reports/test_report_{now_for_filename}_{env_for_filename}.html"

    # 절대 경로 계산
    base_dir = os.path.dirname(os.path.abspath(filename))
    parent_dir = os.path.dirname(base_dir)
    
    # 스크린샷과 비디오 경로를 절대 경로로 변환
    def get_absolute_path(relative_path):
        if relative_path:
            if relative_path.startswith("file:///"):
                return relative_path
            abs_path = os.path.abspath(relative_path).replace('\\', '/')
            return f"file:///{abs_path}"
        return None
    
    # 비디오 경로를 절대 경로로 변환
    if video_path:
        video_abs_path = get_absolute_path(video_path)
    else:
        video_abs_path = None

    # Pass 비율 계산
    total = len([r for r in test_results if r['value'] in ['Pass', 'Fail']])
    passed = len([r for r in test_results if r['value'] == 'Pass'])
    pass_ratio_val = (passed/total*100) if total > 0 else 0
    pass_ratio = f"{pass_ratio_val:.0f}%" if total > 0 else "-"
    is_full_pass = pass_ratio_val == 100.0 and total > 0
    status_html = (
        f"<div class='result-summary-status-label fail'>확인 필요</div>"
        f"<div class='result-summary-status-value fail'>{pass_ratio}</div>"
        if not is_full_pass else
        f"<div class='result-summary-status-label pass'>이상 없음</div>"
        f"<div class='result-summary-status-value pass'>{pass_ratio}</div>"
    )

    gauge_color = "#388e3c" if is_full_pass else ("#1976d2" if pass_ratio_val >= 70 else "#d32f2f")
    gauge_text_color = "#fff" if is_full_pass else ("#222" if pass_ratio_val >= 70 else "#fff")
    gauge_shadow = "0 0 16px #388e3c88" if is_full_pass else "none"
    gauge_text_shadow = "0 0 8px #388e3c" if is_full_pass else "none"

    # 비디오 리스트 추출 (중복 없이, 순서대로)
    video_items = []
    seen_videos = set()
    for r in test_results:
        if r.get('video') and r['video'] and r['video'] != 'None' and r['video'] not in seen_videos:
            video_abs_path = get_absolute_path(r['video'])
            if video_abs_path:
                video_items.append({'video': video_abs_path, 'label': r['checklist']})
                seen_videos.add(r['video'])

    # 영상 섹션 렌더링 부분 (html 생성 전에 위치)
    video_section_html = ''
    try:
        if video_items:
            video_section_html = ''.join([
                f'<div style="margin-bottom:32px;">'
                f'<div style="font-weight:bold; margin-bottom:8px;">{item["label"]}</div>'  # 체크리스트 이름으로 표시
                f'<video controls style="width:100%;max-width:800px;display:block;margin-bottom:4px;"><source src="{item["video"]}" type="video/webm">브라우저가 video 태그를 지원하지 않습니다.</video>'
                f'</div>'
                for i, item in enumerate(video_items)
            ])
        else:
            video_section_html = '<p>녹화된 영상이 없습니다.</p>'
    except Exception as e:
        video_section_html = f'<p>영상 정보를 표시하는 중 오류가 발생했습니다: {e}</p>'

    # 1차: 임시로 리포트 파일을 먼저 저장 (history_html은 placeholder)
    html = f"""
    <!DOCTYPE html>
    <html lang=\"ko\">
    <head>
        <meta charset=\"UTF-8\">
        <title>테스트 리포트</title>
        <link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css">
        <style>
            body {{ font-family: 'Pretendard', Arial, sans-serif; margin: 40px; background: #f7f9fa; }}
            h1 {{ color: #388e3c; text-align: center; font-size: 2.6em; margin-bottom: 0.2em; }}
            h2 {{ color: #444; border-bottom: 2px solid #e0e0e0; padding-bottom: 4px; margin-top: 0; text-align: left; }}
            .section {{ background: #fff; border-radius: 10px; box-shadow: 0 2px 8px #0001; margin-bottom: 32px; padding: 32px; max-width: 900px; min-width: 600px; margin-left: auto; margin-right: auto; }}
            .summary-section.section {{
                margin-bottom: 40px;
                padding-top: 32px;
                padding-bottom: 32px;
            }}
            .summary-table {{ margin: 0 auto; }}
            .summary-table td {{ border: none; background: none; padding: 4px 0; text-align: center; font-size: 1.1em; }}
            .gauge-bar-bg {{ width: 100%; max-width: 800px; height: 32px; background: #e0e0e0; border-radius: 16px; margin: 18px auto 10px auto; overflow: hidden; box-shadow: 0 2px 8px #0001; }}
            .gauge-bar-fill {{ height: 100%; border-radius: 16px; transition: width 0.7s; display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 1.1em; box-shadow: {gauge_shadow}; background: {gauge_color}; color: {gauge_text_color}; text-shadow: {gauge_text_shadow}; }}
            .result-section {{ max-width: 900px; min-width: 600px; margin: 0 auto 32px auto; text-align: left; }}
            table {{ border-collapse: collapse; width: 100%; margin-bottom: 40px; table-layout: fixed; }}
            th, td {{ border: 1px solid #e0e0e0; padding: 10px 14px; }}
            th {{ background: #f0f4f8; text-align: center; }}
            td.checklist, th.checklist {{ width: 220px; min-width: 180px; max-width: 260px; text-align: center; }}
            td.result, th.result {{ width: 70px; min-width: 60px; max-width: 80px; text-align: center; }}
            td.message, th.message {{ width: auto; min-width: 220px; max-width: 1000px; text-align: left; word-break: break-all; white-space: pre-line; }}
            td.screenshot, th.screenshot {{ width: 90px; min-width: 70px; max-width: 100px; text-align: center; }}
            td.video, th.video {{ min-width: 80px; max-width: 120px; }}
            td.message, th.message {{ word-break: break-all; white-space: pre-line; max-width: 600px; }}
            .result-table-wrap {{ overflow-x: auto; width: 100%; }}
            .pass {{ color: #1976d2; font-weight: bold; }}
            .fail {{ color: #d32f2f; font-weight: bold; }}
            .na {{ color: orange; font-weight: bold; }}
            .skip {{ color: gray; font-weight: bold; }}
            pre {{ background: #f8f8f8; padding: 16px; border-radius: 6px; font-size: 15px; text-align: left; max-width: 900px; margin: 0 auto; font-family: 'Pretendard', Arial, sans-serif; word-break: break-all; white-space: pre-line; }}
            .summary-hr {{ border: none; border-top: 1px solid #eee; margin: 4px 0; }}
            .result-summary-outer {{
                width: 100%;
                display: flex;
                justify-content: center;
                margin-bottom: 40px;
            }}
            .result-summary-block {{
                background: #fff;
                border-radius: 18px;
                box-shadow: 0 2px 8px #0001;
                padding: 32px;
                max-width: 900px;
                min-width: 600px;
                margin: 0 auto;
                text-align: center;
                color: #444;
            }}
            .result-summary-title {{
                font-size: 1.5em;
                font-weight: bold;
                margin-bottom: 10px;
                text-align: left;
                color: #444;
            }}
            .result-summary-hr {{
                border: none;
                border-top: 2px solid #ddd;
                margin: 0 0 24px 0;
            }}
            .result-summary-row {{
                display: flex;
                justify-content: center;
                gap: 20px;
                flex-wrap: nowrap;
            }}
            .result-summary-card {{
                background: #f3f3f3;
                border-radius: 18px;
                padding: 18px 18px 12px 18px;
                min-width: 100px;
                display: flex;
                flex-direction: column;
                align-items: center;
                box-shadow: none;
                justify-content: center;
            }}
            .result-summary-card.status {{
                background: none;
                border-radius: 0;
                box-shadow: none;
                min-width: 100px;
                padding: 0 10px;
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
            }}
            .result-summary-status-label.fail {{ color: #b71c1c; font-size: 1.15em; font-weight: bold; margin-bottom: 0.2em; }}
            .result-summary-status-value.fail {{ color: #b71c1c; font-size: 2.2em; font-weight: bold; }}
            .result-summary-status-label.pass {{ color: #1976d2; font-size: 1.15em; font-weight: bold; margin-bottom: 0.2em; }}
            .result-summary-status-value.pass {{ color: #1976d2; font-size: 2.2em; font-weight: bold; }}
            .result-summary-label.all, .result-summary-value.all {{ color: #111; }}
            .result-summary-label.pass, .result-summary-value.pass {{ color: #1976d2; }}
            .result-summary-label.fail, .result-summary-value.fail {{ color: #d32f2f; }}
            .result-summary-label.na, .result-summary-value.na {{ color: orange; }}
            .result-summary-label.skip, .result-summary-value.skip {{ color: gray; }}
            .result-summary-label {{
                font-size: 1.15em;
                font-weight: bold;
                margin-bottom: 10px;
                letter-spacing: -1px;
                text-align: center;
                color: #444;
            }}
            .result-summary-value {{
                font-size: 2.2em;
                font-weight: bold;
                margin-top: 0;
                text-align: center;
                color: #444;
            }}
            .tab-wrap {{ display: flex; gap: 0; margin-bottom: 24px; max-width: 900px; min-width: 600px; margin-left: auto; margin-right: auto; }}
            .tab-btn {{ width: 50%; padding: 8px 0; background: #f3f3f3; border: none; font-size: 1em; font-weight: bold; color: #888; cursor: pointer; border-radius: 12px 12px 0 0; transition: background 0.2s, color 0.2s; max-width: none; min-width: 0; }}
            .tab-btn.active {{ background: #fff; color: #444; border-bottom: 2px solid #fff; }}
            .tab-content {{ display: none; }}
            .tab-content.active {{ display: block; }}
            .history-list ul {{ list-style: none; padding: 0; }}
            .history-list li {{ margin-bottom: 8px; }}
            .history-list a {{ color: #1976d2; text-decoration: underline; }}
            /* 이미지 모달 */
            #img-modal {{
                display: none;
                position: fixed;
                z-index: 9999;
                left: 0; top: 0; width: 100vw; height: 100vh;
                background: rgba(0,0,0,0.7);
                justify-content: center;
                align-items: center;
                transition: background 0.2s;
            }}
            #img-modal.active {{ display: flex; }}
            #img-modal-img {{
                max-width: 80vw;
                max-height: 80vh;
                border-radius: 10px;
                box-shadow: 0 4px 32px #0008;
                background: #fff;
                padding: 8px;
            }}
        </style>
        <script>
        function showTab(tab) {{
            document.getElementById('tab-current').classList.remove('active');
            document.getElementById('tab-history').classList.remove('active');
            document.getElementById('content-current').classList.remove('active');
            document.getElementById('content-history').classList.remove('active');
            document.getElementById('tab-' + tab).classList.add('active');
            document.getElementById('content-' + tab).classList.add('active');
        }}
        
        // 이미지 모달 기능
        function showImageModal(imgSrc) {{
            var modal = document.getElementById('img-modal');
            var modalImg = document.getElementById('img-modal-img');
            modalImg.src = imgSrc;
            modal.classList.add('active');
            modal.style.display = 'flex';
        }}
        
        function closeImageModal() {{
            var modal = document.getElementById('img-modal');
            modal.classList.remove('active');
            modal.style.display = 'none';
            document.getElementById('img-modal-img').src = '';
        }}
        
        // 페이지 로드 시 이벤트 바인딩
        document.addEventListener('DOMContentLoaded', function() {{
            // 스크린샷 이미지 클릭 이벤트
            document.querySelectorAll('.screenshot img').forEach(function(img) {{
                img.style.cursor = 'pointer';
                img.addEventListener('click', function(e) {{
                    e.preventDefault();
                    showImageModal(this.src);
                }});
            }});
            
            // 모달 배경 클릭 시 닫기
            document.getElementById('img-modal').addEventListener('click', function(e) {{
                if (e.target === this) {{
                    closeImageModal();
                }}
            }});
            
            // ESC 키로 모달 닫기
            document.addEventListener('keydown', function(e) {{
                if (e.key === 'Escape') {{
                    closeImageModal();
                }}
            }});
        }});
        </script>
    </head>
    <body>
        <h1 style='margin-bottom: 32px;'>KOS 자동테스트 리포트</h1>
        <div class='tab-wrap' style='max-width:900px; margin:0 auto 32px auto;'>
            <button id='tab-current' class='tab-btn active' onclick="showTab('current')">현재 결과</button>
            <button id='tab-history' class='tab-btn' onclick="showTab('history')">이전 결과</button>
        </div>
        <div id='content-current' class='tab-content active'>
            <div class='summary-section section' style='margin-bottom:40px; padding-top:32px; padding-bottom:32px;'>
                <h2>테스트 요약</h2>
                <table class='summary-table' style='margin-left:auto; margin-right:auto;'>
                    <tr><td><b>수행 시점</b></td><td style='text-align:center;'>{now}</td></tr>
                    <tr><td colspan="2"><hr class='summary-hr'></td></tr>
                    <tr><td><b>테스트 환경</b></td><td style='text-align:center;'>{test_env}</td></tr>
                    <tr><td colspan="2"><hr class='summary-hr'></td></tr>
                    <tr><td><b>테스트 빌드</b></td><td style='text-align:center;'><a href='{build_number}' target='_blank'>{build_number[:30] + '...' + build_number[-20:] if len(build_number) > 55 else build_number}</a></td></tr>
                </table>
            </div>
            <div class='result-summary-outer'>
                <div class='result-summary-block'>
                    <div class='result-summary-title'>결과 요약</div>
                    <hr class='result-summary-hr'>
                    <div class='result-summary-row'>
                        <div class='result-summary-card status'>
                            {status_html}
                        </div>
                        <div class='result-summary-card all'>
                            <div class='result-summary-label all'>체크리스트</div>
                            <div class='result-summary-value all'>{len(test_results)}</div>
                        </div>
                        <div class='result-summary-card pass'>
                            <div class='result-summary-label pass'>Pass</div>
                            <div class='result-summary-value pass'>{sum(1 for r in test_results if r['value'] == 'Pass')}</div>
                        </div>
                        <div class='result-summary-card fail'>
                            <div class='result-summary-label fail'>Fail</div>
                            <div class='result-summary-value fail'>{sum(1 for r in test_results if r['value'] == 'Fail')}</div>
                        </div>
                        <div class='result-summary-card na'>
                            <div class='result-summary-label na'>N/A</div>
                            <div class='result-summary-value na'>{sum(1 for r in test_results if r['value'] == 'N/A')}</div>
                        </div>
                        <div class='result-summary-card skip'>
                            <div class='result-summary-label skip'>Skip</div>
                            <div class='result-summary-value skip'>{sum(1 for r in test_results if r['value'] == 'Skip')}</div>
                        </div>
                    </div>
                </div>
            </div>
            <div class='result-section section' style='margin-bottom:40px;'>
                <h2>테스트 결과</h2>
                <div class='result-table-wrap'>
                    <table style="table-layout:fixed; width:100%;">
                        <thead>
                            <tr>
                                <th style="width:40%; text-align:center;">체크포인트</th>
                                <th style="width:5%; text-align:center;">결과</th>
                                <th style="width:45%; text-align:center;">테스트 정보</th>
                                <th style="width:10%; text-align:center;">스크린샷</th>
                            </tr>
                        </thead>
                        <tbody>
                            {''.join([
                                f"<tr>"
                                f"<td style='min-width:250px; max-width:350px; text-align:center;'>{r['checklist']}</td>"
                                f"<td class='result {r['value'].lower()}'>{r['value']}</td>"
                                f"<td class='message'>{r['message']}</td>"
                                + ("<td class='screenshot'><a href='{0}' target='_blank'><img src='{0}' style='width:60px;max-height:40px;object-fit:contain;vertical-align:middle;border-radius:4px;'></a></td>".format(get_absolute_path(r['screenshot'])) if r.get('screenshot') else "<td class='screenshot'></td>")
                                + "</tr>"
                                for r in test_results
                            ])}
                        </tbody>
                    </table>
                </div>
            </div>
            <div class='section' style='max-width:900px; margin:0 auto 40px auto;'>
                <h2>테스트 영상</h2>
                {video_section_html}
            </div>
            <div class='section' style='max-width:900px; margin:0 auto 40px auto;'>
                <h2>로그</h2>
                <div style="font-family: 'Pretendard', Arial, sans-serif; white-space:pre-line; word-break:break-all;">
                {''.join([
                    l.replace('Pass', '<span style="color: #1976d2; font-weight: bold;">Pass</span>')
                     .replace('Fail', '<span style="color: #d32f2f; font-weight: bold;">Fail</span>') + '<br/>'
                    for l in logs
                    if '[전체 테스트 결과]' not in l
                    and 'run_kid_login_test 시작' not in l
                    and 'start_idx 설정:' not in l
                    and '[디버깅]' not in l
                ])}
                </div>
            </div>
        </div>
        <div id='content-history' class='tab-content'>
            <!--__HISTORY_HTML_PLACEHOLDER__-->
        </div>
        <!-- 이미지 모달 -->
        <div id="img-modal" style="display:none;">
            <img id="img-modal-img" src="" alt="screenshot" />
        </div>
    </body>
    </html>
    """
    with open(filename, "w", encoding="utf-8") as f:
        f.write(html)
        f.flush()
        os.fsync(f.fileno())  # 디스크에 flush 보장

    # 2차: 파일 목록을 다시 읽어와서 history_html 생성
    reports_dir = "reports"
    if os.path.exists(reports_dir):
        report_files = [f for f in os.listdir(reports_dir) if f.startswith('test_report_') and f.endswith('.html')]
    else:
        report_files = []
    current_report_file = os.path.basename(filename)
    if current_report_file not in report_files:
        report_files.append(current_report_file)
    parsed_reports = []
    for f in report_files:
        m = re.match(r'test_report_(\d{8})_(\d{6})_(.+)_(\d)\.html', f)
        if m:
            date, time, env_full, pass_ratio = m.groups()
            env_parts = env_full.split('_')
            if pass_ratio.endswith('%') and len(env_parts) > 1:
                env = '_'.join(env_parts[:-1])
            else:
                env = env_full
            date_fmt = f"{date[:4]}-{date[4:6]}-{date[6:]}"
            dt_str = f"{date_fmt} {time[:2]}:{time[2:4]}:{time[4:]}"
            parsed_reports.append({
                'file': f,
                'datetime': dt_str,
                'env': env,
                'pass_ratio': pass_ratio,
                'build': '-',
                'is_current': (f == current_report_file)
            })
        else:
            m_old = re.match(r'test_report_(\d{8})_(\d{6})_([^.]+)\.html', f)
            if m_old:
                date, time, env = m_old.groups()
                date_fmt = f"{date[:4]}-{date[4:6]}-{date[6:]}"
                dt_str = f"{date_fmt} {time[:2]}:{time[2:4]}:{time[4:]}"
                parsed_reports.append({
                    'file': f,
                    'datetime': dt_str,
                    'env': env,
                    'pass_ratio': '-',
                    'build': '-',
                    'is_current': (f == current_report_file)
                })
    parsed_reports.sort(key=lambda x: x['datetime'], reverse=True)
    report_rows = ''
    for r in parsed_reports:
        style = ' style="font-weight:bold;background:#e3f2fd;"' if r.get('is_current') else ''
        current_label = ' <span style="color:#1976d2;font-weight:bold;">(현재)</span>' if r.get('is_current') else ''
        if r['pass_ratio'] == '100%':
            ratio_html = f'<span style="color: #1976d2; font-weight: bold;">{r["pass_ratio"]}</span>'
        elif r['pass_ratio'] != '-':
            ratio_html = f'<span style="color: #d32f2f; font-weight: bold;">{r["pass_ratio"]}</span>'
        else:
            ratio_html = '-'
        report_rows += (
            f"<tr{style}>"
            f"<td style='text-align:center;'>{r['datetime']}{current_label}</td>"
            f"<td style='text-align:center;'>{r['env']}</td>"
            f"<td style='text-align:center;'>{ratio_html}</td>"
            f"<td style='text-align:center;'><a href='{r['file']}' target='_blank'>테스트 결과</a></td>"
            f"</tr>"
        )
    history_html = f"""
    <div class='section' style='max-width:900px; min-width:600px; margin:0 auto;'>
        <h2 style='margin-bottom:24px;'>이전 결과</h2>
        <table style="table-layout:fixed; width:100%;">
            <thead><tr>
                <th style='width:40%; text-align:center;'>수행 시점</th>
                <th style='width:20%; text-align:center;'>테스트 환경</th>
                <th style='width:20%; text-align:center;'>테스트 결과</th>
                <th style='width:20%; text-align:center;'>결과 리포트</th>
            </tr></thead>
            <tbody>{report_rows}</tbody>
        </table>
    </div>
    """

    # 3차: history_html을 포함해 최종 리포트 파일을 다시 저장
    html = html.replace("<!--__HISTORY_HTML_PLACEHOLDER__-->", history_html)
    with open(filename, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"리포트가 {filename}에 저장되었습니다.")

    return filename

if __name__ == "__main__":
    # 예시: test_results.json, logs.json 파일에서 데이터 불러오기
    with open("test_results.json", "r", encoding="utf-8") as f:
        test_results = json.load(f)
    with open("logs.json", "r", encoding="utf-8") as f:
        logs = json.load(f)
    save_report_html(test_results, logs, build_number=build_url, test_env=BUILD_ENV) 