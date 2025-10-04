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
import hashlib
from app import config

# 블루프린트 생성
bp = Blueprint('admin', __name__, url_prefix='/admin')

# 매니저 인스턴스
db_manager = DatabaseManager()
admin_manager = AdminManager()
chatbot_manager = ChatbotTypeManager()

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

@bp.route('/create_admin', methods=['POST'])
@require_super
def create_admin():
    """새 관리자 생성 (Super 권한 필요)"""
    username = request.form.get('username', '').strip()
    password = request.form.get('password', '').strip()
    role = request.form.get('role', 'admin').strip()
    
    if not username or not password:
        return redirect(url_for('admin.admin_management'))
    
    success = admin_manager.create_admin(username, password, role)
    if success:
        return redirect(url_for('admin.admin_management'))
    else:
        return redirect(url_for('admin.admin_management'))

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
