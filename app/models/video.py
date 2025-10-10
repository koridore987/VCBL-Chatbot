"""
동영상 관리 모델
"""
import sqlite3
import re
from typing import List, Tuple, Optional
from datetime import datetime
from app import config

class VideoManager:
    """동영상 관리 클래스"""
    
    def __init__(self, db_path: str = None):
        self.db_path = db_path or config.DATABASE_PATH
    
    def get_connection(self):
        """데이터베이스 연결"""
        return sqlite3.connect(self.db_path)
    
    def extract_youtube_id(self, url: str) -> Optional[str]:
        """유튜브 URL에서 비디오 ID 추출"""
        patterns = [
            r'(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/)([^&\n?#]+)',
            r'youtube\.com\/v\/([^&\n?#]+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return None
    
    def get_embed_url(self, youtube_url: str) -> str:
        """유튜브 URL을 embed URL로 변환"""
        video_id = self.extract_youtube_id(youtube_url)
        if video_id:
            return f"https://www.youtube.com/embed/{video_id}"
        return youtube_url
    
    def get_all_videos(self) -> List[Tuple]:
        """모든 동영상 조회"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                SELECT id, title, video_url, description, created_at
                FROM video
                ORDER BY created_at DESC
            """)
            return cursor.fetchall()
        finally:
            conn.close()
    
    def get_video_by_id(self, video_id: int) -> Optional[Tuple]:
        """특정 동영상 조회"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                SELECT id, title, video_url, description, created_at
                FROM video
                WHERE id = ?
            """, (video_id,))
            return cursor.fetchone()
        finally:
            conn.close()
    
    def get_latest_video(self) -> Optional[Tuple]:
        """최신 동영상 1개 조회"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                SELECT id, title, video_url, description, created_at
                FROM video
                ORDER BY created_at DESC
                LIMIT 1
            """)
            return cursor.fetchone()
        finally:
            conn.close()
    
    def create_video(self, title: str, video_url: str, description: str = "") -> int:
        """새로운 동영상 생성"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            # 유튜브 URL 검증 및 embed URL로 변환
            embed_url = self.get_embed_url(video_url)
            
            cursor.execute("""
                INSERT INTO video (title, video_url, description)
                VALUES (?, ?, ?)
            """, (title, embed_url, description))
            conn.commit()
            return cursor.lastrowid
        except sqlite3.Error as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    def update_video(self, video_id: int, title: str, video_url: str, description: str = "") -> bool:
        """동영상 수정"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            # 유튜브 URL 검증 및 embed URL로 변환
            embed_url = self.get_embed_url(video_url)
            
            cursor.execute("""
                UPDATE video 
                SET title = ?, video_url = ?, description = ?
                WHERE id = ?
            """, (title, embed_url, description, video_id))
            conn.commit()
            return cursor.rowcount > 0
        except sqlite3.Error as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    def delete_video(self, video_id: int) -> bool:
        """동영상 삭제"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("DELETE FROM video WHERE id = ?", (video_id,))
            conn.commit()
            return cursor.rowcount > 0
        except sqlite3.Error as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    def get_video_stats(self) -> List[Tuple]:
        """동영상별 시청 통계 조회"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                SELECT v.id, v.title, 
                       COUNT(al.id) as total_views,
                       COUNT(CASE WHEN al.activity_type = 'video_ended' THEN 1 END) as completed_views,
                       AVG(CASE WHEN al.metadata IS NOT NULL 
                           THEN json_extract(al.metadata, '$.watch_time') 
                           END) as avg_watch_time
                FROM video v
                LEFT JOIN activity_log al ON v.id = al.video_id 
                    AND al.activity_type IN ('video_play', 'video_ended', 'video_progress')
                GROUP BY v.id, v.title
                ORDER BY total_views DESC
            """)
            return cursor.fetchall()
        finally:
            conn.close()
    
    def get_video_segments(self, video_id: int) -> List[Tuple]:
        """비디오 구간 목록 조회"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                SELECT id, segment_index, segment_name, start_time, end_time, description
                FROM video_segments
                WHERE video_id = ?
                ORDER BY segment_index ASC
            """, (video_id,))
            return cursor.fetchall()
        finally:
            conn.close()
    
    def create_video_segment(self, video_id: int, segment_index: int, segment_name: str, 
                           start_time: float, end_time: float, description: str = "") -> int:
        """비디오 구간 생성"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO video_segments (video_id, segment_index, segment_name, start_time, end_time, description)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (video_id, segment_index, segment_name, start_time, end_time, description))
            conn.commit()
            return cursor.lastrowid
        except sqlite3.Error as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    def update_video_segment(self, segment_id: int, segment_name: str, 
                           start_time: float, end_time: float, description: str = "") -> bool:
        """비디오 구간 수정"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                UPDATE video_segments 
                SET segment_name = ?, start_time = ?, end_time = ?, description = ?
                WHERE id = ?
            """, (segment_name, start_time, end_time, description, segment_id))
            conn.commit()
            return cursor.rowcount > 0
        except sqlite3.Error as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    def delete_video_segment(self, segment_id: int) -> bool:
        """비디오 구간 삭제"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("DELETE FROM video_segments WHERE id = ?", (segment_id,))
            conn.commit()
            return cursor.rowcount > 0
        except sqlite3.Error as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    def get_segment_by_time(self, video_id: int, current_time: float) -> Optional[Tuple]:
        """현재 시간에 해당하는 구간 조회"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                SELECT id, segment_index, segment_name, start_time, end_time, description
                FROM video_segments
                WHERE video_id = ? AND start_time <= ? AND end_time > ?
                ORDER BY segment_index ASC
                LIMIT 1
            """, (video_id, current_time, current_time))
            return cursor.fetchone()
        finally:
            conn.close()
