import streamlit as st
import json
import hashlib
import os
from datetime import datetime, timedelta
from cryptography.fernet import Fernet
import pandas as pd

# 페이지 설정
st.set_page_config(
    page_title="말씀동행 - 성경읽기 현황판",
    page_icon="📖",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# CSS 스타일링
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #1e3a8a 0%, #3b82f6 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
    }
    
    .stat-card {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 4px solid #d97706;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin-bottom: 1rem;
    }
    
    .group-header {
        background: linear-gradient(90deg, #1e40af 0%, #3b82f6 100%);
        color: white;
        padding: 1rem;
        border-radius: 8px;
        margin-bottom: 1rem;
    }
    
    .bible-book {
        display: inline-block;
        margin: 2px;
        padding: 4px 8px;
        border-radius: 15px;
        font-size: 0.8rem;
        font-weight: bold;
        color: white;
        min-width: 60px;
        text-align: center;
    }
    
    .book-completed {
        background: linear-gradient(45deg, #10b981, #059669);
        box-shadow: 0 2px 4px rgba(16,185,129,0.3);
    }
    
    .book-partial {
        background: linear-gradient(45deg, #f59e0b, #d97706);
        box-shadow: 0 2px 4px rgba(245,158,11,0.3);
    }
    
    .book-unread {
        background: linear-gradient(45deg, #6b7280, #4b5563);
        opacity: 0.6;
    }
    
    .testament-section {
        background: #f8fafc;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
        border-left: 4px solid #3b82f6;
    }
    
    .chapter-grid {
        display: flex;
        flex-wrap: wrap;
        gap: 2px;
        margin: 0.5rem 0;
    }
    
    .chapter-progress {
        width: 24px;
        height: 24px;
        border-radius: 4px;
        margin: 1px;
        text-align: center;
        font-size: 0.7rem;
        color: white;
        line-height: 24px;
        font-weight: bold;
    }
    
    .chapter-read {
        background: #10b981;
        box-shadow: 0 1px 3px rgba(16,185,129,0.3);
    }
    
    .chapter-unread {
        background: #e5e7eb;
        color: #6b7280;
        border: 1px solid #d1d5db;
    }
    
    .progress-bar-container {
        background: #f3f4f6;
        border-radius: 10px;
        height: 24px;
        overflow: hidden;
        margin: 0.5rem 0;
        border: 1px solid #e5e7eb;
    }
    
    .progress-bar-fill {
        height: 100%;
        background: linear-gradient(90deg, #10b981, #059669);
        transition: width 0.3s ease;
        display: flex;
        align-items: center;
        justify-content: center;
        color: white;
        font-weight: bold;
        font-size: 0.8rem;
    }
    
    .book-progress-item {
        background: rgba(248, 250, 252, 0.7);
        border: 1px solid rgba(226, 232, 240, 0.5);
        border-radius: 12px;
        padding: 1.2rem;
        margin: 0.8rem 0;
        backdrop-filter: blur(10px);
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
        transition: all 0.3s ease;
    }
    
    .book-progress-item:hover {
        background: rgba(248, 250, 252, 0.9);
        box-shadow: 0 6px 12px rgba(0, 0, 0, 0.1);
        transform: translateY(-2px);
    }
    
    .book-title {
        font-weight: 600;
        color: #1e40af;
        margin-bottom: 0.8rem;
        display: flex;
        justify-content: space-between;
        align-items: center;
        font-size: 1.1rem;
    }
    
    /* 다크테마 호환성을 위한 테이블 스타일 */
    .dataframe {
        background-color: white !important;
        color: #1f2937 !important;
    }
    
    .dataframe th {
        background-color: #f8fafc !important;
        color: #374151 !important;
        font-weight: 600 !important;
        border-bottom: 2px solid #e5e7eb !important;
    }
    
    .dataframe td {
        background-color: white !important;
        color: #1f2937 !important;
        border-bottom: 1px solid #f3f4f6 !important;
    }
    
    .dataframe tr:hover td {
        background-color: #f9fafb !important;
    }
    
    /* 순위 강조 스타일 */
    .dataframe tr:nth-child(1) td {
        background-color: #fef3c7 !important;
        font-weight: 600 !important;
    }
    
    .dataframe tr:nth-child(2) td {
        background-color: #fef3c7 !important;
        font-weight: 500 !important;
    }
    
    .dataframe tr:nth-child(3) td {
        background-color: #fef3c7 !important;
        font-weight: 500 !important;
    }
    
    .reading-goal-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 10px;
        margin-bottom: 1rem;
    }
    
    .admin-section {
        background: #fef3c7;
        border: 2px solid #f59e0b;
        border-radius: 8px;
        padding: 1rem;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# 성경 구조 정의
BIBLE_STRUCTURE = {
    "구약": {
        "모세오경": ["창세기", "출애굽기", "레위기", "민수기", "신명기"],
        "역사서": ["여호수아", "사사기", "룻기", "사무엘상", "사무엘하", "열왕기상", "열왕기하", 
                  "역대상", "역대하", "에스라", "느헤미야", "에스더"],
        "시가서": ["욥기", "시편", "잠언", "전도서", "아가"],
        "대선지서": ["이사야", "예레미야", "예레미야애가", "에스겔", "다니엘"],
        "소선지서": ["호세아", "요엘", "아모스", "오바댜", "요나", "미가", "나훔", "하박국", 
                    "스바냐", "학개", "스가랴", "말라기"]
    },
    "신약": {
        "복음서": ["마태복음", "마가복음", "누가복음", "요한복음"],
        "역사서": ["사도행전"],
        "바울서신": ["로마서", "고린도전서", "고린도후서", "갈라디아서", "에베소서", 
                   "빌립보서", "골로새서", "데살로니가전서", "데살로니가후서", 
                   "디모데전서", "디모데후서", "디도서", "빌레몬서"],
        "일반서신": ["히브리서", "야고보서", "베드로전서", "베드로후서", 
                    "요한일서", "요한이서", "요한삼서", "유다서"],
        "예언서": ["요한계시록"]
    }
}

# 각 성경 권의 장 수
BIBLE_CHAPTERS = {
    "창세기": 50, "출애굽기": 40, "레위기": 27, "민수기": 36, "신명기": 34,
    "여호수아": 24, "사사기": 21, "룻기": 4, "사무엘상": 31, "사무엘하": 24,
    "열왕기상": 22, "열왕기하": 25, "역대상": 29, "역대하": 36, "에스라": 10,
    "느헤미야": 13, "에스더": 10, "욥기": 42, "시편": 150, "잠언": 31,
    "전도서": 12, "아가": 8, "이사야": 66, "예레미야": 52, "예레미야애가": 5,
    "에스겔": 48, "다니엘": 12, "호세아": 14, "요엘": 3, "아모스": 9,
    "오바댜": 1, "요나": 4, "미가": 7, "나훔": 3, "하박국": 3,
    "스바냐": 3, "학개": 2, "스가랴": 14, "말라기": 4,
    "마태복음": 28, "마가복음": 16, "누가복음": 24, "요한복음": 21,
    "사도행전": 28, "로마서": 16, "고린도전서": 16, "고린도후서": 13,
    "갈라디아서": 6, "에베소서": 6, "빌립보서": 4, "골로새서": 4,
    "데살로니가전서": 5, "데살로니가후서": 3, "디모데전서": 6, "디모데후서": 4,
    "디도서": 3, "빌레몬서": 1, "히브리서": 13, "야고보서": 5,
    "베드로전서": 5, "베드로후서": 3, "요한일서": 5, "요한이서": 1,
    "요한삼서": 1, "유다서": 1, "요한계시록": 22
}

# 모든 성경 권명 리스트
ALL_BOOKS = []
for testament in BIBLE_STRUCTURE.values():
    for category in testament.values():
        ALL_BOOKS.extend(category)

# 암호화 키 생성/로드
def get_encryption_key():
    key_file = "encryption.key"
    if not os.path.exists(key_file):
        key = Fernet.generate_key()
        with open(key_file, "wb") as f:
            f.write(key)
    else:
        with open(key_file, "rb") as f:
            key = f.read()
    return key

# 데이터 암호화/복호화
def encrypt_data(data, key):
    fernet = Fernet(key)
    json_data = json.dumps(data, ensure_ascii=False)
    encrypted_data = fernet.encrypt(json_data.encode())
    return encrypted_data

def decrypt_data(encrypted_data, key):
    try:
        fernet = Fernet(key)
        decrypted_data = fernet.decrypt(encrypted_data)
        return json.loads(decrypted_data.decode())
    except:
        return {}

# 데이터 파일 경로
DATA_FILE = "bible_tracker_data.encrypted"
KEY = get_encryption_key()

# 데이터 로드 및 마이그레이션
def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "rb") as f:
            encrypted_data = f.read()
        data = decrypt_data(encrypted_data, KEY)
        
        # 데이터 구조 마이그레이션
        data = migrate_data_structure(data)
        return data
    return {
        "users": {},
        "groups": {},
        "reading_records": {}
    }

def migrate_data_structure(data):
    """기존 데이터를 새로운 구조로 마이그레이션"""
    
    # 기본 키가 없는 경우 추가
    if "reading_records" not in data:
        data["reading_records"] = {}
    
    # 기존 checkins 데이터가 있으면 reading_records로 변환
    if "checkins" in data:
        for user_id, user_checkins in data["checkins"].items():
            if user_id not in data["reading_records"]:
                data["reading_records"][user_id] = {}
            
            for group_code, group_checkins in user_checkins.items():
                if group_code not in data["reading_records"][user_id]:
                    data["reading_records"][user_id][group_code] = {}
                
                # 기존 단순 체크인을 읽기 기록으로 변환
                for date, checkin_info in group_checkins.items():
                    if checkin_info.get("checked", False):
                        data["reading_records"][user_id][group_code][date] = [{
                            "book": "창세기",
                            "chapters": [1]
                        }]
        
        # 기존 checkins 데이터 제거
        del data["checkins"]
    
    # 그룹에 reading_goal이 없으면 기본값 추가
    for group_code, group_info in data.get("groups", {}).items():
        if "reading_goal" not in group_info:
            group_info["reading_goal"] = {
                "type": "전체",
                "books": ALL_BOOKS,
                "duration_days": 365,
                "start_date": group_info.get("start_date", datetime.now().isoformat()[:10])
            }
        
        # start_date가 없으면 추가
        if "start_date" not in group_info:
            group_info["start_date"] = datetime.now().isoformat()[:10]
        
        # reading_goal 내 start_date가 없으면 추가
        if "start_date" not in group_info["reading_goal"]:
            group_info["reading_goal"]["start_date"] = group_info.get("start_date", datetime.now().isoformat()[:10])
    
    return data

# 데이터 저장
def save_data(data):
    encrypted_data = encrypt_data(data, KEY)
    with open(DATA_FILE, "wb") as f:
        f.write(encrypted_data)

# 비밀번호 해싱
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# 읽기 목표 관련 함수들
def get_reading_goal_books(goal_type, custom_books=None):
    """읽기 목표에 따른 성경 권 리스트 반환"""
    if goal_type == "전체":
        return ALL_BOOKS
    elif goal_type == "구약":
        books = []
        for category in BIBLE_STRUCTURE["구약"].values():
            books.extend(category)
        return books
    elif goal_type == "신약":
        books = []
        for category in BIBLE_STRUCTURE["신약"].values():
            books.extend(category)
        return books
    elif goal_type == "사용자정의" and custom_books:
        return custom_books
    else:
        return ALL_BOOKS

def calculate_daily_chapters(books, duration_days):
    """읽기 목표에 따른 일일 권장 장 수 계산"""
    total_chapters = sum(BIBLE_CHAPTERS[book] for book in books)
    return max(1, total_chapters // duration_days)

# 로그인/회원가입 함수들
def register_user(nickname, group_code, password):
    data = load_data()
    
    # 닉네임 중복 확인 (같은 그룹 내에서만)
    if group_code in data["groups"]:
        for user_id in data["groups"][group_code]["members"]:
            if user_id in data["users"] and data["users"][user_id]["nickname"] == nickname:
                return False, "이 그룹에 이미 같은 닉네임이 있습니다."
    
    # 그룹 존재 확인
    if group_code not in data["groups"]:
        return False, f"'{group_code}' 그룹을 찾을 수 없습니다. 교회명을 정확히 입력해주세요."
    
    # 사용자 생성
    user_id = f"user_{len(data['users']) + 1}"
    data["users"][user_id] = {
        "nickname": nickname,
        "password": hash_password(password),
        "groups": [group_code],
        "created_at": datetime.now().isoformat()
    }
    
    # 그룹에 사용자 추가
    data["groups"][group_code]["members"].append(user_id)
    
    save_data(data)
    return True, "회원가입이 완료되었습니다!"

def login_user(nickname, password):
    data = load_data()
    
    for user_id, user_info in data["users"].items():
        if (user_info["nickname"] == nickname and 
            user_info["password"] == hash_password(password)):
            return True, user_id
    
    return False, None

def create_group(group_name, admin_nickname, admin_password):
    data = load_data()
    
    # 그룹 코드를 교회 이름으로 직접 사용
    # 이미 존재하는 그룹명인지 확인
    for existing_code, existing_group in data["groups"].items():
        if existing_group["name"] == group_name:
            return None, None
    
    group_code = group_name
    
    # 관리자 사용자 생성
    admin_user_id = f"user_{len(data['users']) + 1}"
    data["users"][admin_user_id] = {
        "nickname": admin_nickname,
        "password": hash_password(admin_password),
        "groups": [group_code],
        "created_at": datetime.now().isoformat()
    }
    
    # 그룹 생성
    data["groups"][group_code] = {
        "name": group_name,
        "admin": admin_user_id,
        "members": [admin_user_id],
        "created_at": datetime.now().isoformat(),
        "reading_goal": {
            "type": "전체",
            "books": ALL_BOOKS,
            "duration_days": 365,
            "start_date": datetime.now().isoformat()[:10]
        }
    }
    
    save_data(data)
    return group_code, admin_user_id

# 읽기 기록 관련 함수들
def record_reading(user_id, group_code, book, chapters):
    """성경 읽기 기록"""
    data = load_data()
    today = datetime.now().strftime("%Y-%m-%d")
    
    if user_id not in data["reading_records"]:
        data["reading_records"][user_id] = {}
    
    if group_code not in data["reading_records"][user_id]:
        data["reading_records"][user_id][group_code] = {}
    
    if today not in data["reading_records"][user_id][group_code]:
        data["reading_records"][user_id][group_code][today] = []
    
    # 중복 기록 방지
    new_record = {"book": book, "chapters": chapters}
    existing_records = data["reading_records"][user_id][group_code][today]
    
    # 같은 책의 기록이 있으면 장 번호 합치기
    book_found = False
    for record in existing_records:
        if record["book"] == book:
            # 기존 장과 새 장 합치기 (중복 제거)
            all_chapters = list(set(record["chapters"] + chapters))
            record["chapters"] = sorted(all_chapters)
            book_found = True
            break
    
    if not book_found:
        existing_records.append(new_record)
    
    save_data(data)

def get_last_read_chapter(user_id, group_code, book):
    """특정 책에서 마지막으로 읽은 장 번호 반환"""
    data = load_data()
    
    if (user_id not in data.get("reading_records", {}) or 
        group_code not in data["reading_records"][user_id]):
        return 0
    
    max_chapter = 0
    for date, daily_records in data["reading_records"][user_id][group_code].items():
        for record in daily_records:
            if record["book"] == book:
                max_chapter = max(max_chapter, max(record["chapters"]))
    
    return max_chapter

def get_next_suggested_chapter(user_id, group_code, book):
    """다음 읽기 권장 장 번호 반환"""
    last_chapter = get_last_read_chapter(user_id, group_code, book)
    total_chapters = BIBLE_CHAPTERS[book]
    
    # 마지막 읽은 장 다음 장을 반환 (책의 총 장수를 넘지 않도록)
    next_chapter = min(last_chapter + 1, total_chapters)
    return next_chapter

def get_user_reading_stats(user_id, group_code):
    """사용자의 읽기 통계 계산"""
    data = load_data()
    
    if (user_id not in data.get("reading_records", {}) or 
        group_code not in data["reading_records"][user_id]):
        return {
            "total_chapters": 0,
            "completed_books": 0,
            "reading_days": 0,
            "progress_by_book": {},
            "streak": 0
        }
    
    records = data["reading_records"][user_id][group_code]
    group = data["groups"][group_code]
    goal_books = group.get("reading_goal", {}).get("books", ALL_BOOKS)
    
    # 책별 읽은 장 수 계산
    progress_by_book = {}
    total_chapters = 0
    
    for book in goal_books:
        progress_by_book[book] = set()
    
    for date, daily_records in records.items():
        for record in daily_records:
            book = record["book"]
            if book in progress_by_book:
                progress_by_book[book].update(record["chapters"])
    
    # 완료된 책 수 계산
    completed_books = 0
    for book, read_chapters in progress_by_book.items():
        total_chapters += len(read_chapters)
        if len(read_chapters) >= BIBLE_CHAPTERS[book]:
            completed_books += 1
    
    # 연속 읽기 일수 계산
    streak = calculate_reading_streak(records)
    
    return {
        "total_chapters": total_chapters,
        "completed_books": completed_books,
        "reading_days": len(records),
        "progress_by_book": {book: list(chapters) for book, chapters in progress_by_book.items()},
        "streak": streak
    }

def calculate_reading_streak(records):
    """연속 읽기 일수 계산"""
    if not records:
        return 0
    
    dates = sorted(records.keys(), reverse=True)
    today = datetime.now().strftime("%Y-%m-%d")
    
    streak = 0
    current_date = datetime.now()
    
    while True:
        date_str = current_date.strftime("%Y-%m-%d")
        if date_str in records and records[date_str]:
            streak += 1
            current_date -= timedelta(days=1)
        else:
            if streak == 0 and date_str == today:
                current_date -= timedelta(days=1)
                continue
            break
    
    return streak

def is_admin(user_id, group_code):
    """사용자가 해당 그룹의 관리자인지 확인"""
    data = load_data()
    if group_code in data["groups"]:
        return data["groups"][group_code]["admin"] == user_id
    return False

def update_reading_goal(group_code, goal_type, duration_days, custom_books=None):
    """그룹의 읽기 목표 업데이트"""
    data = load_data()
    
    if group_code in data["groups"]:
        books = get_reading_goal_books(goal_type, custom_books)
        data["groups"][group_code]["reading_goal"] = {
            "type": goal_type,
            "books": books,
            "duration_days": duration_days,
            "start_date": datetime.now().isoformat()[:10]
        }
        save_data(data)
        return True
    return False

# UI 렌더링 함수들
def render_progress_bar(current, total, label=""):
    """진행률 막대 그래프 렌더링"""
    percentage = (current / total * 100) if total > 0 else 0
    
    return f"""
    <div class="progress-bar-container">
        <div class="progress-bar-fill" style="width: {percentage:.1f}%;">
            {label} {percentage:.1f}% ({current}/{total})
        </div>
    </div>
    """

def render_bible_progress_visual(progress_by_book, goal_books):
    """성경 진행 상황을 시각적으로 렌더링"""
    st.markdown("### 📚 성경읽기 진행 현황")
    
    # 읽기 시작한 책들 찾기
    books_in_progress = []
    for book in goal_books:
        read_chapters = progress_by_book.get(book, [])
        total_chapters = BIBLE_CHAPTERS[book]
        if 0 < len(read_chapters) < total_chapters:
            books_in_progress.append(book)
    
    # 진행 중인 책들을 먼저 표시
    if books_in_progress:
        st.markdown("#### 📖 현재 읽고 있는 책")
        for book in books_in_progress:
            render_chapter_progress(book, progress_by_book.get(book, []), expanded=True)
    
    # 전체 성경 진행 현황
    with st.expander("📊 전체 성경 진행 현황", expanded=False):
        for testament, categories in BIBLE_STRUCTURE.items():
            testament_books = []
            for category_books in categories.values():
                testament_books.extend(category_books)
            
            relevant_books = [book for book in testament_books if book in goal_books]
            if not relevant_books:
                continue
                
            st.markdown(f"**{testament}**")
            
            for category, books in categories.items():
                category_books = [book for book in books if book in goal_books]
                if not category_books:
                    continue
                    
                st.markdown(f"*{category}*")
                
                for book in category_books:
                    read_chapters = progress_by_book.get(book, [])
                    total_chapters = BIBLE_CHAPTERS[book]
                    progress_html = render_progress_bar(len(read_chapters), total_chapters, book)
                    st.markdown(progress_html, unsafe_allow_html=True)

def render_chapter_progress(book, read_chapters, expanded=False):
    """특정 책의 장별 진행 상황 렌더링"""
    total_chapters = BIBLE_CHAPTERS[book]
    completed_chapters = len(read_chapters)
    
    st.markdown(f"""
    <div class="book-progress-item">
        <div class="book-title">
            <span>{book}</span>
            <span style="color: #059669;">({completed_chapters}/{total_chapters}장)</span>
        </div>
    """, unsafe_allow_html=True)
    
    # 장별 진행 상황을 10장 단위로 반응형 표시
    chapter_html = '<div class="chapter-grid">'
    for chapter in range(1, total_chapters + 1):
        if chapter in read_chapters:
            chapter_html += f'<span class="chapter-progress chapter-read">{chapter}</span>'
        else:
            chapter_html += f'<span class="chapter-progress chapter-unread">{chapter}</span>'
    
    chapter_html += '</div></div>'
    st.markdown(chapter_html, unsafe_allow_html=True)

# 메인 앱
def main():
    # 세션 상태 초기화
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
    if "user_id" not in st.session_state:
        st.session_state.user_id = None
    if "current_group" not in st.session_state:
        st.session_state.current_group = None

    # 헤더
    st.markdown("""
    <div class="main-header">
        <h1>📖 말씀동행</h1>
        <p>함께하는 성경읽기 여행</p>
    </div>
    """, unsafe_allow_html=True)

    # 로그인하지 않은 경우
    if not st.session_state.logged_in:
        tab1, tab2, tab3 = st.tabs(["로그인", "회원가입", "그룹 생성"])
        
        with tab1:
            st.subheader("로그인")
            with st.form("login_form"):
                nickname = st.text_input("닉네임", placeholder="예: 김성도")
                password = st.text_input("비밀번호", type="password")
                submit = st.form_submit_button("로그인")
                
                if submit:
                    if not nickname.strip():
                        st.error("닉네임을 입력해주세요.")
                    elif not password:
                        st.error("비밀번호를 입력해주세요.")
                    else:
                        success, user_id = login_user(nickname.strip(), password)
                        if success:
                            st.session_state.logged_in = True
                            st.session_state.user_id = user_id
                            st.session_state.logged_in = True
                            st.session_state.user_id = user_id
                            data = load_data()
                            if data["users"][user_id]["groups"]:
                                st.session_state.current_group = data["users"][user_id]["groups"][0]
                            st.rerun()
                        else:
                            st.error("로그인에 실패했습니다. 닉네임과 비밀번호를 확인해주세요.")
        
        with tab2:
            st.subheader("회원가입")
            with st.form("register_form"):
                new_nickname = st.text_input("닉네임 (한글 가능)", placeholder="예: 김성도")
                group_code = st.text_input("교회명", placeholder="예: 새로운교회")
                new_password = st.text_input("비밀번호", type="password")
                confirm_password = st.text_input("비밀번호 확인", type="password")
                submit = st.form_submit_button("가입하기")
                
                if submit:
                    if not new_nickname.strip():
                        st.error("닉네임을 입력해주세요.")
                    elif not group_code.strip():
                        st.error("교회명을 입력해주세요.")
                    elif new_password != confirm_password:
                        st.error("비밀번호가 일치하지 않습니다.")
                    elif len(new_password) < 4:
                        st.error("비밀번호는 4자 이상이어야 합니다.")
                    else:
                        success, message = register_user(new_nickname.strip(), group_code.strip(), new_password)
                        if success:
                            st.success(message)
                        else:
                            st.error(message)
        
        with tab3:
            st.subheader("새 그룹 생성")
            st.info("💡 교회나 소그룹의 리더가 새로운 그룹을 만들 수 있습니다.")
            with st.form("create_group_form"):
                group_name = st.text_input("교회명 또는 그룹명", placeholder="예: 새로운교회, 청년부, 1구역")
                admin_nickname = st.text_input("관리자 닉네임 (한글 가능)", placeholder="예: 김목사")
                admin_password = st.text_input("관리자 비밀번호", type="password")
                submit = st.form_submit_button("그룹 생성")
                
                if submit:
                    if not group_name.strip():
                        st.error("교회명 또는 그룹명을 입력해주세요.")
                    elif not admin_nickname.strip():
                        st.error("관리자 닉네임을 입력해주세요.")
                    elif len(admin_password) < 4:
                        st.error("비밀번호는 4자 이상이어야 합니다.")
                    else:
                        group_code, user_id = create_group(group_name.strip(), admin_nickname.strip(), admin_password)
                        if group_code:
                            st.success(f"'{group_name}' 그룹이 생성되었습니다! 🎉")
                            st.info(f"📝 **그룹 참여 방법 안내**")
                            st.markdown(f"""
                            다른 멤버들이 가입할 때 아래 정보를 알려주세요:
                            - **교회명**: `{group_name}`
                            - 회원가입 시 '교회명' 칸에 정확히 입력하면 됩니다.
                            """)
                        else:
                            st.error(f"'{group_name}' 그룹이 이미 존재합니다. 다른 이름을 사용해주세요.")

    # 로그인한 경우
    else:
        data = load_data()
        user_info = data["users"][st.session_state.user_id]
        
        # 상단 네비게이션
        col1, col2, col3 = st.columns([3, 1, 1])
        with col1:
            st.write(f"환영합니다, **{user_info['nickname']}**님! 👋")
        
        with col2:
            # 그룹 선택
            if len(user_info["groups"]) > 1:
                selected_group = st.selectbox(
                    "그룹 선택",
                    user_info["groups"],
                    index=user_info["groups"].index(st.session_state.current_group) if st.session_state.current_group in user_info["groups"] else 0,
                    format_func=lambda x: data["groups"][x]["name"] if x in data["groups"] else x
                )
                st.session_state.current_group = selected_group
            else:
                st.session_state.current_group = user_info["groups"][0]
        
        with col3:
            if st.button("로그아웃"):
                st.session_state.logged_in = False
                st.session_state.user_id = None
                st.session_state.current_group = None
                st.rerun()

        # 현재 그룹 정보
        if st.session_state.current_group and st.session_state.current_group in data["groups"]:
            current_group = data["groups"][st.session_state.current_group]
            user_is_admin = is_admin(st.session_state.user_id, st.session_state.current_group)
            
            # 그룹 헤더 및 상위 랭커 표시
            reading_goal = current_group.get("reading_goal", {
                "type": "전체",
                "duration_days": 365
            })
            
            st.markdown(f"""
            <div class="group-header">
                <h3>📚 {current_group['name']}</h3>
                <p>멤버 수: {len(current_group['members'])}명 | 읽기 목표: {reading_goal['type']} ({reading_goal['duration_days']}일)</p>
            </div>
            """, unsafe_allow_html=True)

            # 그룹 TOP 3 및 전체 진행률 표시
            goal_books = current_group.get('reading_goal', {}).get('books', ALL_BOOKS)
            total_goal_chapters = sum(BIBLE_CHAPTERS[book] for book in goal_books)
            
            # 그룹 멤버들의 통계 수집
            group_stats = []
            for member_id in current_group["members"]:
                if member_id in data["users"]:
                    member_info = data["users"][member_id]
                    member_stats = get_user_reading_stats(member_id, st.session_state.current_group)
                    
                    # 진행률 계산
                    member_progress = (member_stats["total_chapters"] / total_goal_chapters * 100) if total_goal_chapters > 0 else 0
                    
                    group_stats.append({
                        "nickname": member_info["nickname"],
                        "total_chapters": member_stats["total_chapters"],
                        "completed_books": member_stats["completed_books"],
                        "streak": member_stats["streak"],
                        "progress": member_progress,
                        "is_current_user": member_id == st.session_state.user_id
                    })
            
            group_stats.sort(key=lambda x: x["progress"], reverse=True)
            
            # TOP 3 표시
            if len(group_stats) >= 3:
                st.markdown("### 🏆 그룹 성경읽기 TOP 3")
                col1, col2, col3 = st.columns(3)
                
                medals = ["🥇", "🥈", "🥉"]
                for i in range(3):
                    member = group_stats[i]
                    medal = medals[i]
                    
                    if i == 0:
                        with col1:
                            st.markdown(f"""
                            <div style="text-align: center; padding: 1rem; background: linear-gradient(45deg, #fbbf24, #f59e0b); border-radius: 10px; margin: 0.5rem;">
                                <div style="font-size: 2rem;">{medal}</div>
                                <div style="font-weight: bold; color: white;">{member['nickname']}</div>
                                <div style="color: white;">{member['progress']:.1f}% 완성</div>
                            </div>
                            """, unsafe_allow_html=True)
                    elif i == 1:
                        with col2:
                            st.markdown(f"""
                            <div style="text-align: center; padding: 1rem; background: linear-gradient(45deg, #fbbf24, #f59e0b); border-radius: 10px; margin: 0.5rem;">
                                <div style="font-size: 2rem;">{medal}</div>
                                <div style="font-weight: bold; color: white;">{member['nickname']}</div>
                                <div style="color: white;">{member['progress']:.1f}% 완성</div>
                            </div>
                            """, unsafe_allow_html=True)
                    else:
                        with col3:
                            st.markdown(f"""
                            <div style="text-align: center; padding: 1rem; background: linear-gradient(45deg, #fbbf24, #f59e0b); border-radius: 10px; margin: 0.5rem;">
                                <div style="font-size: 2rem;">{medal}</div>
                                <div style="font-weight: bold; color: white;">{member['nickname']}</div>
                                <div style="color: white;">{member['progress']:.1f}% 완성</div>
                            </div>
                            """, unsafe_allow_html=True)
            
            # 그룹 전체 읽기 현황 막대그래프
            st.markdown("### 📊 그룹 전체 읽기 현황")
            if group_stats:
                avg_progress = sum(m["progress"] for m in group_stats) / len(group_stats)
                total_completed_books = sum(m["completed_books"] for m in group_stats)
                progress_html = render_progress_bar(avg_progress, 100, "그룹 평균")
                st.markdown(progress_html, unsafe_allow_html=True)
                
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("그룹 평균 진행률", f"{avg_progress:.1f}%")
                with col2:
                    st.metric("그룹 총 완독 책수", f"{total_completed_books}권")

            # 관리자 전용 섹션
            if user_is_admin:
                with st.expander("🔧 그룹 관리 (관리자 전용)", expanded=False):
                    st.markdown('<div class="admin-section">', unsafe_allow_html=True)
                    st.subheader("📋 읽기 목표 설정")
                    
                    col1, col2 = st.columns([2, 1])
                    with col1:
                        goal_type = st.selectbox(
                            "읽기 범위",
                            ["전체", "구약", "신약", "사용자정의"],
                            index=["전체", "구약", "신약", "사용자정의"].index(
                                current_group.get('reading_goal', {}).get('type', '전체')
                            )
                        )
                    
                    with col2:
                        duration_days = st.number_input(
                            "읽기 기간 (일)",
                            min_value=30,
                            max_value=1095,
                            value=current_group.get('reading_goal', {}).get('duration_days', 365),
                            step=1
                        )
                    
                    custom_books = []
                    if goal_type == "사용자정의":
                        st.markdown("**읽을 성경 권 선택:**")
                        
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.markdown("**구약**")
                            for category, books in BIBLE_STRUCTURE["구약"].items():
                                st.markdown(f"*{category}*")
                                for book in books:
                                    current_books = current_group.get('reading_goal', {}).get('books', ALL_BOOKS)
                                    if st.checkbox(book, 
                                                 value=book in current_books,
                                                 key=f"book_{book}"):
                                        custom_books.append(book)
                        
                        with col2:
                            st.markdown("**신약**")
                            for category, books in BIBLE_STRUCTURE["신약"].items():
                                st.markdown(f"*{category}*")
                                for book in books:
                                    current_books = current_group.get('reading_goal', {}).get('books', ALL_BOOKS)
                                    if st.checkbox(book, 
                                                 value=book in current_books,
                                                 key=f"book_{book}"):
                                        custom_books.append(book)
                    
                    if st.button("읽기 목표 업데이트"):
                        if goal_type == "사용자정의" and not custom_books:
                            st.error("사용자정의 선택 시 최소 1권 이상 선택해주세요.")
                        else:
                            success = update_reading_goal(st.session_state.current_group, goal_type, duration_days, custom_books)
                            if success:
                                st.success("읽기 목표가 업데이트되었습니다!")
                                st.rerun()
                            else:
                                st.error("업데이트에 실패했습니다.")
                    
                    # 현재 설정된 목표 정보 표시
                    st.markdown("---")
                    st.markdown("**현재 읽기 목표**")
                    goal_books = current_group.get('reading_goal', {}).get('books', ALL_BOOKS)
                    total_chapters = sum(BIBLE_CHAPTERS[book] for book in goal_books)
                    daily_chapters = calculate_daily_chapters(goal_books, duration_days)
                    start_date = current_group.get('reading_goal', {}).get('start_date', 
                                                  current_group.get('start_date', datetime.now().isoformat()[:10]))
                    
                    st.info(f"""
                    - 📖 총 {len(goal_books)}권, {total_chapters}장
                    - 📅 {duration_days}일 계획 (일평균 {daily_chapters}장)
                    - 📆 시작일: {start_date}
                    """)
                    
                    st.markdown('</div>', unsafe_allow_html=True)

            # 오늘의 성경읽기 기록
            st.subheader("📖 오늘의 성경읽기")
            
            today = datetime.now().strftime("%Y-%m-%d")
            user_stats = get_user_reading_stats(st.session_state.user_id, st.session_state.current_group)
            
            # 오늘 읽은 기록 표시
            today_records = []
            if (st.session_state.user_id in data.get("reading_records", {}) and
                st.session_state.current_group in data["reading_records"][st.session_state.user_id] and
                today in data["reading_records"][st.session_state.user_id][st.session_state.current_group]):
                today_records = data["reading_records"][st.session_state.user_id][st.session_state.current_group][today]
            
            if today_records:
                st.success(f"✅ 오늘 읽은 내용:")
                for record in today_records:
                    chapters_str = ", ".join(map(str, sorted(record["chapters"])))
                    st.info(f"📖 {record['book']} {chapters_str}장")
            
            # 새로운 읽기 기록 추가
            st.markdown("**새로운 읽기 기록 추가**")
            
            col1, col2 = st.columns([2, 1])
            
            with col1:
                goal_books = current_group.get('reading_goal', {}).get('books', ALL_BOOKS)
                selected_book = st.selectbox(
                    "읽은 성경",
                    goal_books,
                    help="오늘 읽은 성경 권을 선택하세요",
                    key="book_select"
                )
            
            with col2:
                if selected_book:
                    max_chapters = BIBLE_CHAPTERS[selected_book]
                    st.info(f"총 {max_chapters}장")
                else:
                    st.info("성경을 선택하세요")
            
            # 장 선택 방식 (폼 밖에서 처리)
            chapter_mode = st.radio(
                "읽은 장 선택",
                ["한 장", "여러 장"],
                horizontal=True,
                key="chapter_mode"
            )
            
            selected_chapters = []
            
            if selected_book:
                max_chapters = BIBLE_CHAPTERS[selected_book]
                
                if chapter_mode == "한 장":
                    suggested_chapter = get_next_suggested_chapter(
                        st.session_state.user_id, 
                        st.session_state.current_group, 
                        selected_book
                    )
                    
                    chapter = st.number_input(
                        "장 번호",
                        min_value=1,
                        max_value=max_chapters,
                        value=suggested_chapter,
                        key="single_chapter"
                    )
                    selected_chapters = [chapter]
                
                else:  # 여러 장
                    last_read = get_last_read_chapter(
                        st.session_state.user_id, 
                        st.session_state.current_group, 
                        selected_book
                    )
                    suggested_start = min(last_read + 1, max_chapters)
                    suggested_end = min(suggested_start + 1, max_chapters)
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        start_chapter = st.number_input(
                            "읽기 시작한 장",
                            min_value=1,
                            max_value=max_chapters,
                            value=suggested_start,
                            key="start_chapter"
                        )
                    with col2:
                        end_chapter = st.number_input(
                            "마지막으로 읽은 장",
                            min_value=start_chapter,
                            max_value=max_chapters,
                            value=max(suggested_end, start_chapter),
                            key="end_chapter"
                        )
                    selected_chapters = list(range(start_chapter, end_chapter + 1))
            
            # 읽기 기록 추가 버튼
            if st.button("📝 읽기 기록 추가", type="primary"):
                if selected_chapters and selected_book:
                    record_reading(st.session_state.user_id, st.session_state.current_group, selected_book, selected_chapters)
                    chapters_str = ", ".join(map(str, sorted(selected_chapters)))
                    st.success(f"🎉 {selected_book} {chapters_str}장 읽기가 기록되었습니다!")
                    st.rerun()
                else:
                    if not selected_book:
                        st.error("성경을 선택해주세요.")
                    else:
                        st.error("읽은 장을 확인해주세요.")

            # 개인 읽기 현황
            st.subheader("📊 나의 읽기 현황")
            
            progress_percentage = (user_stats["total_chapters"] / total_goal_chapters * 100) if total_goal_chapters > 0 else 0
            
            # 개인 진행률 막대그래프
            progress_html = render_progress_bar(user_stats["total_chapters"], total_goal_chapters, "나의 진행률")
            st.markdown(progress_html, unsafe_allow_html=True)

            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("읽은 장수", f"{user_stats['total_chapters']}장")
            with col2:
                st.metric("완독한 책", f"{user_stats['completed_books']}권")
            with col3:
                st.metric("연속 읽기", f"{user_stats['streak']}일")
            with col4:
                st.metric("전체 진행률", f"{progress_percentage:.1f}%")

            # 연속 읽기 배지
            if user_stats['streak'] > 0:
                if user_stats['streak'] >= 100:
                    badge_text = f"🏆 {user_stats['streak']}일 연속 대단해요!"
                elif user_stats['streak'] >= 30:
                    badge_text = f"🔥 {user_stats['streak']}일 연속 달성!"
                elif user_stats['streak'] >= 7:
                    badge_text = f"⭐ {user_stats['streak']}일 연속!"
                else:
                    badge_text = f"🌱 {user_stats['streak']}일 연속"
                
                st.markdown(f"""
                <div style="background: linear-gradient(45deg, #d97706, #f59e0b); 
                           color: white; padding: 0.5rem 1rem; border-radius: 20px; 
                           text-align: center; font-weight: bold; margin: 1rem 0;">
                    {badge_text}
                </div>
                """, unsafe_allow_html=True)

            # 성경 진행 현황 시각화
            render_bible_progress_visual(user_stats["progress_by_book"], goal_books)

            # 그룹 현황 테이블
            st.subheader("👥 그룹 멤버 상세 현황")
            
            if group_stats:
                # 테이블용 데이터 변환
                table_data = []
                today = datetime.now().strftime("%Y-%m-%d")
                
                for member in group_stats:
                    # 오늘 읽기 여부 확인
                    member_id = None
                    for uid, user_info in data["users"].items():
                        if user_info["nickname"] == member["nickname"]:
                            member_id = uid
                            break
                    
                    today_reading = "❌"
                    if (member_id and member_id in data.get("reading_records", {}) and
                        st.session_state.current_group in data["reading_records"][member_id] and
                        today in data["reading_records"][member_id][st.session_state.current_group] and
                        data["reading_records"][member_id][st.session_state.current_group][today]):
                        today_reading = "✅"
                    
                    table_data.append({
                        "닉네임": member["nickname"],
                        "읽은 장수": member["total_chapters"],
                        "완독한 책": member["completed_books"],
                        "연속 읽기": member["streak"],
                        "진행률": member["progress"],
                        "오늘 읽기": today_reading
                    })
                
                df = pd.DataFrame(table_data)
                df.index = range(1, len(df) + 1)
                
                # 상위 3명 강조 스타일 (다크테마 호환)
                def highlight_top3(row):
                    return ['' for _ in row]  # CSS로 처리하므로 여기서는 제거
                
                # 다크테마 호환을 위한 CSS 클래스 추가
                st.markdown("""
                <style>
                /* Streamlit 데이터프레임 다크테마 강제 오버라이드 */
                .stDataFrame > div {
                    background-color: white !important;
                }
                
                .stDataFrame table {
                    background-color: white !important;
                    color: #1f2937 !important;
                }
                
                .stDataFrame th {
                    background-color: #f8fafc !important;
                    color: #374151 !important;
                    font-weight: 600 !important;
                }
                
                .stDataFrame td {
                    background-color: white !important;
                    color: #1f2937 !important;
                }
                
                .stDataFrame tbody tr:nth-child(1) {
                    background-color: #fef3c7 !important;
                    font-weight: 600 !important;
                }
                
                .stDataFrame tbody tr:nth-child(2) {
                    background-color: #fef3c7 !important;
                    font-weight: 500 !important;
                }
                
                .stDataFrame tbody tr:nth-child(3) {
                    background-color: #fef3c7 !important;
                    font-weight: 500 !important;
                }
                </style>
                """, unsafe_allow_html=True)
                
                styled_df = df
                st.dataframe(
                    styled_df,
                    column_config={
                        "닉네임": "닉네임",
                        "읽은 장수": "읽은 장수",
                        "완독한 책": "완독한 책",
                        "연속 읽기": "연속 읽기",
                        "진행률": st.column_config.ProgressColumn(
                            "진행률",
                            help="목표 대비 진행률",
                            format="%.1f%%",
                            min_value=0,
                            max_value=100,
                        ),
                        "오늘 읽기": "오늘"
                    },
                    use_container_width=True
                )

        else:
            st.error("그룹 정보를 찾을 수 없습니다.")

if __name__ == "__main__":
    main()
