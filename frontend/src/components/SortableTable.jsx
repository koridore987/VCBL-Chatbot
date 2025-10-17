import { useState, useMemo } from 'react'
import { HiChevronUp, HiChevronDown, HiSearch } from 'react-icons/hi'

/**
 * 재사용 가능한 정렬/검색 가능한 반응형 테이블 컴포넌트
 * 
 * @param {Array} data - 테이블 데이터 배열
 * @param {Array} columns - 컬럼 정의 배열
 *   - key: 데이터 키
 *   - label: 표시할 컬럼명
 *   - sortable: 정렬 가능 여부 (기본값: true)
 *   - searchable: 검색 대상 여부 (기본값: false)
 *   - render: 커스텀 렌더링 함수 (선택사항)
 *   - className: 추가 CSS 클래스
 *   - width: 컬럼 너비 (선택사항)
 * @param {Function} onRowClick - 행 클릭 핸들러 (선택사항)
 * @param {String} rowKey - 행의 고유 키 (기본값: 'id')
 * @param {Boolean} enableSearch - 검색 기능 활성화 (기본값: false)
 * @param {String} searchPlaceholder - 검색 입력 플레이스홀더
 * @param {Object} emptyState - 데이터 없을 때 표시할 내용
 * @param {Boolean} stickyHeader - 헤더 고정 여부 (기본값: false)
 * @param {String} height - 테이블 높이 (선택사항)
 */
const SortableTable = ({
  data = [],
  columns = [],
  onRowClick,
  rowKey = 'id',
  enableSearch = false,
  searchPlaceholder = '검색...',
  emptyState,
  stickyHeader = false,
  height = 'auto',
  className = ''
}) => {
  const [sortConfig, setSortConfig] = useState({ key: null, direction: null })
  const [searchTerm, setSearchTerm] = useState('')

  // 정렬 처리
  const sortedData = useMemo(() => {
    if (!sortConfig.key) return data

    const sorted = [...data].sort((a, b) => {
      const aValue = a[sortConfig.key]
      const bValue = b[sortConfig.key]

      // null/undefined 처리
      if (aValue == null) return 1
      if (bValue == null) return -1

      // 숫자 비교
      if (typeof aValue === 'number' && typeof bValue === 'number') {
        return sortConfig.direction === 'asc' ? aValue - bValue : bValue - aValue
      }

      // 문자열 비교
      const aStr = String(aValue).toLowerCase()
      const bStr = String(bValue).toLowerCase()

      if (aStr < bStr) return sortConfig.direction === 'asc' ? -1 : 1
      if (aStr > bStr) return sortConfig.direction === 'asc' ? 1 : -1
      return 0
    })

    return sorted
  }, [data, sortConfig])

  // 검색 처리
  const filteredData = useMemo(() => {
    if (!searchTerm.trim()) return sortedData

    const searchLower = searchTerm.toLowerCase()
    const searchableColumns = columns.filter(col => col.searchable !== false)

    return sortedData.filter(row => {
      return searchableColumns.some(col => {
        const value = row[col.key]
        if (value == null) return false
        return String(value).toLowerCase().includes(searchLower)
      })
    })
  }, [sortedData, searchTerm, columns])

  // 정렬 토글
  const handleSort = (key) => {
    const column = columns.find(col => col.key === key)
    if (column?.sortable === false) return

    let direction = 'asc'
    if (sortConfig.key === key && sortConfig.direction === 'asc') {
      direction = 'desc'
    }

    setSortConfig({ key, direction })
  }

  // 정렬 아이콘 렌더링
  const renderSortIcon = (key) => {
    if (sortConfig.key !== key) {
      return <HiChevronDown style={{ opacity: 0.3 }} />
    }
    return sortConfig.direction === 'asc' ? 
      <HiChevronUp /> : 
      <HiChevronDown />
  }

  // 셀 값 렌더링
  const renderCell = (row, column) => {
    if (column.render) {
      return column.render(row[column.key], row)
    }
    return row[column.key]
  }

  return (
    <div className={`sortable-table-container ${className}`}>
      {/* 검색 바 */}
      {enableSearch && (
        <div style={{ marginBottom: '20px' }}>
          <div style={{ 
            position: 'relative',
            maxWidth: '400px'
          }}>
            <HiSearch style={{ 
              position: 'absolute',
              left: '12px',
              top: '50%',
              transform: 'translateY(-50%)',
              color: '#9ca3af',
              fontSize: '20px'
            }} />
            <input
              type="text"
              className="form-input"
              placeholder={searchPlaceholder}
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              style={{
                paddingLeft: '40px',
                width: '100%'
              }}
            />
          </div>
        </div>
      )}

      {/* 테이블 래퍼 */}
      <div 
        style={{ 
          overflowX: 'auto',
          height: height,
          position: 'relative'
        }}
        className="table-wrapper"
      >
        <table className="sortable-table">
          <thead style={stickyHeader ? { position: 'sticky', top: 0, zIndex: 10 } : {}}>
            <tr>
              {columns.map((column) => (
                <th
                  key={column.key}
                  onClick={() => handleSort(column.key)}
                  className={column.sortable !== false ? 'sortable' : ''}
                  style={{
                    width: column.width || 'auto',
                    cursor: column.sortable !== false ? 'pointer' : 'default',
                    userSelect: 'none'
                  }}
                >
                  <div style={{ 
                    display: 'flex', 
                    alignItems: 'center', 
                    gap: '8px',
                    justifyContent: 'space-between'
                  }}>
                    <span>{column.label}</span>
                    {column.sortable !== false && renderSortIcon(column.key)}
                  </div>
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {filteredData.length === 0 ? (
              <tr>
                <td colSpan={columns.length} style={{ textAlign: 'center', padding: '40px' }}>
                  {emptyState || (
                    <div style={{ color: '#9ca3af' }}>
                      {searchTerm ? '검색 결과가 없습니다' : '데이터가 없습니다'}
                    </div>
                  )}
                </td>
              </tr>
            ) : (
              filteredData.map((row) => (
                <tr
                  key={row[rowKey]}
                  onClick={() => onRowClick && onRowClick(row)}
                  className={onRowClick ? 'clickable' : ''}
                >
                  {columns.map((column) => (
                    <td
                      key={column.key}
                      className={column.className || ''}
                      onClick={(e) => column.onClick && column.onClick(e, row)}
                    >
                      {renderCell(row, column)}
                    </td>
                  ))}
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* 반응형 카드 뷰 (모바일) */}
      <div className="mobile-card-view">
        {enableSearch && (
          <div style={{ marginBottom: '20px' }}>
            <div style={{ position: 'relative' }}>
              <HiSearch style={{ 
                position: 'absolute',
                left: '12px',
                top: '50%',
                transform: 'translateY(-50%)',
                color: '#9ca3af',
                fontSize: '20px'
              }} />
              <input
                type="text"
                className="form-input"
                placeholder={searchPlaceholder}
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                style={{ paddingLeft: '40px', width: '100%' }}
              />
            </div>
          </div>
        )}

        {filteredData.length === 0 ? (
          <div style={{ 
            textAlign: 'center', 
            padding: '40px',
            color: '#9ca3af'
          }}>
            {emptyState || (searchTerm ? '검색 결과가 없습니다' : '데이터가 없습니다')}
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            {filteredData.map((row) => (
              <div
                key={row[rowKey]}
                className={`mobile-card ${onRowClick ? 'clickable' : ''}`}
                onClick={() => onRowClick && onRowClick(row)}
              >
                {columns.map((column) => (
                  <div key={column.key} className="mobile-card-row">
                    <span className="mobile-card-label">{column.label}</span>
                    <span className="mobile-card-value">
                      {renderCell(row, column)}
                    </span>
                  </div>
                ))}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* 결과 수 표시 */}
      {filteredData.length > 0 && (
        <div style={{ 
          marginTop: '16px', 
          fontSize: '14px', 
          color: '#6b7280',
          textAlign: 'right'
        }}>
          총 {filteredData.length}개의 항목
          {searchTerm && ` (전체 ${data.length}개 중)`}
        </div>
      )}

      <style jsx>{`
        .sortable-table-container {
          width: 100%;
        }

        .sortable-table {
          width: 100%;
          border-collapse: collapse;
          background: white;
        }

        .sortable-table thead {
          background: #f9fafb;
          border-bottom: 2px solid #e5e7eb;
        }

        .sortable-table th {
          padding: 12px 16px;
          text-align: left;
          font-weight: 600;
          font-size: 14px;
          color: #374151;
        }

        .sortable-table th.sortable:hover {
          background: #f3f4f6;
        }

        .sortable-table td {
          padding: 12px 16px;
          border-bottom: 1px solid #e5e7eb;
          font-size: 14px;
        }

        .sortable-table tr.clickable {
          cursor: pointer;
          transition: background-color 0.15s;
        }

        .sortable-table tr.clickable:hover {
          background-color: #f9fafb;
        }

        /* 모바일 카드 뷰 (기본적으로 숨김) */
        .mobile-card-view {
          display: none;
        }

        /* 반응형: 768px 이하에서 테이블 숨기고 카드 뷰 표시 */
        @media (max-width: 768px) {
          .table-wrapper {
            display: none;
          }

          .mobile-card-view {
            display: block;
          }

          .mobile-card {
            background: white;
            border: 1px solid #e5e7eb;
            border-radius: 8px;
            padding: 16px;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
          }

          .mobile-card.clickable {
            cursor: pointer;
            transition: all 0.15s;
          }

          .mobile-card.clickable:active {
            transform: scale(0.98);
            box-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
          }

          .mobile-card-row {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 8px 0;
            border-bottom: 1px solid #f3f4f6;
          }

          .mobile-card-row:last-child {
            border-bottom: none;
          }

          .mobile-card-label {
            font-weight: 600;
            font-size: 13px;
            color: #6b7280;
            flex-shrink: 0;
            margin-right: 16px;
          }

          .mobile-card-value {
            font-size: 14px;
            color: #111827;
            text-align: right;
            flex: 1;
          }
        }

        /* 반응형: 1024px 이하에서 테이블 스크롤 가능 */
        @media (max-width: 1024px) {
          .table-wrapper {
            -webkit-overflow-scrolling: touch;
          }

          .sortable-table {
            min-width: 600px;
          }
        }
      `}</style>
    </div>
  )
}

export default SortableTable

