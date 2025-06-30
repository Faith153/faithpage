import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime, date, timedelta
import calendar
import openai
from typing import Dict, List, Optional
import uuid

# 페이지 설정
st.set_page_config(
    page_title="DD 업무관리시스템",
    page_icon="📋",
    layout="wide"
)

# CSS 스타일링
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
    }
    .priority-high { border-left: 5px solid #ff4757; }
    .priority-medium { border-left: 5px solid #ffa502; }
    .priority-low { border-left: 5px solid #2ed573; }
    .task-card {
        background: white;
        padding: 1rem;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin-bottom: 1rem;
    }
    .calendar-cell {
        border: 1px solid #ddd;
        padding: 5px;
        height: 80px;
        vertical-align: top;
    }
    .task-dot {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        display: inline-block;
        margin: 2px;
    }
    .status-pending { background-color: #ff6b6b; }
    .status-progress { background-color: #4ecdc4; }
    .status-completed { background-color: #45b7d1; }
</style>
""", unsafe_allow_html=True)

class WorkManager:
    def __init__(self):
        # 데이터 저장 파일 경로
        self.data_file = "work_manager_data.json"
        
        # secrets.toml에서 비밀번호 로드
        try:
            self.admin_password = st.secrets["work_manager"]["admin_password"]
            self.manager_password = st.secrets["work_manager"]["manager_password"]
        except Exception as e:
            st.error("설정 파일 로드 오류. secrets.toml 파일을 확인해주세요.")
            self.admin_password = None
            self.manager_password = None
        
        # 세션 상태 초기화
        if 'authenticated' not in st.session_state:
            st.session_state.authenticated = False
        if 'current_user' not in st.session_state:
            st.session_state.current_user = None
        if 'user_role' not in st.session_state:
            st.session_state.user_role = None
        if 'tasks' not in st.session_state:
            st.session_state.tasks = self.load_tasks()
        if 'chat_history' not in st.session_state:
            st.session_state.chat_history = []

    def authenticate_user(self, password: str) -> bool:
        """비밀번호만으로 사용자 인증"""
        if password == self.admin_password:
            st.session_state.authenticated = True
            st.session_state.current_user = "대표"
            st.session_state.user_role = "admin"
            return True
        elif password == self.manager_password:
            st.session_state.authenticated = True
            st.session_state.current_user = "총괄팀장"
            st.session_state.user_role = "manager"
            return True
        return False

    def get_user_name(self) -> str:
        """현재 사용자 이름 반환"""
        return st.session_state.get('current_user', '사용자')

    def load_tasks(self) -> List[Dict]:
        """저장된 업무 목록 로드"""
        try:
            if os.path.exists(self.data_file):
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return data.get('tasks', [])
            else:
                # 파일이 없으면 빈 리스트 반환하고 기본 파일 생성
                self.save_tasks([])
                return []
        except Exception as e:
            st.error(f"데이터 로드 중 오류 발생: {e}")
            return []

    def save_tasks(self, tasks=None):
        """업무 목록 저장"""
        try:
            if tasks is None:
                tasks = st.session_state.tasks
            
            data = {
                'tasks': tasks,
                'last_updated': datetime.now().isoformat()
            }
            
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            st.error(f"데이터 저장 중 오류 발생: {e}")

    def backup_data(self):
        """데이터 백업 생성"""
        try:
            if os.path.exists(self.data_file):
                backup_file = f"work_manager_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                with open(self.data_file, 'r', encoding='utf-8') as original:
                    with open(backup_file, 'w', encoding='utf-8') as backup:
                        backup.write(original.read())
                return backup_file
        except Exception as e:
            st.error(f"백업 생성 중 오류 발생: {e}")
            return None

    def get_openai_client(self):
        """OpenAI 클라이언트 초기화"""
        try:
            api_key = st.secrets["faithgpt"]["API_KEY"]
            client = openai.OpenAI(api_key=api_key)
            return client
        except Exception as e:
            st.error(f"OpenAI API 연결 실패: {e}")
            return None

    def chat_with_gpt(self, message: str) -> str:
        """ChatGPT와 대화"""
        client = self.get_openai_client()
        if not client:
            return "API 연결에 실패했습니다."
        
        try:
            response = client.chat.completions.create(
                model="gpt-4.1",
                messages=[
                    {"role": "system", "content": """당신은 디자인드림의 업무 관리 어시스턴트입니다. 
                    승화전사 전문 기업의 대표와 총괄팀장의 업무 효율성을 높이는 데 도움을 주세요.
                    간결하고 실용적인 조언을 제공하며, 업무 우선순위나 처리 방법에 대한 제안을 해주세요.
                    내부 업무를 효율적으로 하기 위한 부분에 집중합니다."""},
                    {"role": "user", "content": message}
                ],
                max_tokens=10000,
                temperature=0.2
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"응답 생성 중 오류가 발생했습니다: {e}"

    def render_login(self):
        """로그인 화면"""
        st.markdown('<div class="main-header"><h1>🏢 DD 업무관리시스템</h1></div>', unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.subheader("🔐 로그인")
            st.info("💡 접속코드를 입력하세요")
            password = st.text_input("접속코드", type="password", placeholder="접속코드를 입력해주세요")
            
            if st.button("로그인", use_container_width=True):
                if self.authenticate_user(password):
                    st.success(f"{self.get_user_name()}님, 환영합니다!")
                    st.rerun()
                else:
                    st.error("접속코드가 올바르지 않습니다.")

    def render_calendar(self):
        """월별 캘린더 렌더링"""
        st.subheader("📅 이번 달 업무 캘린더")
        
        # 현재 날짜 기준으로 캘린더 생성
        today = date.today()
        cal = calendar.monthcalendar(today.year, today.month)
        
        # 이번 달 업무들 필터링
        month_tasks = [task for task in st.session_state.tasks 
                      if task.get('due_date') and 
                      datetime.strptime(task['due_date'], '%Y-%m-%d').month == today.month]
        
        # 캘린더 헤더
        st.markdown(f"### {today.year}년 {today.month}월")
        
        # 요일 헤더
        cols = st.columns(7)
        weekdays = ['월', '화', '수', '목', '금', '토', '일']
        for i, day in enumerate(weekdays):
            cols[i].markdown(f"**{day}**")
        
        # 캘린더 날짜들
        for week in cal:
            cols = st.columns(7)
            for i, day in enumerate(week):
                if day == 0:
                    cols[i].markdown("")
                else:
                    # 해당 날짜의 업무 개수 계산
                    day_date = f"{today.year}-{today.month:02d}-{day:02d}"
                    day_tasks = [task for task in month_tasks if task.get('due_date') == day_date]
                    
                    if day_tasks:
                        task_count = len(day_tasks)
                        cols[i].markdown(f"""
                        <div style="border: 1px solid #ddd; padding: 5px; height: 60px; background: {'#ffe6e6' if task_count > 0 else 'white'};">
                            <strong>{day}</strong><br>
                            <small>{task_count}개 업무</small>
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        cols[i].markdown(f"""
                        <div style="border: 1px solid #ddd; padding: 5px; height: 60px;">
                            {day}
                        </div>
                        """, unsafe_allow_html=True)

    def render_task_form(self):
        """새 업무 추가 폼"""
        st.subheader("➕ 새 업무 추가")
        
        with st.form("new_task_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                title = st.text_input("업무 제목", placeholder="예: 장비 견적서 검토")
                category = st.selectbox("카테고리", 
                    ["결제승인", "장비관리", "고객대응", "기획업무", "인사관리", "기타"])
                priority = st.selectbox("우선순위", ["높음", "보통", "낮음"])
                
            with col2:
                due_date = st.date_input("마감일", value=date.today() + timedelta(days=1))
                estimated_time = st.selectbox("예상 소요시간", 
                    ["15분", "30분", "1시간", "2시간", "반나절", "하루", "며칠"])
                requester = st.selectbox("요청자", ["총괄팀장", "직접입력", "기타"])
            
            description = st.text_area("세부 내용", height=100)
            
            if st.form_submit_button("업무 추가"):
                new_task = {
                    "id": str(uuid.uuid4()),
                    "title": title,
                    "description": description,
                    "category": category,
                    "priority": priority,
                    "due_date": due_date.strftime('%Y-%m-%d'),
                    "estimated_time": estimated_time,
                    "requester": requester,
                    "status": "대기중",
                    "created_date": datetime.now().strftime('%Y-%m-%d %H:%M'),
                    "completed_date": None,
                    "notes": ""
                }
                st.session_state.tasks.append(new_task)
                self.save_tasks()
                st.success("새 업무가 추가되었습니다!")
                st.rerun()

    def render_task_list(self):
        """업무 목록 렌더링"""
        st.subheader("📋 업무 목록")
        
        if not st.session_state.tasks:
            st.info("등록된 업무가 없습니다. 새 업무를 추가해보세요!")
            return
        
        # 필터링 옵션
        col1, col2, col3 = st.columns(3)
        with col1:
            status_filter = st.selectbox("상태별 필터", ["전체", "대기중", "진행중", "완료"])
        with col2:
            priority_filter = st.selectbox("우선순위별 필터", ["전체", "높음", "보통", "낮음"])
        with col3:
            category_filter = st.selectbox("카테고리별 필터", 
                ["전체", "결제승인", "장비관리", "고객대응", "기획업무", "인사관리", "기타"])
        
        # 필터링된 업무 목록
        filtered_tasks = st.session_state.tasks
        if status_filter != "전체":
            filtered_tasks = [t for t in filtered_tasks if t["status"] == status_filter]
        if priority_filter != "전체":
            filtered_tasks = [t for t in filtered_tasks if t["priority"] == priority_filter]
        if category_filter != "전체":
            filtered_tasks = [t for t in filtered_tasks if t["category"] == category_filter]
        
        # 우선순위순 정렬
        priority_order = {"높음": 0, "보통": 1, "낮음": 2}
        filtered_tasks.sort(key=lambda x: priority_order.get(x["priority"], 3))
        
        # 업무 카드들 렌더링
        for task in filtered_tasks:
            self.render_task_card(task)

    def render_task_card(self, task: Dict):
        """개별 업무 카드 렌더링"""
        priority_class = f"priority-{task['priority'].replace('높음', 'high').replace('보통', 'medium').replace('낮음', 'low')}"
        
        with st.container():
            st.markdown(f'<div class="task-card {priority_class}">', unsafe_allow_html=True)
            
            col1, col2, col3 = st.columns([3, 1, 1])
            
            with col1:
                # 체크박스로 완료 상태 관리
                completed = st.checkbox(
                    f"**{task['title']}**", 
                    value=task['status'] == "완료",
                    key=f"task_{task['id']}"
                )
                
                if completed and task['status'] != "완료":
                    task['status'] = "완료"
                    task['completed_date'] = datetime.now().strftime('%Y-%m-%d %H:%M')
                    self.save_tasks()
                elif not completed and task['status'] == "완료":
                    task['status'] = "대기중"
                    task['completed_date'] = None
                    self.save_tasks()
                
                # 업무 정보 표시
                st.markdown(f"""
                **카테고리:** {task['category']} | **우선순위:** {task['priority']} | **마감일:** {task['due_date']}  
                **요청자:** {task['requester']} | **예상시간:** {task['estimated_time']}  
                **등록일:** {task['created_date']}
                """)
                
                if task['description']:
                    with st.expander("세부 내용 보기"):
                        st.write(task['description'])
            
            with col2:
                status_color = {"대기중": "🔴", "진행중": "🟡", "완료": "🟢"}
                st.markdown(f"**상태:** {status_color.get(task['status'], '⚪')} {task['status']}")
                
                if task['completed_date']:
                    st.markdown(f"**완료일:** {task['completed_date']}")
            
            with col3:
                if st.button("수정", key=f"edit_{task['id']}"):
                    st.session_state.editing_task = task['id']
                
                if st.button("삭제", key=f"delete_{task['id']}"):
                    st.session_state.tasks = [t for t in st.session_state.tasks if t['id'] != task['id']]
                    self.save_tasks()
                    st.rerun()
            
            # 메모 추가 기능
            notes = st.text_area("메모/진행상황", value=task.get('notes', ''), 
                               key=f"notes_{task['id']}", height=70)
            if notes != task.get('notes', ''):
                task['notes'] = notes
                self.save_tasks()
            
            st.markdown('</div>', unsafe_allow_html=True)

    def render_ai_assistant(self):
        """AI 어시스턴트 섹션"""
        st.subheader("🤖 AI 업무 어시스턴트")
        
        # 채팅 기록 표시
        for chat in st.session_state.chat_history[-5:]:  # 최근 5개만 표시
            with st.chat_message(chat["role"]):
                st.write(chat["content"])
        
        # 새 메시지 입력
        if prompt := st.chat_input("업무에 대해 질문하거나 도움을 요청하세요..."):
            # 사용자 메시지 추가
            st.session_state.chat_history.append({"role": "user", "content": prompt})
            
            # 현재 업무 상황을 컨텍스트로 제공
            context = f"현재 등록된 업무 수: {len(st.session_state.tasks)}개\n"
            pending_tasks = [t for t in st.session_state.tasks if t['status'] == '대기중']
            context += f"대기중인 업무: {len(pending_tasks)}개\n"
            
            if pending_tasks:
                context += "주요 대기 업무:\n"
                for task in pending_tasks[:3]:
                    context += f"- {task['title']} (우선순위: {task['priority']}, 마감: {task['due_date']})\n"
            
            full_prompt = f"업무 현황:\n{context}\n\n질문: {prompt}"
            
            # AI 응답 생성
            response = self.chat_with_gpt(full_prompt)
            st.session_state.chat_history.append({"role": "assistant", "content": response})
            
            st.rerun()

    def render_dashboard(self):
        """대시보드 렌더링"""
        user_emoji = "👑" if st.session_state.user_role == "admin" else "👨‍💼"
        st.markdown(f'<div class="main-header"><h1>📊 디자인드림 업무관리 대시보드</h1><p>{user_emoji} {self.get_user_name()}님 환영합니다</p></div>', unsafe_allow_html=True)
        
        # 상단 통계
        col1, col2, col3, col4 = st.columns(4)
        
        total_tasks = len(st.session_state.tasks)
        pending_tasks = len([t for t in st.session_state.tasks if t['status'] == '대기중'])
        in_progress_tasks = len([t for t in st.session_state.tasks if t['status'] == '진행중'])
        completed_tasks = len([t for t in st.session_state.tasks if t['status'] == '완료'])
        
        with col1:
            st.metric("전체 업무", total_tasks)
        with col2:
            st.metric("대기중", pending_tasks, delta=f"-{pending_tasks}")
        with col3:
            st.metric("진행중", in_progress_tasks)
        with col4:
            st.metric("완료", completed_tasks, delta=f"+{completed_tasks}")
        
        # 메인 콘텐츠
        tab1, tab2, tab3, tab4 = st.tabs(["📅 캘린더", "📋 업무관리", "➕ 업무추가", "🤖 AI 어시스턴트"])
        
        with tab1:
            self.render_calendar()
        
        with tab2:
            self.render_task_list()
        
        with tab3:
            self.render_task_form()
        
        with tab4:
            self.render_ai_assistant()
        
        # 로그아웃 버튼
        with st.sidebar:
            st.markdown(f"### {user_emoji} {self.get_user_name()}")
            st.markdown("---")
            
            # 데이터 관리 섹션
            st.markdown("#### 📁 데이터 관리")
            if st.button("💾 수동 저장", use_container_width=True):
                self.save_tasks()
                st.success("데이터가 저장되었습니다!")
            
            if st.button("🔄 백업 생성", use_container_width=True):
                backup_file = self.backup_data()
                if backup_file:
                    st.success(f"백업이 생성되었습니다: {backup_file}")
            
            # 데이터 상태 표시
            if os.path.exists(self.data_file):
                file_stats = os.stat(self.data_file)
                last_modified = datetime.fromtimestamp(file_stats.st_mtime)
                st.markdown(f"**마지막 저장:** {last_modified.strftime('%m/%d %H:%M')}")
            
            st.markdown("---")
            if st.button("🚪 로그아웃", use_container_width=True):
                # 로그아웃 전 자동 저장
                self.save_tasks()
                st.session_state.authenticated = False
                st.session_state.current_user = None
                st.session_state.user_role = None
                st.rerun()

    def run(self):
        """메인 실행 함수"""
        if not st.session_state.authenticated:
            self.render_login()
        else:
            self.render_dashboard()

# 앱 실행
if __name__ == "__main__":
    app = WorkManager()
    app.run()
