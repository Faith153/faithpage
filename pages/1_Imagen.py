import streamlit as st
from openai import OpenAI
import re
import requests
import time
import os
import json

# API KEY from Streamlit TOML
API_KEY = st.secrets['openai']['API_KEY']
client = OpenAI(api_key=API_KEY)

# 누적된 이미지를 저장할 리스트
if "all_images" not in st.session_state:
    st.session_state["all_images"] = []

# -----------------------------------------------------------
# 사이드바 항상 열림 (UI/UX 개선용)
st.markdown("""
    <style>
    [data-testid="stSidebar"][aria-expanded="false"] {
        min-width: 340px;
        max-width: 340px;
        width: 340px;
        transition: all 0.3s;
    }
    </style>
    """, unsafe_allow_html=True)

# ===========================================================
# ========== 이용자 코드 입력 및 30분 제한 구현 =============

# 1. 실패 로그 기록(쿠키/DB 대신 파일캐시 활용)
def fail_log_path():
    # 유저 IP + 오늘 날짜로 파일명 구성(봇방지용)
    if hasattr(st.runtime, 'scriptrunner'):
        try:
            ip = st.runtime.scriptrunner.get_script_run_ctx().client_ip
        except:
            ip = "default"
    else:
        ip = "default"
    now_day = time.strftime("%Y%m%d")
    return f".failcount_{ip}_{now_day}.json"

def get_fail_info():
    path = fail_log_path()
    if os.path.exists(path):
        with open(path, "r") as f:
            try:
                obj = json.load(f)
                return obj.get("fail_count", 0), obj.get("fail_time", 0)
            except:
                return 0, 0
    return 0, 0

def set_fail_info(fail_count, fail_time):
    path = fail_log_path()
    with open(path, "w") as f:
        json.dump({"fail_count": fail_count, "fail_time": fail_time}, f)
        
# 2. 현재 실패 정보 확인
fail_count, fail_time = get_fail_info()
blocked = False
block_seconds = 30 * 60  # 30분

if fail_count >= 5:
    # 마지막 실패 이후 30분 경과 체크
    now = time.time()
    if now - fail_time < block_seconds:
        blocked = True
        left_min = int((block_seconds - (now - fail_time)) // 60) + 1
        st.sidebar.error(f"5회 이상 오류로 30분간 입력 불가. ({left_min}분 후 재시도)")
    else:
        # 제한 해제
        set_fail_info(0, 0)
        fail_count, fail_time = 0, 0
        blocked = False

# 3. 사이드바 코드 입력(비활성화/활성화)
user_code = st.sidebar.text_input("이용자 코드 입력", max_chars=16, disabled=blocked, type="password")

# 4. 코드별 한도(secrets.toml에서 바로!)
user_limits = st.secrets["user_codes"]                   # secrets.toml의 [user_codes] 전체 딕셔너리
limit = int(user_limits.get(user_code, 0))               # user_code 키로 한도를 꺼내 정수로 변환, 없으면 0


# 5. 세션 사용량 관리(코드 바뀌면 초기화)
if "used_count" not in st.session_state or st.session_state.get("last_user_code") != user_code:
    st.session_state["used_count"] = 0
    st.session_state["last_user_code"] = user_code

# 6. 한도 체크 및 실패 처리
if user_code:
    # (limit이 0보다 크거나 -1인 경우만 유효 코드로 간주)
    if limit > 0 or limit == -1:
        # 성공 시 실패카운트/파일 초기화
        set_fail_info(0, 0)                         # (파일에 남아 있던 fail_count, fail_time을 0으로 초기화)
        fail_count = 0                              # (로컬 변수도 초기화)
        if limit > 0:
            st.sidebar.info(f"사용 가능 이미지: {limit - st.session_state['used_count']}장 남음")
        else:
            st.sidebar.info("무제한 코드")          # (limit == -1일 때)
    else:
        # 실패 카운트 증가, 5회시 시간 저장
        fail_count += 1                            # (틀릴 때마다 1씩 증가)
        # 5회 차단 시점에만 시간 갱신
        set_fail_info(fail_count,
                      int(time.time()) if fail_count >= 5 else fail_time)
        if fail_count >= 5:
            st.sidebar.error("5회 이상 오류로 30분간 입력이 차단됩니다.")
        else:
            st.sidebar.warning(f"유효하지 않은 코드입니다! (실패 {fail_count}회)")
        limit = 0
else:
    limit = 0
    
#================================================
# 사이드바 이미지 생성 옵션
st.sidebar.title("AI 이미지 생성 옵션")
sizes = [
    ("1:1비율(1024x1024)", "1024x1024"),
    ("세로형(1024x1792)", "1024x1792"),
    ("가로형(1792x1024)", "1792x1024")
]
selected_size_label = st.sidebar.selectbox("이미지 비율/사이즈", [x[0] for x in sizes])
selected_size = [x[1] for x in sizes if x[0] == selected_size_label][0]

styles = [
    "자동(Auto, best fit)", "사진(Real photo)", "디즈니 스타일(Disney style cartoon)",
    "픽사 3D 스타일(Pixar 3D animation)", "드림웍스 스타일(Dreamworks style)",
    "일본풍 애니메이션(Japanese anime)", "수채화(Watercolor painting)", "유화(Oil painting)",
    "연필 드로잉(Pencil sketch)", "픽토그램(Flat pictogram icon)", "미니멀리즘(Minimalist flat design)",
    "아트포스터(Vintage art poster)", "반 고흐(Vincent van Gogh style)", "에드워드 호퍼(Edward Hopper style)",
    "앤디 워홀(Andy Warhol pop art)", "구스타프 클림트(Gustav Klimt style)", "무하(Alphonse Mucha Art Nouveau)",
    "헤이즐 블룸(Hazel Bloom digital art)"
]
selected_style = st.sidebar.selectbox("스타일/작가 레퍼런스", styles, index=0)

# 3. 메인 - 프롬프트 입력 등
st.title("AI 이미지 생성기")
st.write("한글로 원하는 그림 설명하면 프롬프트로 완성해주고, 최종 이미지 생성")

user_kor_prompt = st.text_area("원하는 이미지를 한글로 설명해 주세요.", height=80)
st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)


# ─────────────────────────────────────────────
# (1) 1차 프롬프트 생성 버튼  +  (2) 즉시 1장 생성 버튼
#    두 개를 같은 줄(col) 에 배치
# ─────────────────────────────────────────────
col_gen, col_quick = st.columns([1,1])              # 버튼 2개 나란히

if col_gen.button("1차 프롬프트 자동 생성"):
    if not user_kor_prompt.strip():
        st.warning("먼저 한글로 원하는 그림 설명을 입력하세요!")
    else:
        with st.spinner("AI가 디테일하고 풍성한 프롬프트를 만드는 중입니다..."):
            gpt_prompt = (
                f"""당신은 AI 이미지 프롬프트 엔지니어입니다.
                아래는 사용자의 간단한 한글 설명입니다.
                ---
                {user_kor_prompt} {f'({selected_style})' if selected_style != '자동(Auto, best fit)' else ''}
                ---
                1. 이 내용을 바탕으로 색상, 질감, 배경, 분위기, 조명, 카메라 각도, 디테일, 동작, 감정 등 시각적 정보까지 추가해 풍성한 한글 프롬프트를 완성해줘.
                2. 두 번째로, 이 한글 프롬프트를 AI가 잘 이해할 수 있는 영어 프롬프트로 자연스럽게 번역해줘. 
                 - 영어 프롬프트에는 ‘edge-to-edge composition, no letterboxing’ 같은 여백 제거 지시어를 반드시 포함해줘. 
                3. 각각은 아래 양식으로, 반드시 영어 프롬프트는 코드블럭으로 출력해.
                4. 그 뒤에 영어 프롬프트를 확인할 수 있도록 플레인 텍스트로 한국어 설명을 플레인텍스트로 자세히 설명해줘.
                [English Prompt]
                ```
                (여기에 풍성한 영어 프롬프트)
                ```
                [프롬프트 설명]
                1. 여기에 영문 프롬프트를 플레인 텍스트로 자세하게 설명.
                2. 영문 프롬프트 한국어 전문 번역 후 프롬프트 의도 설명
                """
            )
            response = client.chat.completions.create(
                model="gpt-4.1-mini",
                messages=[{"role": "user", "content": gpt_prompt}],
                temperature=0.6
            )
            ai_response = response.choices[0].message.content.strip()
            import re
            eng_block = ""
            eng_match = re.search(r"\[English Prompt\]\s*```([\s\S]+?)```", ai_response)
            desc_match = re.search(r"\[프롬프트 설명\]\s*([\s\S]+)", ai_response)
            if eng_match:
                eng_block = eng_match.group(1).strip()
            if desc_match:
                kor_desc = desc_match.group(1).strip()
            else:
                kor_desc = ""
            # 세션 상태에 저장
            st.session_state['eng_prompt'] = eng_block
            st.session_state['kor_desc'] = kor_desc

            # ─── 프롬프트 해설(kor_desc) 요약(매번 갱신) ───
            resp = client.chat.completions.create(
                model="gpt-4.1-mini",
                messages=[{
                    "role":"user",
                    "content":f"아래 한글 해설을 10자 이내로 요약해줘:\n{kor_desc}"
                }],
                temperature=0.2
            )
            st.session_state['summary'] = resp.choices[0].message.content.strip()

# ② 즉시 이미지 생성(1장)
if col_quick.button("즉시 이미지 생성(1장)"):
    if not user_kor_prompt.strip():
        st.warning("먼저 한글 설명을 입력하세요!")
    else:
        # 프롬프트가 이미 만들어졌는지 확인
        if 'eng_prompt' not in st.session_state:
            st.warning("먼저 왼쪽 버튼으로 프롬프트를 생성해 주세요!")
        else:
            with st.spinner("프롬프트 기반으로 이미지 1장 바로 생성 중..."):
                try:
                    resp = client.images.generate(
                        prompt=st.session_state['eng_prompt'],
                        model="dall-e-3",
                        n=1,
                        size=selected_size
                    )
                    url = resp.data[0].url
                    # 누적 리스트에 저장
                    st.session_state["all_images"].append({
                        "url": url,
                        "caption": st.session_state.get("summary", "")
                    })
                    # 사용 횟수 차감
                    if limit > 0:
                        st.session_state["used_count"] += 1
                except Exception as e:
                    st.error(f"이미지 즉시 생성 오류: {e}")

# 2차: 프롬프트 결과/수정/리프롬프트
if st.session_state.get('eng_prompt'):
    st.markdown("**[자동 생성된 영어 프롬프트]**")
    st.code(st.session_state['eng_prompt'], language='text')
    st.markdown("**[프롬프트 한국어 설명 및 해석]**")
    st.info(st.session_state.get('kor_desc', ''))

    # 프롬프트 해설/의도(한국어) 직접 보완 입력
    kor_prompt_update = st.text_area(
        "의도, 세부 묘사, 추가 요청사항 등 원하는 내용을 기록해두세요.",
        value=st.session_state.get('kor_desc', ''),
        height=100
    )

    # 리프롬프트(수정한 한글로 다시 영어 프롬프트)
    if st.button("리프롬프트-프롬프트를 수정합니다"):
        with st.spinner("수정된 내용을 반영해서 프롬프트 재작업 중..."):
            gpt_re_prompt = (
                f"""아래 한글 프롬프트를 더 디테일하게 보완해 AI가 잘 이해할 수 있는 영어 프롬프트로 자연스럽게 번역해줘.
                색감, 분위기, 질감, 동작, 감정, 세부 연출 등 시각적 디테일을 추가하고,
                선택한 스타일 레퍼런스(화풍/작가)도 자연스럽게 포함해줘.
                반드시 코드블럭(플레인텍스트)로 출력해.
                ```
                {kor_prompt_update}
                ```
                """
            )
            re_response = client.chat.completions.create(
                model="gpt-4.1-mini",
                messages=[{"role": "user", "content": gpt_re_prompt}],
                temperature=0.6  # 창의성 설정
            )
            re_eng_match = re.search(r"```([\s\S]+?)```", re_response.choices[0].message.content)
            if re_eng_match:
                st.session_state['eng_prompt'] = re_eng_match.group(1).strip()
            st.session_state['kor_desc'] = kor_prompt_update

# ======= 이미지 생성 버튼(한도체크) =======
#  이미지 생성 개수 선택 (메인에서 결정)
num_images = st.radio(
    "이미지 생성 개수",
    [1, 2, 3, 4],
    index=0,
    horizontal=True
    )
if st.button("이미지 생성"):
    # ---- 한도 체크 ----
    if limit == 0:
        st.error("등록되지 않은 이용자 코드입니다!")
    elif limit > 0 and st.session_state["used_count"] + num_images > limit:
        st.error(f"생성 가능 횟수({limit}장)를 모두 사용하셨습니다.")
    else:
        with st.spinner("이미지를 생성 중입니다..."):
            try:
                for _ in range(num_images):   # num_images만큼 반복 호출
                    resp = client.images.generate(
                        prompt=st.session_state.get('eng_prompt', user_kor_prompt),
                        model="dall-e-3",
                        n=1,                     # ← 반드시 1로 고정
                        size=selected_size
                    )
                    url = resp.data[0].url
                    # 세션 리스트에 누적 저장 (url + 최신 summary)
                    st.session_state["all_images"].append({
                        "url": url,
                        "caption": st.session_state["summary"]
                    })
                    
                # ---- 사용횟수 업데이트 ----
                if limit > 0:
                    st.session_state["used_count"] += num_images
                    st.success(f"총 {st.session_state['used_count']} / {limit}장 사용")
            except Exception as e:
                st.error(f"이미지 생성 중 오류가 발생했습니다: {e}")

# ────────── 누적된 이미지 모두 그리드로 표시 ──────────
if st.session_state["all_images"]:
    st.markdown("## 생성된 이미지")
    imgs = st.session_state["all_images"]
    n = len(imgs)
    # 1장: 1열, 2~3장: n열, 4장 이상: 2열
    cols_per_row = 1 if n==1 else (n if n<=3 else 2)
    for i in range(0, n, cols_per_row):
        row = st.columns(cols_per_row)
        for j, col in enumerate(row):
                idx = i + j
                if idx < n:
                    item = imgs[idx]
                    col.image(
                        item["url"],
                        caption=f"이미지{idx+1} : {item['caption']}",
                        use_container_width=True
                    )
                    # ─── img_data 정의 후 다운로드 버튼 ───
                    img_data = requests.get(item["url"]).content
                    col.download_button(
                        label=f"이미지{idx+1} 다운로드",
                        data=img_data,
                        file_name=f"ai_image_{idx+1}.png",
                        mime="image/png",
                        key=f"dl_{idx}"
                    )
