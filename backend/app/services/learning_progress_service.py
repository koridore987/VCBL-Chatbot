from datetime import datetime
from typing import Dict, List, Optional, Tuple

from sqlalchemy import func

from app import db
from app.models.learning_progress import LearningProgress
from app.models.user import User
from app.models.video import Video


class LearningProgressService:
  """사용자별 학습 진행 상황 관리 서비스"""

  @staticmethod
  def _get_progress(user_id: int, video_id: int) -> Optional[LearningProgress]:
    return LearningProgress.query.filter_by(user_id=user_id, video_id=video_id).first()

  @staticmethod
  def _get_or_create(user_id: int, video_id: int) -> LearningProgress:
    progress = LearningProgressService._get_progress(user_id, video_id)

    if progress:
      return progress

    progress = LearningProgress(user_id=user_id, video_id=video_id, status='not_started')
    db.session.add(progress)
    db.session.commit()
    return progress

  @staticmethod
  def mark_started(user_id: int, video_id: int) -> None:
    """학습 시작 기록"""
    now = datetime.utcnow()
    progress = LearningProgressService._get_or_create(user_id, video_id)

    try:
      if not progress.started_at:
        progress.started_at = now

      progress.last_activity_at = now
      if progress.status == 'not_started':
        progress.status = 'in_progress'

      db.session.commit()
    except Exception:
      db.session.rollback()
      raise

  @staticmethod
  def mark_activity(user_id: int, video_id: int) -> None:
    """진행 중 활동 기록"""
    now = datetime.utcnow()
    progress = LearningProgressService._get_or_create(user_id, video_id)

    try:
      if not progress.started_at:
        progress.started_at = now

      progress.last_activity_at = now
      if progress.status == 'not_started':
        progress.status = 'in_progress'

      db.session.commit()
    except Exception:
      db.session.rollback()
      raise

  @staticmethod
  def mark_survey_completed(user_id: int, video_id: int) -> LearningProgress:
    """설문 완료 상태 기록"""
    now = datetime.utcnow()
    progress = LearningProgressService._get_or_create(user_id, video_id)

    try:
      if not progress.started_at:
        progress.started_at = now

      progress.last_activity_at = now
      progress.survey_completed = True
      progress.survey_completed_at = now
      if progress.status == 'not_started':
        progress.status = 'in_progress'

      db.session.commit()
      return progress
    except Exception:
      db.session.rollback()
      raise

  @staticmethod
  def mark_completed(user_id: int, video_id: int) -> LearningProgress:
    """학습 완료 처리"""
    now = datetime.utcnow()
    progress = LearningProgressService._get_or_create(user_id, video_id)

    try:
      if not progress.started_at:
        progress.started_at = now

      progress.status = 'completed'
      progress.last_activity_at = now
      progress.completed_at = now
      db.session.commit()
      return progress
    except Exception:
      db.session.rollback()
      raise

  @staticmethod
  def get_progress_map_for_user(user_id: int) -> Dict[int, dict]:
    """사용자별 비디오 진행 상황"""
    entries = LearningProgress.query.filter_by(user_id=user_id).all()
    return {entry.video_id: entry.to_dict() for entry in entries}

  @staticmethod
  def get_progress(user_id: int, video_id: int) -> Optional[dict]:
    progress = LearningProgressService._get_progress(user_id, video_id)
    return progress.to_dict() if progress else None

  @staticmethod
  def get_status_counts() -> Dict[str, int]:
    rows = (
      db.session.query(LearningProgress.status, func.count(LearningProgress.id))
      .group_by(LearningProgress.status)
      .all()
    )
    return {status: count for status, count in rows}

  @staticmethod
  def get_recent_progress(limit: int = 20) -> List[dict]:
    """최근 업데이트된 학습 진행 내역"""
    rows = (
      db.session.query(LearningProgress, User, Video)
      .join(User, LearningProgress.user_id == User.id)
      .join(Video, LearningProgress.video_id == Video.id)
      .order_by(LearningProgress.updated_at.desc())
      .limit(limit)
      .all()
    )

    results = []
    for progress, user, video in rows:
      progress_dict = progress.to_dict()
      progress_dict['user'] = {'id': user.id, 'name': user.name, 'student_id': user.student_id}
      progress_dict['video'] = {'id': video.id, 'title': video.title}
      results.append(progress_dict)

    return results

  @staticmethod
  def get_user_progress_summary(user_id: int) -> dict:
    """사용자별 진행 요약"""
    total = LearningProgress.query.filter_by(user_id=user_id).count()
    completed = LearningProgress.query.filter_by(user_id=user_id, status='completed').count()
    in_progress = LearningProgress.query.filter_by(user_id=user_id, status='in_progress').count()
    latest = (
      LearningProgress.query.filter_by(user_id=user_id)
      .order_by(LearningProgress.updated_at.desc())
      .first()
    )

    return {
      'total_tracked': total,
      'completed': completed,
      'in_progress': in_progress,
      'latest_activity_at': latest.updated_at.isoformat() if latest else None,
      'latest_video_id': latest.video_id if latest else None,
    }
