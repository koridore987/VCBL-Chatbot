import { HiSparkles, HiPlay } from 'react-icons/hi'

const HeroSection = ({ stats }) => {
  return (
    <div className="relative mb-12 overflow-hidden">
      {/* Decorative background elements */}
      <div className="absolute top-0 right-0 w-64 h-64 bg-gradient-to-br from-primary-400/20 to-accent-400/20 rounded-full blur-3xl animate-blob" />
      <div className="absolute bottom-0 left-0 w-72 h-72 bg-gradient-to-tr from-secondary-400/20 to-primary-400/20 rounded-full blur-3xl animate-blob" style={{ animationDelay: '2s' }} />
      
      <div className="relative z-10">
        <div className="text-center max-w-4xl mx-auto">
          {/* Badge */}
          <div className="inline-flex items-center space-x-2 px-4 py-2 bg-gradient-to-r from-primary-50 to-accent-50 border border-primary-200 rounded-full mb-6 animate-slide-up">
            <HiSparkles className="text-accent-600 text-lg" />
            <span className="text-sm font-semibold text-primary-700">
              프리미엄 학습 플랫폼
            </span>
          </div>
          
          {/* Main heading */}
          <h1 className="text-5xl md:text-6xl font-extrabold mb-6 leading-tight">
            <span className="bg-gradient-to-r from-primary-600 via-primary-500 to-accent-600 bg-clip-text text-transparent">
              동영상 사례기반
            </span>
            <br />
            <span className="text-gray-800">
              인터랙티브 학습 플랫폼
            </span>
          </h1>
          
          {/* Supporting copy */}
          <p className="text-xl text-gray-600 mb-12 leading-relaxed max-w-2xl mx-auto">
            교실 속 실제 사례로 학습하는 교사 전문성 개발 플랫폼
          </p>
          
          {/* CTA Button */}
          <div className="flex justify-center">
            <button 
              className="group relative inline-flex items-center space-x-2 px-8 py-4 bg-gradient-to-r from-primary-600 to-primary-500 text-white rounded-xl font-semibold text-lg shadow-lg hover:shadow-xl transform hover:scale-105 transition-all duration-300"
              onClick={() => {
                document.getElementById('video-list')?.scrollIntoView({ behavior: 'smooth' })
              }}
            >
              <span>학습 시작하기</span>
              <HiPlay className="text-xl transform group-hover:translate-x-1 transition-transform" />
              <div className="absolute -inset-1 bg-gradient-to-r from-primary-600 to-accent-600 rounded-xl blur opacity-30 group-hover:opacity-50 transition duration-300 -z-10" />
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

export default HeroSection

