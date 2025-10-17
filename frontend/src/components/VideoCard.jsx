import { HiPlay } from 'react-icons/hi'
import { Link } from 'react-router-dom'
import { formatters } from '../utils'

const VideoCard = ({ video }) => {
  const progress = video.learning_progress || {}
  const status = progress.status || 'not_started'
  const activityTimestamp = progress.completed_at || progress.last_activity_at || progress.started_at

  const statusMeta = {
    completed: {
      label: '완료',
      className: 'bg-emerald-100 text-emerald-700'
    },
    in_progress: {
      label: '진행 중',
      className: 'bg-blue-100 text-blue-700'
    },
    not_started: {
      label: '미시작',
      className: 'bg-gray-100 text-gray-600'
    }
  }[status] || {
    label: '미시작',
    className: 'bg-gray-100 text-gray-600'
  }

  return (
    <Link
      to={`/modules/${video.id}`}
      className="group block"
    >
      <div className="glass-card p-0 overflow-hidden transition-all duration-300">
        {/* Thumbnail */}
        <div className="relative pb-[56.25%] bg-gradient-to-br from-primary-100 to-accent-100 overflow-hidden">
          {video.thumbnail_url ? (
            <img
              src={video.thumbnail_url}
              alt={video.title}
              className="absolute inset-0 w-full h-full object-cover group-hover:scale-110 transition-transform duration-500"
            />
          ) : (
            <div className="absolute inset-0 flex items-center justify-center">
              <div className="text-center">
                <HiPlay className="text-6xl text-primary-300 mx-auto mb-2" />
                <div className="text-sm text-primary-500 font-medium">비디오 미리보기</div>
              </div>
            </div>
          )}
          
          {/* Gradient overlay on hover */}
          <div className="absolute inset-0 bg-gradient-to-t from-black/60 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
          
          {/* Play button overlay */}
          <div className="absolute inset-0 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-all duration-300">
            <div className="bg-white/90 backdrop-blur-sm rounded-full p-4 transform scale-75 group-hover:scale-100 transition-transform duration-300 shadow-xl">
              <HiPlay className="text-4xl text-primary-600" />
            </div>
          </div>
        </div>
        
        {/* Content */}
        <div className="p-6">
          <h3 className="text-lg font-bold text-gray-800 mb-2 line-clamp-2 group-hover:text-primary-600 transition-colors">
            {video.title}
          </h3>
          
          {video.description && (
            <p className="text-gray-600 text-sm line-clamp-2 leading-relaxed">
              {video.description}
            </p>
          )}
        </div>
        
        <div className="px-6 pb-6 pt-0">
          <div className="border-t border-gray-100 pt-4 mt-2 flex items-center justify-between text-xs text-gray-500">
            <span className={`inline-flex items-center px-2.5 py-1 rounded-full font-semibold ${statusMeta.className}`}>
              {statusMeta.label}
            </span>
            <span className="text-right">
              {activityTimestamp
                ? `${status === 'completed' ? '완료' : '최근 학습'} · ${formatters.formatRelativeTime(activityTimestamp)}`
                : '학습 기록 없음'}
            </span>
          </div>
          {status === 'completed' && progress.completed_at && (
            <p className="text-[11px] text-gray-400 mt-1 text-right">
              완료일: {formatters.formatDate(progress.completed_at)}
            </p>
          )}
        </div>
      </div>
    </Link>
  )
}

export default VideoCard
