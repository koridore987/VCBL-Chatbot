import { HiPlay } from 'react-icons/hi'
import { Link } from 'react-router-dom'

const VideoCard = ({ video }) => {
  return (
    <Link
      to={`/videos/${video.id}`}
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
      </div>
    </Link>
  )
}

export default VideoCard

