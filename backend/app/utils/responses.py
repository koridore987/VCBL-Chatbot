"""
표준화된 응답 형식
"""
from flask import jsonify
from typing import Any, Dict, Optional


def success_response(data: Any = None, message: str = None, status_code: int = 200):
    """
    성공 응답
    
    Args:
        data: 응답 데이터
        message: 성공 메시지
        status_code: HTTP 상태 코드
    """
    response = {}
    
    if message:
        response['message'] = message
    
    if data is not None:
        response['data'] = data
    
    return jsonify(response), status_code


def error_response(message: str, status_code: int = 400, details: Dict = None):
    """
    에러 응답
    
    Args:
        message: 에러 메시지
        status_code: HTTP 상태 코드
        details: 추가 에러 상세 정보
    """
    response = {
        'error': message
    }
    
    if details:
        response['details'] = details
    
    return jsonify(response), status_code


def paginated_response(items: list, total: int, page: int, per_page: int, status_code: int = 200):
    """
    페이지네이션 응답
    
    Args:
        items: 아이템 리스트
        total: 전체 아이템 수
        page: 현재 페이지
        per_page: 페이지당 아이템 수
        status_code: HTTP 상태 코드
    """
    total_pages = (total + per_page - 1) // per_page if per_page > 0 else 0
    
    response = {
        'items': items,
        'pagination': {
            'total': total,
            'page': page,
            'per_page': per_page,
            'total_pages': total_pages,
            'has_next': page < total_pages,
            'has_prev': page > 1
        }
    }
    
    return jsonify(response), status_code

