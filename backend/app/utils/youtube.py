"""
YouTube 관련 유틸리티 함수
"""
import re
from typing import Optional


def extract_youtube_id(youtube_url: str) -> Optional[str]:
    """
    YouTube URL에서 비디오 ID를 추출합니다.
    
    지원하는 URL 형식:
    - https://www.youtube.com/watch?v=VIDEO_ID
    - https://youtu.be/VIDEO_ID
    - https://youtube.com/watch?v=VIDEO_ID
    - https://m.youtube.com/watch?v=VIDEO_ID
    - https://www.youtube.com/embed/VIDEO_ID
    - https://youtube.com/embed/VIDEO_ID
    
    Args:
        youtube_url: YouTube URL
        
    Returns:
        YouTube 비디오 ID 또는 None (추출 실패 시)
    """
    if not youtube_url:
        return None
    
    # 다양한 YouTube URL 패턴
    patterns = [
        r'(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/)([a-zA-Z0-9_-]{11})',
        r'youtube\.com\/watch\?.*v=([a-zA-Z0-9_-]{11})',
        r'youtube\.com\/embed\/([a-zA-Z0-9_-]{11})',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, youtube_url)
        if match:
            return match.group(1)
    
    return None


def is_valid_youtube_url(youtube_url: str) -> bool:
    """
    유효한 YouTube URL인지 확인합니다.
    
    Args:
        youtube_url: 확인할 URL
        
    Returns:
        유효한 YouTube URL이면 True, 아니면 False
    """
    return extract_youtube_id(youtube_url) is not None


def get_youtube_thumbnail_url(youtube_id: str, quality: str = 'maxresdefault') -> str:
    """
    YouTube 비디오 ID로 썸네일 URL을 생성합니다.
    
    Args:
        youtube_id: YouTube 비디오 ID
        quality: 썸네일 품질 ('default', 'medium', 'high', 'standard', 'maxresdefault')
        
    Returns:
        썸네일 URL
    """
    return f"https://img.youtube.com/vi/{youtube_id}/{quality}.jpg"
