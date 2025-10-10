"""
관리자 관련 라우트
"""
from flask import Blueprint, render_template, request, redirect, url_for, jsonify, make_response, send_file
import pandas as pd
import openpyxl
from io import BytesIO, StringIO
import os
import csv
from datetime import datetime
from werkzeug.utils import secure_filename
from app.models import DatabaseManager
from app.models.admin import AdminManager
from app.models.chatbot import ChatbotTypeManager
from app.models.video import VideoManager
from app.models.activity_log import ActivityLogManager
import hashlib
from app import config

# 블루프린트 생성
bp = Blueprint('admin', __name__, url_prefix='/admin')

# 매니저 인스턴스
db_manager = DatabaseManager()
admin_manager = AdminManager()
chatbot_manager = ChatbotTypeManager()
video_manager = VideoManager()
activity_log_manager = ActivityLogManager()

def check_admin_auth(request):
    """관리자 인증 확인"""
    admin_id = request.cookies.get('admin_id')
    admin_role = request.cookies.get('admin_role')
    
    if admin_id and admin_role:
        # 데이터베이스에서 관리자 존재 확인
        admin = admin_manager.get_admin_by_id(int(admin_id))
        if admin:
            return (int(admin_id), admin_role)
    return None

def require_auth(f):
    """인증 데코레이터"""
    def decorated_function(*args, **kwargs):
        auth = check_admin_auth(request)
        if not auth:
            return redirect(url_for('admin.admin_login'))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

def require_super(f):
    """Super 권한 데코레이터"""
    def decorated_function(*args, **kwargs):
        auth = check_admin_auth(request)
        if not auth:
            return redirect(url_for('admin.admin_login'))
        elif auth[1] != 'super':
            return redirect(url_for('admin.dashboard'))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

@bp.route('/login', methods=['GET', 'POST'])
def admin_login():
    """관리자 로그인"""
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        
        auth_result = admin_manager.authenticate_admin(username, password)
        if auth_result:
            admin_id, role = auth_result
            # 쿠키 설정
            response = make_response(redirect(url_for('admin.dashboard')))
            response.set_cookie('admin_id', str(admin_id), max_age=3600)  # 1시간
            response.set_cookie('admin_role', role, max_age=3600)
            return response
        else:
            return render_template('admin/login.html', error='잘못된 인증 정보입니다.')
    
    return render_template('admin/login.html')

@bp.route('/logout')
def admin_logout():
    """관리자 로그아웃"""
    response = make_response(redirect(url_for('admin.admin_login')))
    response.set_cookie('admin_id', '', expires=0)
    response.set_cookie('admin_role', '', expires=0)
    return response

@bp.route('/')
@require_auth
def dashboard():
    """관리자 대시보드"""
    
    # 사용자 목록 가져오기
    conn = db_manager.get_connection()
    cursor = conn.cursor()
    
    try:
        # 사용자별 메시지 수 통계
        cursor.execute("""
            SELECT u.id, u.username, COUNT(m.id) as message_count,
                   MAX(m.timestamp) as last_message
            FROM user u
            LEFT JOIN message m ON u.id = m.user_id
            GROUP BY u.id, u.username
            ORDER BY last_message DESC
        """)
        users = cursor.fetchall()
        
        # 전체 통계
        cursor.execute("SELECT COUNT(*) FROM user")
        total_users = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM message")
        total_messages = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM message WHERE sender = 'user'")
        user_messages = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM message WHERE sender = 'bot'")
        bot_messages = cursor.fetchone()[0]
        
    finally:
        conn.close()
    
    return render_template('admin/dashboard.html', 
                         users=users,
                         total_users=total_users,
                         total_messages=total_messages,
                         user_messages=user_messages,
                         bot_messages=bot_messages)

@bp.route('/user/<int:user_id>')
def user_detail(user_id):
    """사용자 상세 정보 및 채팅 기록"""
    if not check_admin_auth(request):
        return redirect(url_for('admin.admin_login'))
    
    conn = db_manager.get_connection()
    cursor = conn.cursor()
    
    try:
        # 사용자 정보
        cursor.execute("SELECT id, username FROM user WHERE id = ?", (user_id,))
        user = cursor.fetchone()
        
        if not user:
            return redirect(url_for('admin.dashboard'))
        
        # 사용자의 모든 메시지
        cursor.execute("""
            SELECT sender, content, timestamp
            FROM message
            WHERE user_id = ?
            ORDER BY timestamp ASC
        """, (user_id,))
        messages = cursor.fetchall()
        
    finally:
        conn.close()
    
    return render_template('admin/user_detail.html', user=user, messages=messages)

@bp.route('/admins')
@require_super
def admin_management():
    """관리자 계정 관리 (Super 권한 필요)"""
    admins = admin_manager.get_all_admins()
    return render_template('admin/admin_management.html', admins=admins)

@bp.route('/create_admin_page')
@require_super
def create_admin_page():
    """관리자 생성 페이지"""
    student_numbers = admin_manager.get_all_student_numbers()
    return render_template('admin/create_admin.html', student_numbers=student_numbers)

@bp.route('/create_admin', methods=['POST'])
@require_super
def create_admin():
    """새 관리자 생성 (Super 권한 필요)"""
    username = request.form.get('username', '').strip()
    password = request.form.get('password', '').strip()
    role = request.form.get('role', 'admin').strip()
    student_number = request.form.get('student_number', '').strip()
    
    if not username or not password:
        return redirect(url_for('admin.create_admin_page'))
    
    # 학번 검증
    if not admin_manager.verify_student_number(student_number):
        return render_template('admin/create_admin.html', 
                             student_numbers=admin_manager.get_all_student_numbers(),
                             error='유효하지 않은 학번입니다.')
    
    success = admin_manager.create_admin(username, password, role)
    if success:
        return redirect(url_for('admin.admin_management'))
    else:
        return render_template('admin/create_admin.html',
                             student_numbers=admin_manager.get_all_student_numbers(),
                             error='관리자 생성에 실패했습니다.')

@bp.route('/change_password/<int:admin_id>', methods=['POST'])
@require_super
def change_password(admin_id):
    """관리자 비밀번호 변경 (Super 권한 필요)"""
    new_password = request.form.get('new_password', '').strip()
    
    if not new_password:
        return redirect(url_for('admin.admin_management'))
    
    success = admin_manager.update_admin_password(admin_id, new_password)
    return redirect(url_for('admin.admin_management'))

@bp.route('/delete_admin/<int:admin_id>', methods=['POST'])
@require_super
def delete_admin(admin_id):
    """관리자 삭제 (Super 권한 필요)"""
    current_admin_id = check_admin_auth(request)[0]
    success = admin_manager.delete_admin(admin_id, current_admin_id)
    
    if success:
        return jsonify({'success': True})
    else:
        return jsonify({'success': False, 'error': '삭제할 수 없습니다.'}), 400

# 학번 관리 라우트들 (회원 관리 영역으로 이동)
@bp.route('/student_numbers')
@require_auth
def student_number_management():
    """학번 관리 페이지"""
    student_numbers = admin_manager.get_all_student_numbers()
    return render_template('admin/student_number_management.html', student_numbers=student_numbers)

@bp.route('/add_student_number', methods=['POST'])
@require_auth
def add_student_number():
    """학번 추가"""
    student_number = request.form.get('student_number', '').strip()
    name = request.form.get('name', '').strip()
    
    if not student_number:
        return redirect(url_for('admin.student_number_management'))
    
    # 학번 10자리 검증
    if len(student_number) != 10 or not student_number.isdigit():
        return render_template('admin/student_number_management.html',
                             student_numbers=admin_manager.get_all_student_numbers(),
                             error='학번은 10자리 숫자여야 합니다.')
    
    success = admin_manager.add_student_number(student_number, name)
    if success:
        return redirect(url_for('admin.student_number_management'))
    else:
        return render_template('admin/student_number_management.html',
                             student_numbers=admin_manager.get_all_student_numbers(),
                             error='학번 추가에 실패했습니다. (중복된 학번일 수 있습니다)')

@bp.route('/delete_student_number/<int:student_number_id>', methods=['POST'])
@require_auth
def delete_student_number(student_number_id):
    """학번 삭제"""
    success = admin_manager.delete_student_number(student_number_id)
    
    if success:
        return jsonify({'success': True})
    else:
        return jsonify({'success': False, 'error': '삭제에 실패했습니다.'}), 400

@bp.route('/users')
@require_auth
def user_management():
    """회원 관리 페이지"""
    users = db_manager.get_all_users_with_stats()
    stats = db_manager.get_user_stats()
    total_users, active_users, total_messages, recent_users = stats
    
    return render_template('admin/user_management.html', 
                         users=users,
                         total_users=total_users,
                         active_users=active_users,
                         total_messages=total_messages,
                         recent_users=recent_users)

@bp.route('/delete_user/<int:user_id>', methods=['POST'])
@require_auth
def delete_user(user_id):
    """회원 삭제"""
    success = db_manager.delete_user(user_id)
    
    if success:
        return jsonify({'success': True})
    else:
        return jsonify({'success': False, 'error': '삭제에 실패했습니다.'}), 400

@bp.route('/api/user/<int:user_id>/messages')
def user_messages_api(user_id):
    """사용자 메시지 API"""
    if not check_admin_auth(request):
        return jsonify({'error': '인증이 필요합니다'}), 401
    
    conn = db_manager.get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT sender, content, timestamp
            FROM message
            WHERE user_id = ?
            ORDER BY timestamp ASC
        """, (user_id,))
        messages = cursor.fetchall()
        
        # JSON 형태로 변환
        messages_data = []
        for sender, content, timestamp in messages:
            messages_data.append({
                'sender': sender,
                'content': content,
                'timestamp': timestamp
            })
        
        return jsonify({'messages': messages_data})
        
    finally:
        conn.close()

@bp.route('/prompts')
@require_auth
def prompt_management():
    """프롬프트 관리 페이지"""
    chatbot_types = chatbot_manager.get_all_chatbot_types()
    
    # 각 챗봇 타입별 사용자 수 조회
    usage_counts = {}
    for chatbot_type in chatbot_types:
        usage_counts[chatbot_type[0]] = chatbot_manager.get_chatbot_type_usage(chatbot_type[0])
    
    return render_template('admin/prompt_management.html',
                         chatbot_types=chatbot_types,
                         usage_counts=usage_counts)

@bp.route('/create_chatbot_type', methods=['POST'])
@require_auth
def create_chatbot_type():
    """챗봇 타입 생성"""
    name = request.form.get('name')
    description = request.form.get('description')
    system_prompt = request.form.get('system_prompt')
    
    chatbot_manager.create_chatbot_type(name, description, system_prompt)
    return redirect(url_for('admin.prompt_management'))

@bp.route('/update_chatbot_type/<int:chatbot_type_id>', methods=['POST'])
@require_auth
def update_chatbot_type(chatbot_type_id):
    """챗봇 타입 업데이트"""
    name = request.form.get('name')
    description = request.form.get('description')
    system_prompt = request.form.get('system_prompt')
    
    chatbot_manager.update_chatbot_type(chatbot_type_id, name, description, system_prompt)
    return redirect(url_for('admin.prompt_management'))

@bp.route('/delete_chatbot_type/<int:chatbot_type_id>', methods=['POST'])
@require_auth
def delete_chatbot_type(chatbot_type_id):
    """챗봇 타입 삭제"""
    success = chatbot_manager.delete_chatbot_type(chatbot_type_id)
    
    if success:
        return jsonify({'success': True})
    else:
        return jsonify({'success': False, 'error': '사용 중인 챗봇 타입은 삭제할 수 없습니다.'}), 400

@bp.route('/excel_upload')
@require_auth
def excel_upload_page():
    """엑셀 업로드 페이지"""
    chatbot_types = chatbot_manager.get_all_chatbot_types()
    return render_template('admin/excel_upload.html', chatbot_types=chatbot_types)

@bp.route('/download_template')
@require_auth
def download_template():
    """엑셀 템플릿 다운로드"""
    # 템플릿 데이터 생성
    data = {
        'username': ['user001', 'user002', 'user003'],
        'password': ['password123', 'password123', 'password123'],
        'chatbot_type_id': [1, 2, 3]
    }
    
    df = pd.DataFrame(data)
    
    # 엑셀 파일 생성
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Users')
    
    output.seek(0)
    
    return send_file(
        output,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name='user_template.xlsx'
    )

@bp.route('/upload_excel', methods=['POST'])
@require_auth
def upload_excel():
    """엑셀 파일 업로드 및 사용자 등록"""
    if 'excel_file' not in request.files:
        chatbot_types = chatbot_manager.get_all_chatbot_types()
        return render_template('admin/excel_upload.html', 
                             chatbot_types=chatbot_types,
                             error='파일이 선택되지 않았습니다.')
    
    file = request.files['excel_file']
    
    if file.filename == '':
        chatbot_types = chatbot_manager.get_all_chatbot_types()
        return render_template('admin/excel_upload.html', 
                             chatbot_types=chatbot_types,
                             error='파일이 선택되지 않았습니다.')
    
    if not file.filename.endswith('.xlsx'):
        chatbot_types = chatbot_manager.get_all_chatbot_types()
        return render_template('admin/excel_upload.html', 
                             chatbot_types=chatbot_types,
                             error='xlsx 파일만 업로드 가능합니다.')
    
    try:
        # 엑셀 파일 읽기
        df = pd.read_excel(file)
        
        # 필수 컬럼 확인
        required_columns = ['username', 'password', 'chatbot_type_id']
        if not all(col in df.columns for col in required_columns):
            chatbot_types = chatbot_manager.get_all_chatbot_types()
            return render_template('admin/excel_upload.html', 
                                 chatbot_types=chatbot_types,
                                 error='필수 컬럼이 누락되었습니다: username, password, chatbot_type_id')
        
        # 사용자 등록
        results = {
            'success': 0,
            'failed': 0,
            'duplicated': 0,
            'errors': []
        }
        
        for index, row in df.iterrows():
            try:
                username = str(row['username']).strip()
                password = str(row['password']).strip()
                chatbot_type_id = int(row['chatbot_type_id']) if pd.notna(row['chatbot_type_id']) else 1
                
                # 사용자명 중복 확인
                if db_manager.get_user_by_username(username):
                    results['duplicated'] += 1
                    results['errors'].append(f"행 {index+2}: '{username}' - 이미 존재하는 사용자명")
                    continue
                
                # 사용자 생성
                user_id = db_manager.create_user(username, password, chatbot_type_id)
                
                if user_id:
                    results['success'] += 1
                else:
                    results['failed'] += 1
                    results['errors'].append(f"행 {index+2}: '{username}' - 등록 실패")
                    
            except Exception as e:
                results['failed'] += 1
                results['errors'].append(f"행 {index+2}: {str(e)}")
        
        chatbot_types = chatbot_manager.get_all_chatbot_types()
        return render_template('admin/excel_upload.html', 
                             chatbot_types=chatbot_types,
                             success=f'업로드 완료! 총 {results["success"]}명 등록',
                             results=results)
        
    except Exception as e:
        chatbot_types = chatbot_manager.get_all_chatbot_types()
        return render_template('admin/excel_upload.html', 
                             chatbot_types=chatbot_types,
                             error=f'엑셀 파일 처리 중 오류가 발생했습니다: {str(e)}')

@bp.route('/export_logs')
@require_auth
def export_logs_page():
    """로그 내보내기 페이지"""
    # 통계 정보
    stats = db_manager.get_user_stats()
    total_users, active_users, total_messages, recent_users = stats
    
    # 사용자 목록 (메시지 수 포함)
    users = db_manager.get_all_users_with_stats()
    
    # 총 대화 수 계산 (user 메시지 수)
    conn = db_manager.get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM message WHERE sender = 'user'")
    total_conversations = cursor.fetchone()[0]
    conn.close()
    
    return render_template('admin/export_logs.html',
                         total_messages=total_messages,
                         total_users=total_users,
                         total_conversations=total_conversations,
                         users=users)

@bp.route('/export_all_csv')
@require_auth
def export_all_csv():
    """전체 로그 CSV 내보내기"""
    logs = db_manager.get_all_chat_logs()
    
    # CSV 생성
    output = StringIO()
    writer = csv.writer(output)
    
    # 헤더
    writer.writerow(['ID', '사용자명', '챗봇타입', '발신자', '내용', '시간'])
    
    # 데이터
    for log in logs:
        writer.writerow(log)
    
    output.seek(0)
    
    # 현재 날짜로 파일명 생성
    filename = f'chat_logs_all_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
    
    return send_file(
        BytesIO(output.getvalue().encode('utf-8-sig')),  # BOM 추가로 한글 깨짐 방지
        mimetype='text/csv',
        as_attachment=True,
        download_name=filename
    )

@bp.route('/export_all_excel')
@require_auth
def export_all_excel():
    """전체 로그 Excel 내보내기"""
    logs = db_manager.get_all_chat_logs()
    
    # DataFrame 생성
    df = pd.DataFrame(logs, columns=['ID', '사용자명', '챗봇타입', '발신자', '내용', '시간'])
    
    # Excel 파일 생성
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Chat Logs')
        
        # 컬럼 너비 조정
        worksheet = writer.sheets['Chat Logs']
        worksheet.column_dimensions['A'].width = 10
        worksheet.column_dimensions['B'].width = 15
        worksheet.column_dimensions['C'].width = 15
        worksheet.column_dimensions['D'].width = 10
        worksheet.column_dimensions['E'].width = 50
        worksheet.column_dimensions['F'].width = 20
    
    output.seek(0)
    
    # 현재 날짜로 파일명 생성
    filename = f'chat_logs_all_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
    
    return send_file(
        output,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name=filename
    )

@bp.route('/export_user_logs', methods=['POST'])
@require_auth
def export_user_logs():
    """특정 사용자 로그 내보내기"""
    user_id = int(request.form.get('user_id'))
    format_type = request.form.get('format')
    
    logs = db_manager.get_chat_logs_by_user(user_id)
    
    # 사용자명 가져오기
    username = logs[0][1] if logs else 'unknown'
    
    if format_type == 'csv':
        # CSV 생성
        output = StringIO()
        writer = csv.writer(output)
        writer.writerow(['ID', '사용자명', '챗봇타입', '발신자', '내용', '시간'])
        for log in logs:
            writer.writerow(log)
        output.seek(0)
        
        filename = f'chat_logs_{username}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        
        return send_file(
            BytesIO(output.getvalue().encode('utf-8-sig')),
            mimetype='text/csv',
            as_attachment=True,
            download_name=filename
        )
    else:  # excel
        df = pd.DataFrame(logs, columns=['ID', '사용자명', '챗봇타입', '발신자', '내용', '시간'])
        
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Chat Logs')
            worksheet = writer.sheets['Chat Logs']
            worksheet.column_dimensions['A'].width = 10
            worksheet.column_dimensions['B'].width = 15
            worksheet.column_dimensions['C'].width = 15
            worksheet.column_dimensions['D'].width = 10
            worksheet.column_dimensions['E'].width = 50
            worksheet.column_dimensions['F'].width = 20
        
        output.seek(0)
        
        filename = f'chat_logs_{username}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
        
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=filename
        )

@bp.route('/export_date_range_logs', methods=['POST'])
@require_auth
def export_date_range_logs():
    """날짜 범위 로그 내보내기"""
    start_date = request.form.get('start_date')
    end_date = request.form.get('end_date')
    format_type = request.form.get('format')
    
    logs = db_manager.get_chat_logs_by_date_range(start_date, end_date)
    
    if format_type == 'csv':
        # CSV 생성
        output = StringIO()
        writer = csv.writer(output)
        writer.writerow(['ID', '사용자명', '챗봇타입', '발신자', '내용', '시간'])
        for log in logs:
            writer.writerow(log)
        output.seek(0)
        
        filename = f'chat_logs_{start_date}_to_{end_date}.csv'
        
        return send_file(
            BytesIO(output.getvalue().encode('utf-8-sig')),
            mimetype='text/csv',
            as_attachment=True,
            download_name=filename
        )
    else:  # excel
        df = pd.DataFrame(logs, columns=['ID', '사용자명', '챗봇타입', '발신자', '내용', '시간'])
        
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Chat Logs')
            worksheet = writer.sheets['Chat Logs']
            worksheet.column_dimensions['A'].width = 10
            worksheet.column_dimensions['B'].width = 15
            worksheet.column_dimensions['C'].width = 15
            worksheet.column_dimensions['D'].width = 10
            worksheet.column_dimensions['E'].width = 50
            worksheet.column_dimensions['F'].width = 20
        
        output.seek(0)
        
        filename = f'chat_logs_{start_date}_to_{end_date}.xlsx'
        
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=filename
        )

# 동영상 관리 라우트들
@bp.route('/videos')
@require_auth
def video_management():
    """동영상 관리 페이지"""
    videos = video_manager.get_all_videos()
    video_stats = []
    
    for video in videos:
        stats = activity_log_manager.get_video_watch_stats(video[0])
        video_stats.append({
            'video': video,
            'stats': stats
        })
    
    return render_template('admin/video_management.html', 
                         videos=videos, 
                         video_stats=video_stats)

@bp.route('/videos/create', methods=['POST'])
@require_auth
def create_video():
    """동영상 생성"""
    try:
        title = request.form.get('title')
        video_url = request.form.get('video_url')
        description = request.form.get('description', '')
        
        if not title or not video_url:
            return jsonify({'success': False, 'error': '제목과 동영상 URL은 필수입니다.'})
        
        video_id = video_manager.create_video(title, video_url, description)
        return jsonify({'success': True, 'video_id': video_id})
        
    except Exception as e:
        return jsonify({'success': False, 'error': f'동영상 생성 중 오류가 발생했습니다: {str(e)}'})

@bp.route('/videos/update/<int:video_id>', methods=['POST'])
@require_auth
def update_video(video_id):
    """동영상 수정"""
    try:
        title = request.form.get('title')
        video_url = request.form.get('video_url')
        description = request.form.get('description', '')
        
        if not title or not video_url:
            return jsonify({'success': False, 'error': '제목과 동영상 URL은 필수입니다.'})
        
        success = video_manager.update_video(video_id, title, video_url, description)
        if success:
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'error': '동영상을 찾을 수 없습니다.'})
            
    except Exception as e:
        return jsonify({'success': False, 'error': f'동영상 수정 중 오류가 발생했습니다: {str(e)}'})

@bp.route('/videos/delete/<int:video_id>', methods=['POST'])
@require_auth
def delete_video(video_id):
    """동영상 삭제"""
    try:
        success = video_manager.delete_video(video_id)
        if success:
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'error': '동영상을 찾을 수 없습니다.'})
            
    except Exception as e:
        return jsonify({'success': False, 'error': f'동영상 삭제 중 오류가 발생했습니다: {str(e)}'})

@bp.route('/user/<int:user_id>/timeline')
@require_auth
def user_timeline(user_id):
    """사용자 활동 타임라인"""
    import json
    
    # 사용자 정보 조회
    conn = db_manager.get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT id, username FROM user WHERE id = ?", (user_id,))
        user = cursor.fetchone()
        if not user:
            return redirect(url_for('admin.user_management'))
    finally:
        conn.close()
    
    # 활동 타임라인 조회
    timeline = activity_log_manager.get_user_timeline(user_id, 100)
    activity_summary = activity_log_manager.get_user_activity_summary(user_id)
    
    # 메타데이터 파싱 및 유니코드 디코딩
    parsed_timeline = []
    for activity in timeline:
        parsed_activity = list(activity)
        
        # content 필드 유니코드 디코딩
        parsed_activity[2] = decode_unicode_escape(activity[2])
        
        # metadata 파싱
        if activity[3]:  # metadata가 있는 경우
            try:
                parsed_activity[3] = json.loads(activity[3])
            except (json.JSONDecodeError, TypeError):
                parsed_activity[3] = None
                
        parsed_timeline.append(parsed_activity)
    
    return render_template('admin/user_timeline.html',
                         user=user,
                         timeline=parsed_timeline,
                         activity_summary=activity_summary)

@bp.route('/user/<int:user_id>/export_timeline')
@require_auth
def export_user_timeline(user_id):
    """사용자 활동 타임라인 내보내기"""
    import json
    from datetime import datetime
    
    # 사용자 정보 조회
    conn = db_manager.get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT id, username FROM user WHERE id = ?", (user_id,))
        user = cursor.fetchone()
        if not user:
            return redirect(url_for('admin.user_management'))
    finally:
        conn.close()
    
    # 활동 타임라인 조회
    timeline = activity_log_manager.get_user_timeline(user_id, 1000)  # 더 많은 데이터
    
    # 메타데이터 파싱 및 유니코드 디코딩
    parsed_timeline = []
    for activity in timeline:
        parsed_activity = list(activity)
        
        # content 필드 유니코드 디코딩
        parsed_activity[2] = decode_unicode_escape(activity[2])
        
        # metadata 파싱
        if activity[3]:  # metadata가 있는 경우
            try:
                parsed_activity[3] = json.loads(activity[3])
            except (json.JSONDecodeError, TypeError):
                parsed_activity[3] = None
                
        parsed_timeline.append(parsed_activity)
    
    format_type = request.args.get('format', 'csv')
    
    if format_type == 'csv':
        # CSV 내보내기
        output = StringIO()
        writer = csv.writer(output)
        
        # 헤더
        writer.writerow(['시간', '활동 유형', '내용', '동영상', '시청 시간', '진행률', '응답 길이'])
        
        # 데이터
        for activity in parsed_timeline:
            metadata = activity[3] or {}
            writer.writerow([
                activity[4],  # 시간
                activity[1],  # 활동 유형
                activity[2] or '',  # 내용
                activity[6] or '',  # 동영상
                metadata.get('watch_time', ''),
                metadata.get('progress_percentage', ''),
                metadata.get('response_length', '')
            ])
        
        output.seek(0)
        response = make_response(output.getvalue().encode('utf-8-sig'))  # BOM 추가로 한글 지원
        response.headers['Content-Type'] = 'text/csv; charset=utf-8'
        response.headers['Content-Disposition'] = f'attachment; filename=user_{user[1]}_timeline_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        return response
        
    elif format_type == 'excel':
        # Excel 내보내기
        output = BytesIO()
        
        with pd.ExcelWriter(output, engine='openpyxl', options={'strings_to_numbers': False}) as writer:
            # 데이터 준비
            data = []
            for activity in parsed_timeline:
                metadata = activity[3] or {}
                data.append({
                    '시간': activity[4],
                    '활동 유형': activity[1],
                    '내용': activity[2] or '',
                    '동영상': activity[6] or '',
                    '시청 시간(초)': metadata.get('watch_time', ''),
                    '진행률(%)': metadata.get('progress_percentage', ''),
                    '응답 길이(자)': metadata.get('response_length', ''),
                    '현재 시간(초)': metadata.get('current_time', ''),
                    '총 길이(초)': metadata.get('duration', '')
                })
            
            df = pd.DataFrame(data)
            df.to_excel(writer, sheet_name='활동 타임라인', index=False)
            
            # 워크시트 스타일링
            worksheet = writer.sheets['활동 타임라인']
            worksheet.column_dimensions['A'].width = 20
            worksheet.column_dimensions['B'].width = 15
            worksheet.column_dimensions['C'].width = 30
            worksheet.column_dimensions['D'].width = 20
        
        output.seek(0)
        response = make_response(output.getvalue())
        response.headers['Content-Type'] = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        response.headers['Content-Disposition'] = f'attachment; filename=user_{user[1]}_timeline_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
        return response
    
    return redirect(url_for('admin.user_timeline', user_id=user_id))

def decode_unicode_escape(text):
    """유니코드 이스케이프 시퀀스를 한글로 변환"""
    if not text or not isinstance(text, str):
        return text
    
    try:
        # 유니코드 이스케이프 시퀀스가 포함된 경우
        if '\\u' in text:
            return text.encode().decode('unicode_escape')
        return text
    except (UnicodeDecodeError, UnicodeEncodeError):
        return text

# 비디오 구간 관리 라우트
@bp.route('/admin/videos/<int:video_id>/segments')
@require_auth
def video_segments(video_id):
    """비디오 구간 관리"""
    try:
        video = video_manager.get_video_by_id(video_id)
        if not video:
            flash('동영상을 찾을 수 없습니다.', 'error')
            return redirect(url_for('admin.video_management'))
        
        segments = video_manager.get_video_segments(video_id)
        return render_template('admin/video_segments.html', video=video, segments=segments)
    except Exception as e:
        flash(f'구간 정보를 불러오는 중 오류가 발생했습니다: {str(e)}', 'error')
        return redirect(url_for('admin.video_management'))

@bp.route('/admin/videos/<int:video_id>/segments/create', methods=['POST'])
@require_auth
def create_video_segment(video_id):
    """비디오 구간 생성"""
    try:
        segment_index = int(request.form.get('segment_index'))
        segment_name = request.form.get('segment_name')
        start_time = float(request.form.get('start_time'))
        end_time = float(request.form.get('end_time'))
        description = request.form.get('description', '')
        
        segment_id = video_manager.create_video_segment(
            video_id, segment_index, segment_name, start_time, end_time, description
        )
        
        flash('구간이 생성되었습니다.', 'success')
    except Exception as e:
        flash(f'구간 생성 중 오류가 발생했습니다: {str(e)}', 'error')
    
    return redirect(url_for('admin.video_segments', video_id=video_id))

@bp.route('/admin/videos/segments/<int:segment_id>/update', methods=['POST'])
@require_auth
def update_video_segment(segment_id):
    """비디오 구간 수정"""
    try:
        segment_name = request.form.get('segment_name')
        start_time = float(request.form.get('start_time'))
        end_time = float(request.form.get('end_time'))
        description = request.form.get('description', '')
        
        success = video_manager.update_video_segment(
            segment_id, segment_name, start_time, end_time, description
        )
        
        if success:
            flash('구간이 수정되었습니다.', 'success')
        else:
            flash('구간 수정에 실패했습니다.', 'error')
    except Exception as e:
        flash(f'구간 수정 중 오류가 발생했습니다: {str(e)}', 'error')
    
    return redirect(request.referrer or url_for('admin.video_management'))

@bp.route('/admin/videos/segments/<int:segment_id>/delete', methods=['POST'])
@require_auth
def delete_video_segment(segment_id):
    """비디오 구간 삭제"""
    try:
        success = video_manager.delete_video_segment(segment_id)
        if success:
            flash('구간이 삭제되었습니다.', 'success')
        else:
            flash('구간 삭제에 실패했습니다.', 'error')
    except Exception as e:
        flash(f'구간 삭제 중 오류가 발생했습니다: {str(e)}', 'error')
    
    return redirect(request.referrer or url_for('admin.video_management'))

@bp.route('/admin/activity_mode')
@require_auth
def activity_mode():
    """활동 모드 관리"""
    try:
        # 현재 활동 모드 확인
        conn = db_manager.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT value FROM settings WHERE key = 'activity_mode'")
        current_mode = cursor.fetchone()
        current_mode = current_mode[0] if current_mode else 'chatbot'
        
        # 질문지 목록 조회
        cursor.execute("SELECT id, question, order_index FROM qa_template ORDER BY order_index ASC")
        questions = cursor.fetchall()
        
        conn.close()
        
        return render_template('admin/activity_mode.html', 
                             current_mode=current_mode,
                             questions=questions)
    except Exception as e:
        flash(f'활동 모드 정보를 불러오는 중 오류가 발생했습니다: {str(e)}', 'error')
        return redirect(url_for('admin.dashboard'))

@bp.route('/admin/activity_mode/update', methods=['POST'])
@require_auth
def update_activity_mode():
    """활동 모드 업데이트"""
    try:
        mode = request.form.get('mode', 'chatbot')
        
        conn = db_manager.get_connection()
        cursor = conn.cursor()
        
        # 설정 업데이트 또는 생성
        cursor.execute("SELECT id FROM settings WHERE key = 'activity_mode'")
        if cursor.fetchone():
            cursor.execute("UPDATE settings SET value = ? WHERE key = 'activity_mode'", (mode,))
        else:
            cursor.execute("INSERT INTO settings (key, value) VALUES ('activity_mode', ?)", (mode,))
        
        conn.commit()
        conn.close()
        
        flash(f'활동 모드가 {mode}로 변경되었습니다.', 'success')
        return redirect(url_for('admin.activity_mode'))
    except Exception as e:
        flash(f'활동 모드 변경 중 오류가 발생했습니다: {str(e)}', 'error')
        return redirect(url_for('admin.activity_mode'))

@bp.route('/admin/activity_mode/questions', methods=['POST'])
@require_auth
def manage_questions():
    """질문 관리"""
    try:
        action = request.form.get('action')
        
        if action == 'add':
            question = request.form.get('question', '').strip()
            if question:
                conn = db_manager.get_connection()
                cursor = conn.cursor()
                
                # 다음 순서 번호 계산
                cursor.execute("SELECT MAX(order_index) FROM qa_template")
                max_order = cursor.fetchone()[0] or 0
                
                cursor.execute("INSERT INTO qa_template (question, order_index) VALUES (?, ?)", 
                              (question, max_order + 1))
                conn.commit()
                conn.close()
                
                flash('질문이 추가되었습니다.', 'success')
        
        elif action == 'delete':
            question_id = request.form.get('question_id', type=int)
            if question_id:
                conn = db_manager.get_connection()
                cursor = conn.cursor()
                cursor.execute("DELETE FROM qa_template WHERE id = ?", (question_id,))
                conn.commit()
                conn.close()
                
                flash('질문이 삭제되었습니다.', 'success')
        
        elif action == 'reorder':
            question_ids = request.form.getlist('question_ids[]')
            for i, question_id in enumerate(question_ids):
                conn = db_manager.get_connection()
                cursor = conn.cursor()
                cursor.execute("UPDATE qa_template SET order_index = ? WHERE id = ?", (i + 1, question_id))
                conn.commit()
                conn.close()
            
            flash('질문 순서가 업데이트되었습니다.', 'success')
        
        return redirect(url_for('admin.activity_mode'))
    except Exception as e:
        flash(f'질문 관리 중 오류가 발생했습니다: {str(e)}', 'error')
        return redirect(url_for('admin.activity_mode'))

@bp.route('/admin/video_analytics')
@require_auth
def video_analytics():
    """비디오 분석 대시보드"""
    try:
        # 모든 비디오와 사용자 목록 가져오기
        videos = video_manager.get_all_videos()
        users = db_manager.get_all_users_with_stats()
        
        selected_video = None
        selected_user = None
        overall_stats = None
        segment_stats = None
        navigation_analysis = None
        heatmap_data = None
        
        # 선택된 비디오가 있는 경우
        video_id = request.args.get('video_id', type=int)
        user_id = request.args.get('user_id', type=int)
        
        if video_id:
            selected_video = video_manager.get_video_by_id(video_id)
            if selected_video:
                # 전체 통계
                segment_stats_data = activity_log_manager.get_segment_statistics(video_id)
                overall_stats = segment_stats_data['overall_stats']
                segment_stats = segment_stats_data['segment_stats']
                
                # 특정 사용자 분석
                if user_id:
                    selected_user = next((user for user in users if user[0] == user_id), None)
                    if selected_user:
                        navigation_analysis = activity_log_manager.get_video_navigation_analysis(user_id, video_id)
                        continuous_heatmap = activity_log_manager.get_continuous_heatmap(user_id, video_id)
        
        return render_template('admin/video_analytics.html',
                             videos=videos,
                             users=users,
                             selected_video=selected_video,
                             selected_user=selected_user,
                             overall_stats=overall_stats,
                             segment_stats=segment_stats,
                             navigation_analysis=navigation_analysis,
                             continuous_heatmap=continuous_heatmap)
    except Exception as e:
        flash(f'분석 데이터를 불러오는 중 오류가 발생했습니다: {str(e)}', 'error')
        return redirect(url_for('admin.video_management'))
