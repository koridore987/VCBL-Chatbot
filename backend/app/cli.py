"""
CLI 도구
데이터베이스 마이그레이션 및 관리 작업을 위한 명령줄 도구
"""
import click
import os
import sys
from flask import Flask
from flask_migrate import Migrate, upgrade, downgrade, current, history
from app import create_app
from app.models import db


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
            db.session.execute('SELECT 1')
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


if __name__ == '__main__':
    cli()
