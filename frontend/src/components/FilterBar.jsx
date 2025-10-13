import { HiSearch } from 'react-icons/hi'

const FilterBar = ({ searchTerm, setSearchTerm }) => {
  return (
    <div className="mb-8">
      {/* Search Bar */}
      <div className="glass-card p-2">
        <div className="relative">
          <HiSearch className="absolute left-4 top-1/2 transform -translate-y-1/2 text-gray-400 text-xl" />
          <input
            type="text"
            placeholder="비디오 검색..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-12 pr-4 py-3 bg-transparent border-none focus:outline-none text-gray-700 placeholder-gray-400"
          />
        </div>
      </div>
    </div>
  )
}

export default FilterBar

