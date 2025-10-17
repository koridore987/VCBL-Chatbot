import { HiSparkles, HiPlay } from 'react-icons/hi'

const HeroSection = ({ stats = {}, onExploreClick }) => {
  const { total = 0, completed = 0, inProgress = 0 } = stats
  const completionRate = total ? Math.round((completed / total) * 100) : 0
  const handleExplore = onExploreClick || (() => {})
  const statItems = [
    { 
      label: '전체 모듈', 
      value: total, 
      caption: '학습 가능한 영상 수',
      accent: 'from-blue-500/80 to-blue-400/70'
    },
    { 
      label: '완료한 모듈', 
      value: completed, 
      caption: '수료한 콘텐츠',
      accent: 'from-emerald-500/80 to-teal-400/70'
    },
    { 
      label: '진행 중', 
      value: inProgress, 
      caption: '현재 진행 중인 학습',
      accent: 'from-amber-500/80 to-orange-400/70'
    },
  ]

  return (
    <section className="relative overflow-hidden border-b border-primary-100/40 bg-gradient-to-br from-white via-primary-50/20 to-accent-50/30">
      <div className="pointer-events-none absolute -left-24 top-[-80px] h-64 w-64 rounded-full bg-gradient-to-br from-primary-300/40 to-primary-500/30 blur-3xl" />
      <div className="pointer-events-none absolute -right-16 bottom-[-60px] h-72 w-72 rounded-full bg-gradient-to-tr from-accent-300/40 to-secondary-400/30 blur-3xl" />
      <div className="pointer-events-none absolute left-1/2 top-1/2 h-40 w-40 -translate-x-1/2 -translate-y-1/2 rounded-full bg-gradient-to-br from-white/40 to-primary-200/20 blur-2xl" />

      <div className="relative z-10 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-5 sm:py-8">
        <div className="flex flex-col gap-8 md:flex-row md:items-center md:justify-between">
          <div className="max-w-2xl">
            <div className="inline-flex items-center gap-2 rounded-full bg-white/70 px-3 py-1 text-xs font-semibold text-primary-700 shadow-sm ring-1 ring-white/60 backdrop-blur">
              <HiSparkles className="text-primary-500" />
              <span>나의 학습 현황</span>
            </div>
            <h1 className="mt-4 text-3xl sm:text-4xl font-bold text-gray-900 leading-snug">
              바로 이어서 보고 싶은 모듈을 선택해 학습을 계속하세요
            </h1>
            <p className="mt-3 text-sm sm:text-base text-gray-600">
              전체 진행 상황과 완료율을 확인하고, 가장 관심 가는 모듈로 곧바로 이동할 수 있어요.
            </p>
            <div className="mt-6 flex flex-wrap items-center gap-3 text-sm text-gray-500">
              <button
                type="button"
                onClick={handleExplore}
                className="inline-flex items-center gap-2 rounded-full bg-primary-600 px-5 py-2.5 text-sm font-semibold text-white shadow-lg shadow-primary-500/30 transition hover:bg-primary-700 focus:outline-none focus-visible:ring-2 focus-visible:ring-primary-500/60"
              >
                <HiPlay className="text-base" />
                <span>학습 이어가기</span>
              </button>
              <span className="text-xs sm:text-sm">
                완료율 {completionRate}% · 총 {total}개 중 {completed}개 완료
              </span>
            </div>

            <div className="mt-5 flex flex-wrap gap-2 text-xs font-medium text-white">
              {['강의 관찰', '피드백 사례', '실시간 워크숍', 'AI 코칭'].map((label, index) => (
                <span
                  key={label}
                  className={`rounded-full px-3 py-1 shadow-sm backdrop-blur-sm ${
                    [
                      'bg-gradient-to-r from-blue-500/80 to-indigo-500/80',
                      'bg-gradient-to-r from-emerald-500/80 to-teal-400/80',
                      'bg-gradient-to-r from-amber-500/80 to-orange-500/80',
                      'bg-gradient-to-r from-purple-500/80 to-pink-500/80',
                    ][index % 4]
                  }`}
                >
                  {label}
                </span>
              ))}
            </div>
          </div>

          <div className="w-full md:w-auto">
            <div className="grid min-w-[220px] grid-cols-3 gap-3 sm:min-w-[260px] sm:gap-4">
              {statItems.map((item) => (
                <div
                  key={item.label}
                  className="relative overflow-hidden rounded-2xl border border-white/70 bg-white/80 pb-4 pt-5 shadow-sm backdrop-blur-sm transition-transform hover:-translate-y-1"
                >
                  <span className={`absolute -top-1 right-4 h-14 w-14 rounded-full bg-gradient-to-br ${item.accent} opacity-40 blur`} />
                  <span className={`absolute left-4 top-0 h-1 w-16 rounded-full bg-gradient-to-r ${item.accent} opacity-80`} />
                  <p className="text-[11px] uppercase tracking-wide text-gray-500">{item.label}</p>
                  <p className="mt-2 text-2xl font-semibold text-gray-900">{item.value}</p>
                  {item.caption && (
                    <p className="mt-1 text-xs text-gray-400">{item.caption}</p>
                  )}
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </section>
  )
}

export default HeroSection
