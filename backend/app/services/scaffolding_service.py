"""
스캐폴딩 관리 서비스
스캐폴딩 및 응답 관련 비즈니스 로직
"""
from app import db
from app.models.scaffolding import Scaffolding, ScaffoldingResponse
from typing import Optional, Tuple
import logging

logger = logging.getLogger(__name__)


class ScaffoldingService:
    """스캐폴딩 관리 서비스"""
    
    @staticmethod
    def create_scaffolding(video_id: int, title: str, prompt_text: str, 
                          order_index: int = 0) -> Tuple[Optional[Scaffolding], Optional[str]]:
        """
        스캐폴딩 생성
        
        Args:
            video_id: 비디오 ID
            title: 제목
            prompt_text: 프롬프트 텍스트
            order_index: 정렬 순서
            
        Returns:
            (scaffolding, error): 성공 시 스캐폴딩 객체, 실패 시 None과 에러 메시지
        """
        try:
            scaffolding = Scaffolding(
                video_id=video_id,
                title=title,
                prompt_text=prompt_text,
                order_index=order_index
            )
            
            db.session.add(scaffolding)
            db.session.commit()
            
            logger.info(f"Scaffolding created: {scaffolding.id} for video {video_id}")
            return scaffolding, None
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Create scaffolding error: {str(e)}")
            return None, '스캐폴딩 생성 중 오류가 발생했습니다'
    
    @staticmethod
    def update_scaffolding(scaffolding_id: int, **kwargs) -> Tuple[Optional[Scaffolding], Optional[str]]:
        """
        스캐폴딩 업데이트
        
        Args:
            scaffolding_id: 스캐폴딩 ID
            **kwargs: 업데이트할 필드
            
        Returns:
            (scaffolding, error): 성공 시 스캐폴딩 객체, 실패 시 None과 에러 메시지
        """
        try:
            scaffolding = Scaffolding.query.get(scaffolding_id)
            
            if not scaffolding:
                return None, '스캐폴딩을 찾을 수 없습니다'
            
            # 업데이트 가능한 필드
            allowed_fields = ['title', 'prompt_text', 'order_index', 'is_active']
            for field in allowed_fields:
                if field in kwargs:
                    setattr(scaffolding, field, kwargs[field])
            
            db.session.commit()
            
            logger.info(f"Scaffolding updated: {scaffolding_id}")
            return scaffolding, None
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Update scaffolding error: {str(e)}")
            return None, '스캐폴딩 업데이트 중 오류가 발생했습니다'
    
    @staticmethod
    def delete_scaffolding(scaffolding_id: int) -> Tuple[bool, Optional[str]]:
        """
        스캐폴딩 삭제
        
        Args:
            scaffolding_id: 스캐폴딩 ID
            
        Returns:
            (success, error): 성공 여부와 에러 메시지
        """
        try:
            scaffolding = Scaffolding.query.get(scaffolding_id)
            
            if not scaffolding:
                return False, '스캐폴딩을 찾을 수 없습니다'
            
            db.session.delete(scaffolding)
            db.session.commit()
            
            logger.info(f"Scaffolding deleted: {scaffolding_id}")
            return True, None
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Delete scaffolding error: {str(e)}")
            return False, '스캐폴딩 삭제 중 오류가 발생했습니다'
    
    @staticmethod
    def save_response(scaffolding_id: int, video_id: int, user_id: int, 
                     response_text: str) -> Tuple[bool, Optional[str]]:
        """
        스캐폴딩 응답 저장
        
        Args:
            scaffolding_id: 스캐폴딩 ID
            video_id: 비디오 ID
            user_id: 사용자 ID
            response_text: 응답 텍스트
            
        Returns:
            (success, error): 성공 여부와 에러 메시지
        """
        try:
            scaffolding = Scaffolding.query.get(scaffolding_id)
            
            if not scaffolding or scaffolding.video_id != video_id:
                return False, '스캐폴딩을 찾을 수 없습니다'
            
            # 기존 응답 확인
            existing_response = ScaffoldingResponse.query.filter_by(
                scaffolding_id=scaffolding_id,
                user_id=user_id
            ).first()
            
            if existing_response:
                existing_response.response_text = response_text
                logger.info(f"Scaffolding response updated: {existing_response.id}")
            else:
                new_response = ScaffoldingResponse(
                    scaffolding_id=scaffolding_id,
                    user_id=user_id,
                    response_text=response_text
                )
                db.session.add(new_response)
                logger.info(f"Scaffolding response created for user {user_id}")
            
            db.session.commit()
            return True, None
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Save scaffolding response error: {str(e)}")
            return False, '응답 저장 중 오류가 발생했습니다'
    
    @staticmethod
    def save_bulk_responses(video_id: int, user_id: int, 
                           responses: list) -> Tuple[bool, Optional[str]]:
        """
        여러 스캐폴딩 응답 일괄 저장
        
        Args:
            video_id: 비디오 ID
            user_id: 사용자 ID
            responses: 응답 리스트 [{'scaffolding_id': int, 'response_text': str}, ...]
            
        Returns:
            (success, error): 성공 여부와 에러 메시지
        """
        try:
            # 모든 스캐폴딩이 해당 비디오에 속하는지 확인
            scaffolding_ids = [r['scaffolding_id'] for r in responses]
            scaffoldings = Scaffolding.query.filter(
                Scaffolding.id.in_(scaffolding_ids),
                Scaffolding.video_id == video_id
            ).all()
            
            if len(scaffoldings) != len(scaffolding_ids):
                return False, '일부 스캐폴딩을 찾을 수 없습니다'
            
            # 각 응답 저장
            for response_data in responses:
                scaffolding_id = response_data['scaffolding_id']
                response_text = response_data['response_text']
                
                # 기존 응답 확인
                existing_response = ScaffoldingResponse.query.filter_by(
                    scaffolding_id=scaffolding_id,
                    user_id=user_id
                ).first()
                
                if existing_response:
                    existing_response.response_text = response_text
                else:
                    new_response = ScaffoldingResponse(
                        scaffolding_id=scaffolding_id,
                        user_id=user_id,
                        response_text=response_text
                    )
                    db.session.add(new_response)
            
            db.session.commit()
            logger.info(f"Bulk scaffolding responses saved for user {user_id}, video {video_id}")
            return True, None
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Save bulk scaffolding responses error: {str(e)}")
            return False, '응답 저장 중 오류가 발생했습니다'

