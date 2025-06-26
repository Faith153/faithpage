import streamlit as st
import openai
import json
from datetime import datetime
import io

# 페이지 설정
st.set_page_config(
    page_title="FaithGPT-4.1",
    page_icon="🤖",
    layout="wide",
    menu_items={
        'Get Help': None,
        'Report a bug': None,
        'About': None
    }
)

# CSS 스타일링
st.markdown("""
<style>
    .main-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 20px;
    }
    
    .token-gauge {
        width: 200px;
        height: 20px;
        background-color: #f0f0f0;
        border-radius: 10px;
        overflow: hidden;
        position: relative;
    }
    
    .token-fill {
        height: 100%;
        transition: all 0.3s ease;
        border-radius: 10px;
    }
    
    .token-text {
        position: absolute;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        font-size: 12px;
        font-weight: bold;
        color: white;
        text-shadow: 1px 1px 1px rgba(0,0,0,0.5);
    }
    
    .chat-container {
        height: 400px;
        overflow-y: auto;
        border: 1px solid #ddd;
        border-radius: 10px;
        padding: 10px;
        margin-bottom: 20px;
        background-color: #fafafa;
    }
    
    .user-message {
        background-color: #e3f2fd;
        padding: 10px;
        border-radius: 10px;
        margin: 5px 0;
        text-align: right;
        color: #1565c0;
        font-weight: 500;
    }
    
    .assistant-message {
        background-color: #f3e5f5;
        padding: 10px;
        border-radius: 10px;
        margin: 5px 0;
        color: #4a148c;
        font-weight: 500;
    }
    
    .warning-message {
        color: #d32f2f;
        font-size: 12px;
        margin-top: 5px;
        font-weight: bold;
    }
    
    /* 다크모드 대응 */
    [data-theme="dark"] .chat-container {
        background-color: #262730;
        border-color: #464853;
    }
    
    [data-theme="dark"] .user-message {
        background-color: #1976d2;
        color: #ffffff;
    }
    
    [data-theme="dark"] .assistant-message {
        background-color: #7b1fa2;
        color: #ffffff;
    }
    
    [data-theme="dark"] .token-gauge {
        background-color: #464853;
    }
</style>
""", unsafe_allow_html=True)

# 토큰 계산 함수 (tiktoken 없이)
def count_tokens(text):
    """간단한 토큰 추정 (1토큰 ≈ 4자)"""
    # 한글은 더 많은 토큰을 사용하므로 보수적으로 계산
    korean_chars = len([c for c in text if ord(c) >= 0xAC00 and ord(c) <= 0xD7A3])
    other_chars = len(text) - korean_chars
    
    # 한글: 1자당 1토큰, 영문: 4자당 1토큰으로 보수적 계산
    estimated_tokens = korean_chars + (other_chars // 3)
    return max(estimated_tokens, len(text) // 4)  # 최소값 보장

# 사용자 코드 검증 및 정보 조회
def verify_user_code(code):
    """사용자 코드가 유효한지 Secrets에서 확인하고 정보 반환"""
    try:
        # 토큰 한도 정보에서 코드 존재 여부 확인
        faithgpt_codes = st.secrets["faithgpt_codes"]
        if code not in faithgpt_codes:
            return None
            
        # 사용자 정보도 Secrets에서 조회
        faithgpt_users = st.secrets["faithgpt_users"]
        return faithgpt_users.get(code, {"name": "사용자", "age": 0, "grade": "일반"})
    except Exception as e:
        return None

def get_user_token_limit(code):
    """사용자 코드별 토큰 제한 확인"""
    try:
        faithgpt_codes = st.secrets["faithgpt_codes"]
        return faithgpt_codes.get(code, 0)
    except:
        return 0

def check_token_usage(code, current_tokens):
    """토큰 사용량 체크"""
    limit = get_user_token_limit(code)
    if limit == -1:  # 무제한
        return True, "무제한"
    elif current_tokens >= limit:
        return False, f"한도 초과 ({current_tokens:,}/{limit:,})"
    else:
        return True, f"{current_tokens:,}/{limit:,}"

# 시스템 프롬프트 생성
def get_system_prompt(user_info, purpose, custom_age=None):
    base_prompt = """당신은 FaithGPT-4.1입니다. 기독교적 가치관을 바탕으로 한 AI 어시스턴트로서, 
    사랑과 진리, 지혜로 사용자를 도와드립니다."""
    
    if user_info["name"] == "주아":
        return f"""{base_prompt}
        
        사용자는 {user_info['age']}세 {user_info['grade']} 여학생 주아입니다.
        - 아이의 수준에 맞는 쉽고 친근한 언어를 사용하세요
        - 호기심을 자극하고 학습에 도움이 되는 방향으로 답변하세요
        - 항상 격려하고 칭찬하는 톤을 유지하세요
        - 기독교적 가치관(사랑, 용서, 섬김 등)을 자연스럽게 녹여주세요
        목적: {purpose}"""
        
    elif user_info["name"] == "주봄":
        return f"""{base_prompt}
        
        사용자는 {user_info['age']}세 {user_info['grade']} 여학생 주봄입니다.
        - 더욱 쉽고 간단한 언어를 사용하세요
        - 구체적인 예시와 비유를 많이 들어주세요
        - 재미있고 흥미로운 방식으로 설명해주세요
        - 작은 성취도 크게 격려해주세요
        - 기독교적 가치관을 동화나 이야기로 전달해주세요
        목적: {purpose}"""
        
    else:
        age_text = f"{custom_age}세" if custom_age else "성인"
        return f"""{base_prompt}
        
        사용자는 {age_text} {user_info['name']}입니다.
        - 정확하고 도움이 되는 정보를 제공하세요
        - 기독교적 관점에서 지혜로운 조언을 해주세요
        - 사랑과 진리의 균형을 맞춘 답변을 하세요
        목적: {purpose}"""

# 세션 상태 초기화
if "faithgpt_messages" not in st.session_state:
    st.session_state.faithgpt_messages = []
if "faithgpt_total_tokens" not in st.session_state:
    st.session_state.faithgpt_total_tokens = 0
if "faithgpt_user_code" not in st.session_state:
    st.session_state.faithgpt_user_code = ""

# 사이드바 설정
with st.sidebar:
    st.title("🤖 FaithGPT-4.1 설정")
    
    # 사용자 코드 입력
    user_code = st.text_input("사용자 코드 입력", 
                             value=st.session_state.faithgpt_user_code,
                             type="password")
    
    if user_code != st.session_state.faithgpt_user_code:
        st.session_state.faithgpt_user_code = user_code
        st.rerun()
    
    user_info = verify_user_code(user_code) if user_code else None
    
    if user_info:
        # 토큰 사용량 체크
        can_use, usage_status = check_token_usage(user_code, st.session_state.faithgpt_total_tokens)
        
        if can_use:
            st.success(f"✅ {user_info['name']}님 환영합니다!")
            st.info(f"토큰 사용량: {usage_status}")
            
            # 디버깅 정보 (관리자만)
            if user_code == "FAITH":
                with st.expander("🔧 디버깅 정보 (관리자용)"):
                    st.write("사용자 정보:", user_info)
                    st.write("토큰 한도:", get_user_token_limit(user_code))
                    try:
                        st.write("Secrets 키 목록:", list(st.secrets.keys()))
                        if "faithgpt" in st.secrets:
                            st.write("FaithGPT 설정:", "API_KEY" in st.secrets["faithgpt"])
                    except:
                        st.write("Secrets 접근 오류")
        else:
            st.error(f"❌ {user_info['name']}님, 토큰 한도를 초과했습니다.")
            st.error(f"사용량: {usage_status}")
            st.info("새로운 대화 시작으로 토큰을 초기화하거나, 관리자에게 문의하세요.")
            
            # 토큰 초과 시에도 새 대화 시작은 가능하도록
            if st.button("🔄 토큰 초기화 (새 대화 시작)", key="reset_tokens"):
                st.session_state.faithgpt_messages = []
                st.session_state.faithgpt_total_tokens = 0
                st.success("토큰이 초기화되었습니다!")
                st.rerun()
            st.stop()
        
        # 사용자 설정
        st.subheader("👤 사용자 설정")
        
        if user_info["name"] in ["주아", "주봄"]:
            # 아이들은 자동 설정
            st.info(f"자동 설정: {user_info['grade']} {user_info['name']}({user_info['age']}세)")
            selected_user = user_info["name"]
            custom_age = None
        else:
            # 일반 사용자는 선택 가능
            user_options = ["체험", "직접 입력"]
            selected_user = st.radio("사용자 유형", user_options)
            
            if selected_user == "직접 입력":
                custom_age = st.number_input("나이 입력", min_value=1, max_value=100, value=25)
            else:
                custom_age = None
        
        # 목적 선택
        st.subheader("🎯 사용 목적")
        
        if user_info["name"] in ["주아", "주봄"]:
            purpose_options = [
                "숙제 도움", "학습 질문", "창의적 글쓰기", "과학 탐구", 
                "성경 이야기", "도덕적 고민 상담", "재미있는 대화", "독서 감상"
            ]
        else:
            purpose_options = [
                "학습용", "업무 상담", "창작 도움", "문제 해결", 
                "성경 연구", "신앙 상담", "일반 대화", "전문 자료 분석",
                "교육 자료 제작", "프레젠테이션 준비"
            ]
        
        selected_purpose = st.selectbox("목적을 선택하세요", purpose_options)
        
        # API 키 확인
        try:
            faithgpt_api_key = st.secrets["faithgpt"]["API_KEY"]
            if faithgpt_api_key and faithgpt_api_key.startswith("sk-"):
                st.success("🔑 API 연결 성공")
            else:
                st.error("❌ FaithGPT API 키가 올바르지 않습니다")
                st.info("Secrets에서 [faithgpt] API_KEY를 확인해주세요")
                st.stop()
        except KeyError as e:
            st.error(f"❌ FaithGPT API 키가 설정되지 않았습니다: {str(e)}")
            st.info("App settings > Secrets에서 [faithgpt] 섹션과 API_KEY를 확인해주세요")
            st.stop()
        except Exception as e:
            st.error(f"❌ API 키 확인 중 오류: {str(e)}")
            st.stop()
            
    elif user_code:
        st.error("❌ 유효하지 않은 사용자 코드입니다")
        st.stop()
    else:
        st.info("👆 사용자 코드를 입력해주세요")
        st.stop()

# 메인 화면
col1, col2 = st.columns([3, 1])

with col1:
    st.title("🤖 FaithGPT-4.1")

with col2:
    # 토큰 게이지 - 개인 한도 기준으로 표시
    user_limit = get_user_token_limit(user_code)
    current_tokens = st.session_state.faithgpt_total_tokens
    
    if user_limit == -1:  # 무제한 사용자
        MAX_TOKENS = 100000  # 맥락 유지 한도
        token_percentage = min(current_tokens / MAX_TOKENS * 100, 100)
        limit_text = f"{current_tokens:,}/무제한"
    else:  # 제한된 사용자
        MAX_TOKENS = user_limit
        token_percentage = min(current_tokens / MAX_TOKENS * 100, 100)
        limit_text = f"{current_tokens:,}/{MAX_TOKENS:,}"
    
    # 게이지 색상 결정
    if token_percentage >= 90:
        gauge_color = "#f44336"  # 빨간색
    elif token_percentage >= 70:
        gauge_color = "#ff9800"  # 주황색
    else:
        gauge_color = "#4caf50"  # 초록색
    
    st.markdown(f"""
    <div class="token-gauge">
        <div class="token-fill" style="width: {token_percentage}%; background-color: {gauge_color};">
            <div class="token-text">{limit_text}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # 경고 메시지
    if user_limit == -1 and token_percentage >= 90:
        st.markdown('<div class="warning-message">⚠️ 초기 대화를 잊을 수 있으니 정리 후 새롭게 대화 시작하는 것을 추천드립니다</div>', unsafe_allow_html=True)
    elif user_limit != -1 and token_percentage >= 90:
        st.markdown('<div class="warning-message">⚠️ 토큰 한도에 거의 도달했습니다</div>', unsafe_allow_html=True)

# 대화 기록 표시
chat_container = st.container()
with chat_container:
    if st.session_state.faithgpt_messages:
        chat_html = '<div class="chat-container">'
        for message in st.session_state.faithgpt_messages:
            if message["role"] == "user":
                chat_html += f'<div class="user-message"><strong>👤 나:</strong> {message["content"]}</div>'
            else:
                chat_html += f'<div class="assistant-message"><strong>🤖 FaithGPT-4.1:</strong> {message["content"]}</div>'
        chat_html += '</div>'
        st.markdown(chat_html, unsafe_allow_html=True)
    else:
        st.info("대화를 시작해보세요! 😊")

# 사용자 입력 및 전송 처리
with st.form(key="message_form"):
    user_input = st.text_area("메시지를 입력하세요:", height=100, key="user_input", 
                             help="Ctrl+Enter 또는 전송 버튼으로 메시지를 보낼 수 있습니다")
    send_message = st.form_submit_button("전송", type="primary")

if send_message and user_input.strip():
    # 토큰 한도 체크
    can_use, _ = check_token_usage(user_code, st.session_state.faithgpt_total_tokens)
    if not can_use:
        st.error("토큰 한도를 초과했습니다. 새로운 대화를 시작해주세요.")
        st.stop()
    
    # 사용자 메시지 추가
    st.session_state.faithgpt_messages.append({"role": "user", "content": user_input})
    
    # 토큰 계산
    input_tokens = count_tokens(user_input)
    
    # 예상 응답 토큰까지 고려한 사전 체크 (체험 사용자만)
    estimated_response_tokens = min(input_tokens * 2, 2000)  # 대략적 추정
    user_limit = get_user_token_limit(user_code)
    
    if user_limit != -1:  # 제한된 사용자
        if st.session_state.faithgpt_total_tokens + input_tokens + estimated_response_tokens > user_limit:
            st.warning("응답을 생성하면 토큰 한도를 초과할 수 있습니다. 그래도 진행하시겠습니까?")
            if not st.button("계속 진행", key="continue_anyway"):
                # 마지막 메시지 제거하고 중단
                st.session_state.faithgpt_messages.pop()
                st.stop()
    
    st.session_state.faithgpt_total_tokens += input_tokens
    
    # OpenAI API 호출
    try:
        client = openai.OpenAI(api_key=faithgpt_api_key)
        
        # 시스템 프롬프트 생성
        system_prompt = get_system_prompt(user_info, selected_purpose, custom_age)
        
        # 메시지 구성
        messages = [{"role": "system", "content": system_prompt}]
        messages.extend(st.session_state.faithgpt_messages)
        
        # API 호출
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            max_tokens=2000,
            temperature=0.7
        )
        
        assistant_message = response.choices[0].message.content
        
        # 응답 메시지 추가
        st.session_state.faithgpt_messages.append({"role": "assistant", "content": assistant_message})
        
        # 응답 토큰 계산
        response_tokens = count_tokens(assistant_message)
        st.session_state.faithgpt_total_tokens += response_tokens
        
        st.rerun()
        
    except Exception as e:
        st.error(f"오류가 발생했습니다: {str(e)}")

# 하단 버튼들
st.markdown("---")
col1, col2, col3 = st.columns(3)

with col1:
    if st.button("📄 전체 대화 TXT 다운로드"):
        if st.session_state.faithgpt_messages:
            chat_text = f"FaithGPT-4.1 대화 기록\n생성일: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            chat_text += f"사용자: {user_info['name']}\n목적: {selected_purpose}\n\n"
            chat_text += "=" * 50 + "\n\n"
            
            for i, message in enumerate(st.session_state.faithgpt_messages, 1):
                role = "👤 나" if message["role"] == "user" else "🤖 FaithGPT-4.1"
                chat_text += f"[{i}] {role}: {message['content']}\n\n"
            
            st.download_button(
                label="다운로드",
                data=chat_text,
                file_name=f"FaithGPT_chat_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                mime="text/plain"
            )
        else:
            st.info("대화 기록이 없습니다.")

with col2:
    if st.button("📋 전체 대화 요약 다운로드"):
        if st.session_state.faithgpt_messages:
            try:
                # 대화 요약 생성
                client = openai.OpenAI(api_key=faithgpt_api_key)
                
                full_conversation = ""
                for message in st.session_state.faithgpt_messages:
                    role = "사용자" if message["role"] == "user" else "FaithGPT-4.1"
                    full_conversation += f"{role}: {message['content']}\n\n"
                
                summary_response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": "다음 대화를 핵심 내용 중심으로 요약해주세요. 주요 질문과 답변, 중요한 정보를 포함해주세요."},
                        {"role": "user", "content": full_conversation}
                    ],
                    max_tokens=1000
                )
                
                summary = summary_response.choices[0].message.content
                
                summary_text = f"FaithGPT-4.1 대화 요약\n생성일: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                summary_text += f"사용자: {user_info['name']}\n목적: {selected_purpose}\n"
                summary_text += f"총 대화 수: {len(st.session_state.faithgpt_messages)}개\n\n"
                summary_text += "=" * 50 + "\n\n"
                summary_text += summary
                
                st.download_button(
                    label="요약 다운로드",
                    data=summary_text,
                    file_name=f"FaithGPT_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                    mime="text/plain"
                )
                
            except Exception as e:
                st.error(f"요약 생성 중 오류가 발생했습니다: {str(e)}")
        else:
            st.info("요약할 대화가 없습니다.")

with col3:
    if st.button("🔄 새로운 대화 시작"):
        st.session_state.faithgpt_messages = []
        st.session_state.faithgpt_total_tokens = 0
        st.success("새로운 대화가 시작되었습니다!")
        st.rerun()

# 푸터
st.markdown("---")
st.markdown("**🤖 FaithGPT-4.1** - 믿음님의 지인들을 위한 ChatGPT")
