"""
비디오 관리 서비스
비디오 및 스캐폴딩 관련 비즈니스 로직
"""
from app import db
from app.models.video import Video
from app.models.scaffolding import Scaffolding, ScaffoldingResponse
from app.models.event_log import EventLog
from sqlalchemy.orm import joinedload
from typing import List, Optional, Tuple
import logging
import json

logger = logging.getLogger(__name__)


class VideoService:
    """비디오 관리 서비스"""
    
    @staticmethod
    def get_all_videos() -> List[Video]:
        """모든 활성화되고 학습 가능한 비디오 조회 (일반 사용자용)"""
        try:
            return Video.query.filter_by(
                is_active=True, 
                learning_enabled=True
            ).order_by(Video.order_index).all()
        except Exception as e:
            logger.error(f"Get all videos error: {str(e)}")
            return []
    
    @staticmethod
    def get_all_videos_for_admin() -> List[Video]:
        """관리자용: 모든 비디오 조회 (비활성 포함)"""
        try:
            return Video.query.order_by(Video.order_index, Video.id).all()
        except Exception as e:
            logger.error(f"Get all videos for admin error: {str(e)}")
            return []
    
    @staticmethod
    def get_video_with_scaffoldings(video_id: int, user_id: int) -> Tuple[Optional[dict], Optional[str]]:
        """
        비디오 및 스캐폴딩 정보 조회 (N+1 쿼리 최적화)
        
        Args:
            video_id: 비디오 ID
            user_id: 사용자 ID
            
        Returns:
            (video_data, error): 성공 시 비디오 데이터, 실패 시 None과 에러 메시지
        """
        try:
            # 비디오 조회
            video = Video.query.get(video_id)
            
            if not video:
                return None, '비디오를 찾을 수 없습니다'
            
            video_data = video.to_dict()
            
            # 스캐폴딩 포함
            if video.scaffolding_mode in ['prompt', 'both']:
                # 활성 스캐폴딩 모두 조회 (1번 쿼리)
                scaffoldings = Scaffolding.query.filter_by(
                    video_id=video_id, 
                    is_active=True
                ).order_by(Scaffolding.order_index).all()
                
                if scaffoldings:
                    # 모든 스캐폴딩의 ID 수집
                    scaffolding_ids = [s.id for s in scaffoldings]
                    
                    # 해당 사용자의 모든 응답을 한 번에 조회 (1번 쿼리)
                    responses = ScaffoldingResponse.query.filter(
                        ScaffoldingResponse.scaffolding_id.in_(scaffolding_ids),
                        ScaffoldingResponse.user_id == user_id
                    ).all()
                    
                    # 응답을 scaffolding_id로 매핑
                    response_map = {r.scaffolding_id: r for r in responses}
                    
                    # 스캐폴딩 데이터 구성 (메모리에서 처리)
                    video_data['scaffoldings'] = []
                    for scaffolding in scaffoldings:
                        scaffolding_data = scaffolding.to_dict()
                        
                        # 매핑에서 응답 찾기
                        if scaffolding.id in response_map:
                            scaffolding_data['user_response'] = response_map[scaffolding.id].to_dict()
                        
                        video_data['scaffoldings'].append(scaffolding_data)
                    
                    # 학습 진행률 계산
                    total_scaffoldings = len(scaffoldings)
                    completed_scaffoldings = len(response_map)
                    video_data['learning_progress'] = {
                        'total': total_scaffoldings,
                        'completed': completed_scaffoldings,
                        'is_completed': total_scaffoldings > 0 and completed_scaffoldings == total_scaffoldings
                    }
                else:
                    video_data['scaffoldings'] = []
                    video_data['learning_progress'] = {
                        'total': 0,
                        'completed': 0,
                        'is_completed': False
                    }
            else:
                # 스캐폴딩이 없는 경우 (chat only 또는 none)
                video_data['learning_progress'] = {
                    'total': 0,
                    'completed': 0,
                    'is_completed': True  # 스캐폴딩이 없으면 완료로 간주
                }
            
            return video_data, None
            
        except Exception as e:
            logger.error(f"Get video with scaffoldings error: {str(e)}")
            return None, '비디오 정보 조회 중 오류가 발생했습니다'
    
    @staticmethod
    def create_video(title: str, youtube_url: str, youtube_id: str, **kwargs) -> Tuple[Optional[Video], Optional[str]]:
        """
        비디오 생성
        
        Args:
            title: 제목
            youtube_url: YouTube URL
            youtube_id: YouTube ID
            **kwargs: 추가 옵션 (description, duration, thumbnail_url, scaffolding_mode, order_index)
            
        Returns:
            (video, error): 성공 시 비디오 객체, 실패 시 None과 에러 메시지
        """
        try:
            # YouTube 썸네일 URL 자동 생성 (제공되지 않은 경우)
            thumbnail_url = kwargs.get('thumbnail_url')
            if not thumbnail_url and youtube_id:
                thumbnail_url = f"https://img.youtube.com/vi/{youtube_id}/maxresdefault.jpg"
            
            video = Video(
                title=title,
                youtube_url=youtube_url,
                youtube_id=youtube_id,
                description=kwargs.get('description'),
                duration=kwargs.get('duration'),
                thumbnail_url=thumbnail_url,
                scaffolding_mode=kwargs.get('scaffolding_mode', 'both'),
                order_index=kwargs.get('order_index', 0)
            )
            
            db.session.add(video)
            db.session.commit()
            
            logger.info(f"Video created: {video.id} - {title}")
            return video, None
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Create video error: {str(e)}")
            return None, '비디오 생성 중 오류가 발생했습니다'
    
    @staticmethod
    def update_video(video_id: int, **kwargs) -> Tuple[Optional[Video], Optional[str]]:
        """
        비디오 업데이트
        
        Args:
            video_id: 비디오 ID
            **kwargs: 업데이트할 필드
            
        Returns:
            (video, error): 성공 시 비디오 객체, 실패 시 None과 에러 메시지
        """
        try:
            video = Video.query.get(video_id)
            
            if not video:
                return None, '비디오를 찾을 수 없습니다'
            
            # 업데이트 가능한 필드
            allowed_fields = ['title', 'description', 'scaffolding_mode', 'is_active', 'learning_enabled', 'order_index', 'survey_url']
            for field in allowed_fields:
                if field in kwargs:
                    setattr(video, field, kwargs[field])
            
            db.session.commit()
            
            logger.info(f"Video updated: {video_id}")
            return video, None
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Update video error: {str(e)}")
            return None, '비디오 업데이트 중 오류가 발생했습니다'
    
    @staticmethod
    def delete_video(video_id: int) -> Tuple[bool, Optional[str]]:
        """
        비디오 삭제
        
        Args:
            video_id: 비디오 ID
            
        Returns:
            (success, error): 성공 여부와 에러 메시지
        """
        try:
            video = Video.query.get(video_id)
            
            if not video:
                return False, '비디오를 찾을 수 없습니다'
            
            db.session.delete(video)
            db.session.commit()
            
            logger.info(f"Video deleted: {video_id}")
            return True, None
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Delete video error: {str(e)}")
            return False, '비디오 삭제 중 오류가 발생했습니다'
    
    @staticmethod
    def log_video_event(user_id: int, video_id: int, event_type: str, 
                       event_data: dict, ip_address: str, user_agent: str) -> None:
        """
        비디오 이벤트 로그 기록
        
        Args:
            user_id: 사용자 ID
            video_id: 비디오 ID
            event_type: 이벤트 타입
            event_data: 이벤트 데이터
            ip_address: IP 주소
            user_agent: User Agent
        """
        try:
            event_log = EventLog(
                user_id=user_id,
                video_id=video_id,
                event_type=event_type,
                event_data=json.dumps(event_data),
                ip_address=ip_address,
                user_agent=user_agent
            )
            db.session.add(event_log)
            db.session.commit()
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Log video event error: {str(e)}")

