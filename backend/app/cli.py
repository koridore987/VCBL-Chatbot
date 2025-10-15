"""
CLI 도구
데이터베이스 마이그레이션 및 관리 작업을 위한 명령줄 도구
"""
import click
import os
import sys
from flask import Flask
from flask_migrate import Migrate, upgrade, downgrade, current, history
from sqlalchemy import text
from app import create_app, db


@click.group()
def cli():
    """VCBL Chatbot CLI 도구"""
    pass


@cli.command()
@click.option('--message', '-m', help='마이그레이션 메시지')
def makemigrations(message):
    """새로운 마이그레이션 파일 생성"""
    if not message:
        message = click.prompt('마이그레이션 메시지를 입력하세요')
    
    app = create_app()
    with app.app_context():
        from flask_migrate import revision
        revision(message=message)


@cli.command()
def migrate():
    """데이터베이스 마이그레이션 실행"""
    app = create_app()
    with app.app_context():
        upgrade()


@cli.command()
@click.option('--revision', help='되돌릴 리비전 ID')
def rollback(revision):
    """마이그레이션 되돌리기"""
    app = create_app()
    with app.app_context():
        if revision:
            downgrade(revision)
        else:
            # 이전 리비전으로 되돌리기
            downgrade()


@cli.command()
def status():
    """마이그레이션 상태 확인"""
    app = create_app()
    with app.app_context():
        current_rev = current()
        click.echo(f"현재 리비전: {current_rev}")
        
        history_list = history()
        click.echo("\n마이그레이션 히스토리:")
        for rev in history_list:
            click.echo(f"  {rev}")


@cli.command()
def init_db():
    """데이터베이스 초기화"""
    app = create_app()
    with app.app_context():
        db.create_all()
        click.echo("데이터베이스가 초기화되었습니다.")


@cli.command()
@click.option('--confirm', is_flag=True, help='확인 없이 실행')
def reset_db(confirm):
    """데이터베이스 리셋 (주의: 모든 데이터가 삭제됩니다)"""
    if not confirm:
        if not click.confirm('정말로 데이터베이스를 리셋하시겠습니까? 모든 데이터가 삭제됩니다.'):
            click.echo('취소되었습니다.')
            return
    
    app = create_app()
    with app.app_context():
        db.drop_all()
        db.create_all()
        click.echo("데이터베이스가 리셋되었습니다.")


@cli.command()
def health():
    """애플리케이션 상태 확인"""
    app = create_app()
    with app.app_context():
        try:
            # 데이터베이스 연결 테스트
            db.session.execute(text('SELECT 1'))
            click.echo("✅ 데이터베이스 연결: 정상")
        except Exception as e:
            click.echo(f"❌ 데이터베이스 연결 오류: {e}")
            sys.exit(1)
        
        # 환경 변수 확인
        required_vars = ['SECRET_KEY', 'OPENAI_API_KEY']
        missing_vars = []
        
        for var in required_vars:
            if not os.getenv(var):
                missing_vars.append(var)
        
        if missing_vars:
            click.echo(f"❌ 누락된 환경 변수: {', '.join(missing_vars)}")
            sys.exit(1)
        else:
            click.echo("✅ 환경 변수: 정상")
        
        click.echo("✅ 애플리케이션 상태: 정상")


@cli.command('init-admin')
@click.option('--student-id', help='관리자 학번 (환경 변수 ADMIN_STUDENT_ID 또는 기본값 사용)')
@click.option('--name', help='관리자 이름 (환경 변수 ADMIN_NAME 또는 기본값 사용)')
@click.option('--password', help='관리자 비밀번호 (환경 변수 ADMIN_PASSWORD 또는 기본값 사용)')
def init_admin(student_id, name, password):
    """
    초기 Super 관리자 계정 생성
    
    이 명령은 Super 관리자가 없을 때만 작동합니다.
    환경 변수 또는 명령줄 옵션으로 계정 정보를 제공할 수 있습니다.
    
    환경 변수:
        ADMIN_STUDENT_ID - 관리자 학번
        ADMIN_NAME - 관리자 이름
        ADMIN_PASSWORD - 관리자 비밀번호
    
    사용 예시:
        flask init-admin
        flask init-admin --student-id 2024000001 --name "관리자" --password "SecurePass123!"
    """
    app = create_app()
    
    with app.app_context():
        from app.models.user import User
        from app import bcrypt
        
        # Super 관리자가 이미 존재하는지 확인
        existing_super = User.query.filter_by(role='super').first()
        
        if existing_super:
            click.echo(f"✓ Super 관리자가 이미 존재합니다: {existing_super.student_id} ({existing_super.name})")
            click.echo("Super 관리자는 시스템에 하나만 존재할 수 있습니다.")
            sys.exit(0)
        
        # 관리자 정보 결정 (우선순위: CLI 옵션 > 환경 변수 > 기본값)
        # 학번: 10자리 정수, 관리자 규칙상 9999로 시작
        raw_student_id = student_id or os.getenv('ADMIN_STUDENT_ID') or '9999000001'
        try:
            admin_student_id = int(raw_student_id)
        except ValueError:
            click.echo("❌ 관리자 학번은 10자리 정수여야 합니다.")
            sys.exit(1)
        if len(str(admin_student_id)) != 10 or not str(admin_student_id).startswith('9999'):
            click.echo("❌ 관리자 학번은 10자리이며 9999로 시작해야 합니다 (예: 9999000001).")
            sys.exit(1)

        admin_name = name or os.getenv('ADMIN_NAME', 'Super Administrator')

        # 비밀번호: 환경 변수 또는 CLI 옵션으로 명시적으로 제공
        env_password = os.getenv('ADMIN_PASSWORD')
        if password:
            admin_password = password
        elif env_password:
            admin_password = env_password
        else:
            click.echo("❌ 관리자 비밀번호가 설정되지 않았습니다. ADMIN_PASSWORD 환경 변수 또는 --password 옵션을 사용하세요.")
            sys.exit(1)

        click.echo(f"Super 관리자 계정을 생성합니다: {admin_student_id}")
        
        # 비밀번호 해시 생성
        password_hash = bcrypt.generate_password_hash(admin_password).decode('utf-8')
        
        # Super 관리자 생성
        admin = User(
            student_id=admin_student_id,
            password_hash=password_hash,
            name=admin_name,
            role='super',
            is_active=True
        )
        
        db.session.add(admin)
        db.session.commit()
        
        click.echo("")
        click.echo("=" * 60)
        click.echo("✅ Super 관리자가 생성되었습니다!")
        click.echo("=" * 60)
        click.echo(f"학번: {admin.student_id}")
        click.echo(f"이름: {admin.name}")
        click.echo(f"역할: Super Administrator")
        click.echo("=" * 60)
        click.echo("")
        click.echo("📝 주의사항:")
        click.echo("  • 이 계정의 권한은 절대 변경할 수 없습니다.")
        click.echo("  • 이 계정은 비활성화할 수 없습니다.")
        click.echo("  • 비밀번호는 본인만 변경 가능합니다.")
        click.echo("")
        sys.exit(0)


if __name__ == '__main__':
    cli()
