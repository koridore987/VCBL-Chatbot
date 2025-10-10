"""
통합 학습 활동 로그 관리 모델
"""
import sqlite3
import json
from typing import List, Tuple, Optional, Dict, Any
from datetime import datetime
from app import config

class ActivityLogManager:
    """통합 학습 활동 로그 관리 클래스"""
    
    def __init__(self, db_path: str = None):
        self.db_path = db_path or config.DATABASE_PATH
    
    def get_connection(self):
        """데이터베이스 연결"""
        return sqlite3.connect(self.db_path)
    
    def log_activity(self, user_id: int, activity_type: str, content: str = "", 
                    metadata: Dict[str, Any] = None, video_id: int = None) -> int:
        """활동 기록"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            # 시간 관련 데이터 반올림 처리 (3자리수 이하)
            if metadata:
                processed_metadata = {}
                for key, value in metadata.items():
                    if isinstance(value, (int, float)) and any(time_key in key.lower() for time_key in ['time', 'distance', 'duration']):
                        processed_metadata[key] = round(value, 3)
                    else:
                        processed_metadata[key] = value
                metadata = processed_metadata
            
            # content를 직접 저장 (JSON 직렬화하지 않음)
            content_str = content if content else None
            metadata_json = json.dumps(metadata, ensure_ascii=False) if metadata else None
            
            cursor.execute("""
                INSERT INTO activity_log (user_id, activity_type, video_id, content, metadata)
                VALUES (?, ?, ?, ?, ?)
            """, (user_id, activity_type, video_id, content_str, metadata_json))
            conn.commit()
            return cursor.lastrowid
        except sqlite3.Error as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    def get_user_timeline(self, user_id: int, limit: int = 100) -> List[Tuple]:
        """사용자별 통합 타임라인 조회"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                SELECT al.id, al.activity_type, al.content, al.metadata, al.timestamp,
                       v.title as video_title, v.id as video_id
                FROM activity_log al
                LEFT JOIN video v ON al.video_id = v.id
                WHERE al.user_id = ?
                ORDER BY al.timestamp DESC
                LIMIT ?
            """, (user_id, limit))
            return cursor.fetchall()
        finally:
            conn.close()
    
    def get_user_video_progress(self, user_id: int, video_id: int) -> Dict[str, Any]:
        """사용자의 특정 동영상 시청 진행률"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            # 동영상 총 길이 (metadata에서 추출)
            cursor.execute("""
                SELECT metadata
                FROM activity_log
                WHERE user_id = ? AND video_id = ? AND activity_type = 'video_progress'
                ORDER BY timestamp DESC
                LIMIT 1
            """, (user_id, video_id))
            row = cursor.fetchone()
            
            if row and row[0]:
                metadata = json.loads(row[0])
                return {
                    'current_time': metadata.get('current_time', 0),
                    'duration': metadata.get('duration', 0),
                    'progress_percentage': metadata.get('progress_percentage', 0)
                }
            return {'current_time': 0, 'duration': 0, 'progress_percentage': 0}
        finally:
            conn.close()
    
    def get_video_watch_stats(self, video_id: int) -> Dict[str, Any]:
        """동영상별 시청 통계"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            # 총 시청 수
            cursor.execute("""
                SELECT COUNT(DISTINCT user_id)
                FROM activity_log
                WHERE video_id = ? AND activity_type = 'video_play'
            """, (video_id,))
            total_viewers = cursor.fetchone()[0]
            
            # 완료 시청 수
            cursor.execute("""
                SELECT COUNT(DISTINCT user_id)
                FROM activity_log
                WHERE video_id = ? AND activity_type = 'video_ended'
            """, (video_id,))
            completed_viewers = cursor.fetchone()[0]
            
            # 평균 시청 시간
            cursor.execute("""
                SELECT AVG(json_extract(metadata, '$.watch_time'))
                FROM activity_log
                WHERE video_id = ? AND activity_type = 'video_progress'
                AND metadata IS NOT NULL
            """, (video_id,))
            avg_watch_time = cursor.fetchone()[0] or 0
            
            return {
                'total_viewers': total_viewers,
                'completed_viewers': completed_viewers,
                'completion_rate': (completed_viewers / total_viewers * 100) if total_viewers > 0 else 0,
                'avg_watch_time': avg_watch_time
            }
        finally:
            conn.close()
    
    def get_user_activity_summary(self, user_id: int) -> Dict[str, Any]:
        """사용자 활동 요약"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            # 동영상 시청 통계
            cursor.execute("""
                SELECT COUNT(DISTINCT video_id) as videos_watched,
                       COUNT(CASE WHEN activity_type = 'video_ended' THEN 1 END) as videos_completed
                FROM activity_log
                WHERE user_id = ? AND video_id IS NOT NULL
            """, (user_id,))
            video_stats = cursor.fetchone()
            
            # 챗봇 사용 통계
            cursor.execute("""
                SELECT COUNT(*) as chat_messages
                FROM activity_log
                WHERE user_id = ? AND activity_type = 'chat_message'
            """, (user_id,))
            chat_stats = cursor.fetchone()
            
            # 챗봇 응답 통계
            cursor.execute("""
                SELECT COUNT(*) as bot_responses
                FROM activity_log
                WHERE user_id = ? AND activity_type = 'bot_response_end'
            """, (user_id,))
            bot_response_stats = cursor.fetchone()
            
            # 최근 활동
            cursor.execute("""
                SELECT activity_type, timestamp
                FROM activity_log
                WHERE user_id = ?
                ORDER BY timestamp DESC
                LIMIT 1
            """, (user_id,))
            last_activity = cursor.fetchone()
            
            return {
                'videos_watched': video_stats[0] if video_stats else 0,
                'videos_completed': video_stats[1] if video_stats else 0,
                'chat_messages': chat_stats[0] if chat_stats else 0,
                'bot_responses': bot_response_stats[0] if bot_response_stats else 0,
                'last_activity': last_activity[1] if last_activity else None,
                'last_activity_type': last_activity[0] if last_activity else None
            }
        finally:
            conn.close()
    
    def get_activity_by_type(self, user_id: int, activity_type: str, limit: int = 50) -> List[Tuple]:
        """특정 활동 타입별 조회"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                SELECT al.id, al.content, al.metadata, al.timestamp,
                       v.title as video_title
                FROM activity_log al
                LEFT JOIN video v ON al.video_id = v.id
                WHERE al.user_id = ? AND al.activity_type = ?
                ORDER BY al.timestamp DESC
                LIMIT ?
            """, (user_id, activity_type, limit))
            return cursor.fetchall()
        finally:
            conn.close()
    
    def get_video_navigation_analysis(self, user_id: int, video_id: int) -> Dict:
        """비디오 탐색 패턴 분석"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            # 탐색 이벤트 추출
            cursor.execute("""
                SELECT activity_type, metadata, timestamp
                FROM activity_log 
                WHERE user_id = ? AND video_id = ? 
                AND activity_type IN ('video_play', 'video_pause', 'video_seek', 'video_progress', 'video_ended')
                ORDER BY timestamp ASC
            """, (user_id, video_id))
            
            activities = cursor.fetchall()
            
            # 탐색 패턴 분석
            seek_events = []
            segment_changes = []
            total_seek_distance = 0
            forward_seeks = 0
            backward_seeks = 0
            
            for activity in activities:
                activity_type, metadata_json, timestamp = activity
                metadata = json.loads(metadata_json) if metadata_json else {}
                
                if activity_type == 'video_seek':
                    seek_distance = metadata.get('seek_distance', 0)
                    seek_direction = metadata.get('seek_direction', '')
                    
                    seek_events.append({
                        'time': timestamp,
                        'distance': seek_distance,
                        'direction': seek_direction,
                        'from_time': metadata.get('previous_time', 0),
                        'to_time': metadata.get('current_time', 0)
                    })
                    
                    total_seek_distance += abs(seek_distance)
                    if seek_direction == 'forward':
                        forward_seeks += 1
                    elif seek_direction == 'backward':
                        backward_seeks += 1
                
                if metadata.get('segment_change'):
                    segment_changes.append({
                        'time': timestamp,
                        'from_segment': metadata.get('from_segment', ''),
                        'to_segment': metadata.get('to_segment', '')
                    })
            
            # 구간별 시청 빈도
            cursor.execute("""
                SELECT 
                    json_extract(metadata, '$.segment_name') as segment_name,
                    COUNT(*) as view_count,
                    AVG(json_extract(metadata, '$.current_time')) as avg_time
                FROM activity_log 
                WHERE user_id = ? AND video_id = ? 
                AND activity_type = 'video_progress'
                AND json_extract(metadata, '$.segment_name') IS NOT NULL
                GROUP BY json_extract(metadata, '$.segment_name')
                ORDER BY view_count DESC
            """, (user_id, video_id))
            
            segment_stats = cursor.fetchall()
            
            return {
                'seek_events': seek_events,
                'segment_changes': segment_changes,
                'total_seek_distance': total_seek_distance,
                'forward_seeks': forward_seeks,
                'backward_seeks': backward_seeks,
                'segment_stats': segment_stats,
                'navigation_intensity': len(seek_events),
                'preferred_direction': 'forward' if forward_seeks > backward_seeks else 'backward' if backward_seeks > forward_seeks else 'balanced'
            }
        finally:
            conn.close()
    
    def get_segment_heatmap(self, user_id: int, video_id: int) -> List[Dict]:
        """1초 단위 시청 히트맵 데이터"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                SELECT 
                    json_extract(metadata, '$.current_time') as current_time,
                    activity_type,
                    COUNT(*) as frequency
                FROM activity_log 
                WHERE user_id = ? AND video_id = ? 
                AND activity_type IN ('video_play', 'video_pause', 'video_progress')
                AND json_extract(metadata, '$.current_time') IS NOT NULL
                GROUP BY 
                    CAST(json_extract(metadata, '$.current_time') AS INTEGER),
                    activity_type
                ORDER BY current_time ASC
            """, (user_id, video_id))
            
            heatmap_data = []
            for row in cursor.fetchall():
                current_time, activity_type, frequency = row
                time_second = int(current_time)
                
                heatmap_data.append({
                    'time_second': time_second,
                    'time_label': f"{time_second}초",
                    'view_frequency': frequency,
                    'activity_type': activity_type,
                    'heat_level': min(frequency / 3, 1.0)  # 최대 3회를 1.0으로 정규화
                })
            
            return heatmap_data
        finally:
            conn.close()
    
    def get_continuous_heatmap(self, user_id: int, video_id: int) -> List[Dict]:
        """연속적인 그라데이션 히트맵 데이터"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            # 비디오 총 길이 가져오기
            cursor.execute("SELECT duration FROM video WHERE id = ?", (video_id,))
            video_duration = cursor.fetchone()
            if not video_duration or not video_duration[0]:
                return []
            
            total_duration = int(video_duration[0])
            
            # 1초 단위로 모든 시간대의 시청 빈도 계산
            cursor.execute("""
                SELECT 
                    CAST(json_extract(metadata, '$.current_time') AS INTEGER) as time_second,
                    COUNT(*) as frequency
                FROM activity_log 
                WHERE user_id = ? AND video_id = ? 
                AND activity_type IN ('video_play', 'video_pause', 'video_progress')
                AND json_extract(metadata, '$.current_time') IS NOT NULL
                GROUP BY CAST(json_extract(metadata, '$.current_time') AS INTEGER)
                ORDER BY time_second ASC
            """, (user_id, video_id))
            
            # 시간대별 빈도 딕셔너리 생성
            time_frequency = {}
            for row in cursor.fetchall():
                time_second, frequency = row
                time_frequency[time_second] = frequency
            
            # 전체 시간대에 대해 연속적인 데이터 생성
            continuous_data = []
            max_frequency = max(time_frequency.values()) if time_frequency else 1
            
            for second in range(total_duration + 1):
                frequency = time_frequency.get(second, 0)
                heat_level = frequency / max_frequency if max_frequency > 0 else 0
                
                continuous_data.append({
                    'time_second': second,
                    'frequency': frequency,
                    'heat_level': heat_level,
                    'percentage': (second / total_duration * 100) if total_duration > 0 else 0
                })
            
            return continuous_data
        finally:
            conn.close()
    
    def get_distribution_chart(self, user_id: int, video_id: int) -> Dict:
        """분포 그래프 데이터"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            # 비디오 총 길이 가져오기
            cursor.execute("SELECT duration FROM video WHERE id = ?", (video_id,))
            video_duration = cursor.fetchone()
            if not video_duration or not video_duration[0]:
                return {'distribution': [], 'max_frequency': 0}
            
            total_duration = int(video_duration[0])
            
            # 10초 단위로 그룹화하여 분포 계산
            cursor.execute("""
                SELECT 
                    CAST(json_extract(metadata, '$.current_time') / 10 AS INTEGER) * 10 as time_segment,
                    COUNT(*) as frequency
                FROM activity_log 
                WHERE user_id = ? AND video_id = ? 
                AND activity_type IN ('video_play', 'video_pause', 'video_progress')
                AND json_extract(metadata, '$.current_time') IS NOT NULL
                GROUP BY CAST(json_extract(metadata, '$.current_time') / 10 AS INTEGER)
                ORDER BY time_segment ASC
            """, (user_id, video_id))
            
            distribution_data = []
            max_frequency = 0
            
            for row in cursor.fetchall():
                time_segment, frequency = row
                max_frequency = max(max_frequency, frequency)
                
                distribution_data.append({
                    'time_segment': time_segment,
                    'time_label': f"{time_segment}-{time_segment + 10}초",
                    'frequency': frequency,
                    'height_percentage': (frequency / max_frequency * 100) if max_frequency > 0 else 0
                })
            
            return {
                'distribution': distribution_data,
                'max_frequency': max_frequency,
                'total_duration': total_duration
            }
        finally:
            conn.close()
    
    def get_segment_statistics(self, video_id: int) -> Dict:
        """구간별 통계"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            # 구간별 평균 시청 시간
            cursor.execute("""
                SELECT 
                    json_extract(metadata, '$.segment_name') as segment_name,
                    COUNT(*) as total_views,
                    AVG(json_extract(metadata, '$.current_time')) as avg_watch_time,
                    COUNT(CASE WHEN activity_type = 'video_seek' THEN 1 END) as seek_count,
                    COUNT(CASE WHEN json_extract(metadata, '$.seek_direction') = 'backward' THEN 1 END) as backward_seeks
                FROM activity_log 
                WHERE video_id = ? 
                AND activity_type IN ('video_progress', 'video_seek')
                AND json_extract(metadata, '$.segment_name') IS NOT NULL
                GROUP BY json_extract(metadata, '$.segment_name')
                ORDER BY total_views DESC
            """, (video_id,))
            
            segment_stats = cursor.fetchall()
            
            # 전체 통계
            cursor.execute("""
                SELECT 
                    COUNT(DISTINCT user_id) as unique_viewers,
                    COUNT(*) as total_activities,
                    AVG(json_extract(metadata, '$.current_time')) as avg_watch_time
                FROM activity_log 
                WHERE video_id = ? 
                AND activity_type IN ('video_play', 'video_pause', 'video_progress')
            """, (video_id,))
            
            overall_stats = cursor.fetchone()
            
            return {
                'segment_stats': segment_stats,
                'overall_stats': {
                    'unique_viewers': overall_stats[0] or 0,
                    'total_activities': overall_stats[1] or 0,
                    'avg_watch_time': overall_stats[2] or 0
                }
            }
        finally:
            conn.close()
