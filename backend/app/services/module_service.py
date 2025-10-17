"""
모듈 관리 서비스
모듈 및 스캐폴딩 관련 비즈니스 로직
"""
from app import db
from app.models.module import Module
from app.models.scaffolding import Scaffolding, ScaffoldingResponse
from app.models.event_log import EventLog
from app.services.learning_progress_service import LearningProgressService
from app.utils.youtube import extract_youtube_id, get_youtube_thumbnail_url, is_valid_youtube_url
from sqlalchemy.orm import joinedload
from typing import List, Optional, Tuple
import logging
import json

logger = logging.getLogger(__name__)


class ModuleService:
    """모듈 관리 서비스"""
    
    @staticmethod
    def get_all_modules() -> List[Module]:
        """모든 활성화되고 학습 가능한 모듈 조회 (일반 사용자용)"""
        try:
            return Module.query.filter_by(
                is_active=True, 
                learning_enabled=True
            ).order_by(Module.order_index).all()
        except Exception as e:
            logger.error(f"Get all modules error: {str(e)}")
            return []
    
    @staticmethod
    def get_all_modules_for_admin() -> List[Module]:
        """관리자용: 모든 모듈 조회 (비활성 포함)"""
        try:
            return Module.query.order_by(Module.order_index, Module.id).all()
        except Exception as e:
            logger.error(f"Get all modules for admin error: {str(e)}")
            return []
    
    @staticmethod
    def get_module_with_scaffoldings(module_id: int, user_id: int) -> Tuple[Optional[dict], Optional[str]]:
        """
        모듈 및 스캐폴딩 정보 조회 (N+1 쿼리 최적화)
        
        Args:
            module_id: 모듈 ID
            user_id: 사용자 ID
            
        Returns:
            (module_data, error): 성공 시 모듈 데이터, 실패 시 None과 에러 메시지
        """
        try:
            # 모듈 조회
            module = Module.query.get(module_id)
            
            if not module:
                return None, '모듈을 찾을 수 없습니다'
            
            module_data = module.to_dict()
            
            # 학습 진행 상황 초기화
            try:
                LearningProgressService.mark_started(user_id, module_id)
                progress_state = LearningProgressService.get_progress(user_id, module_id)
            except Exception as e:
                logger.error(f"Failed to update learning progress for user {user_id}, module {module_id}: {str(e)}")
                progress_state = None
            
            # 스캐폴딩 포함
            if module.scaffolding_mode in ['prompt', 'both']:
                scaffoldings = Scaffolding.query.filter_by(
                    module_id=module_id, 
                    is_active=True
                ).order_by(Scaffolding.order_index).all()
                
                if scaffoldings:
                    scaffolding_ids = [s.id for s in scaffoldings]
                    
                    responses = ScaffoldingResponse.query.filter(
                        ScaffoldingResponse.scaffolding_id.in_(scaffolding_ids),
                        ScaffoldingResponse.user_id == user_id
                    ).all()
                    
                    response_map = {r.scaffolding_id: r for r in responses}
                    
                    module_data['scaffoldings'] = []
                    for scaffolding in scaffoldings:
                        scaffolding_data = scaffolding.to_dict()
                        if scaffolding.id in response_map:
                            scaffolding_data['user_response'] = response_map[scaffolding.id].to_dict()
                        module_data['scaffoldings'].append(scaffolding_data)
                    
                    total_scaffoldings = len(scaffoldings)
                    completed_scaffoldings = len(response_map)
                    scaffolding_completed = total_scaffoldings > 0 and completed_scaffoldings == total_scaffoldings
                else:
                    module_data['scaffoldings'] = []
                    total_scaffoldings = 0
                    completed_scaffoldings = 0
                    scaffolding_completed = False
            else:
                total_scaffoldings = 0
                completed_scaffoldings = 0
                scaffolding_completed = True  # 스캐폴딩이 없으면 완료로 간주
            
            default_progress = {
                'status': 'not_started',
                'started_at': None,
                'last_activity_at': None,
                'completed_at': None,
                'survey_completed': False,
                'survey_completed_at': None,
            }
            merged_progress = {**default_progress, **(progress_state or {})}
            merged_progress.update({
                'total': total_scaffoldings,
                'completed': completed_scaffoldings,
                'is_completed': scaffolding_completed
            })
            module_data['learning_progress'] = merged_progress
            
            return module_data, None
            
        except Exception as e:
            logger.error(f"Get module with scaffoldings error: {str(e)}")
            return None, '모듈 정보 조회 중 오류가 발생했습니다'
    
    @staticmethod
    def create_module(title: str, youtube_url: str, youtube_id: Optional[str] = None, **kwargs) -> Tuple[Optional[Module], Optional[str]]:
        """
        모듈 생성
        
        Args:
            title: 제목
            youtube_url: YouTube URL
            youtube_id: YouTube ID (선택사항, 자동 추출됨)
            **kwargs: 추가 옵션 (description, duration, thumbnail_url, scaffolding_mode, order_index)
            
        Returns:
            (module, error): 성공 시 모듈 객체, 실패 시 None과 에러 메시지
        """
        try:
            # YouTube URL 유효성 검사
            if not is_valid_youtube_url(youtube_url):
                return None, '유효하지 않은 YouTube URL입니다'
            
            # YouTube ID 자동 추출 (제공되지 않은 경우)
            if not youtube_id:
                youtube_id = extract_youtube_id(youtube_url)
                if not youtube_id:
                    return None, 'YouTube URL에서 비디오 ID를 추출할 수 없습니다'
            
            # YouTube 썸네일 URL 자동 생성 (제공되지 않은 경우)
            thumbnail_url = kwargs.get('thumbnail_url')
            if not thumbnail_url and youtube_id:
                thumbnail_url = get_youtube_thumbnail_url(youtube_id)
            
            module = Module(
                title=title,
                youtube_url=youtube_url,
                youtube_id=youtube_id,
                description=kwargs.get('description'),
                duration=kwargs.get('duration'),
                thumbnail_url=thumbnail_url,
                scaffolding_mode=kwargs.get('scaffolding_mode', 'none'),
                order_index=kwargs.get('order_index', 0),
                survey_url=kwargs.get('survey_url'),
                intro_text=kwargs.get('intro_text')
            )
            
            db.session.add(module)
            db.session.commit()
            
            logger.info(f"Module created: {module.id} - {title} (YouTube ID: {youtube_id})")
            return module, None
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Create module error: {str(e)}")
            return None, '모듈 생성 중 오류가 발생했습니다'
    
    @staticmethod
    def update_module(module_id: int, **kwargs) -> Tuple[Optional[Module], Optional[str]]:
        """
        모듈 업데이트
        
        Args:
            module_id: 모듈 ID
            **kwargs: 업데이트할 필드
            
        Returns:
            (module, error): 성공 시 모듈 객체, 실패 시 None과 에러 메시지
        """
        try:
            module = Module.query.get(module_id)
            
            if not module:
                return None, '모듈을 찾을 수 없습니다'
            
            # scaffolding_mode 검증
            if 'scaffolding_mode' in kwargs:
                valid_modes = ['none', 'prompt', 'chat']
                if kwargs['scaffolding_mode'] not in valid_modes:
                    return None, f'유효하지 않은 학습 모드입니다. 허용된 값: {", ".join(valid_modes)}'
            
            # 업데이트 가능한 필드
            allowed_fields = ['title', 'description', 'scaffolding_mode', 'is_active', 'learning_enabled', 'order_index', 'survey_url', 'intro_text']
            for field in allowed_fields:
                if field in kwargs:
                    logger.info(f"Updating field {field}: {kwargs[field]}")
                    setattr(module, field, kwargs[field])
            
            logger.info(f"Module before commit - survey_url: {module.survey_url}, intro_text: {module.intro_text}")
            db.session.commit()
            logger.info(f"Module after commit - survey_url: {module.survey_url}, intro_text: {module.intro_text}")
            
            logger.info(f"Module updated: {module_id}")
            return module, None
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Update module error: {str(e)}")
            return None, '모듈 업데이트 중 오류가 발생했습니다'
    
    @staticmethod
    def delete_module(module_id: int) -> Tuple[bool, Optional[str]]:
        """
        모듈 삭제
        
        Args:
            module_id: 모듈 ID
            
        Returns:
            (success, error): 성공 여부와 에러 메시지
        """
        try:
            module = Module.query.get(module_id)
            
            if not module:
                return False, '모듈을 찾을 수 없습니다'
            
            db.session.delete(module)
            db.session.commit()
            
            logger.info(f"Module deleted: {module_id}")
            return True, None
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Delete module error: {str(e)}")
            return False, '모듈 삭제 중 오류가 발생했습니다'
    
    @staticmethod
    def log_module_event(user_id: int, module_id: int, event_type: str, 
                       event_data: dict, ip_address: str, user_agent: str) -> None:
        """
        모듈 이벤트 로그 기록
        
        Args:
            user_id: 사용자 ID
            module_id: 모듈 ID
            event_type: 이벤트 타입
            event_data: 이벤트 데이터
            ip_address: IP 주소
            user_agent: User Agent
        """
        try:
            event_log = EventLog(
                user_id=user_id,
                module_id=module_id,
                event_type=event_type,
                event_data=json.dumps(event_data),
                ip_address=ip_address,
                user_agent=user_agent
            )
            db.session.add(event_log)
            db.session.commit()
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Log module event error: {str(e)}")
            return

        if module_id:
            try:
                LearningProgressService.mark_activity(user_id, module_id)
            except Exception as e:
                logger.error(f"Failed to mark learning activity for user {user_id}, module {module_id}: {str(e)}")




