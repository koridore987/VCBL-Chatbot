import { useEffect, useState } from 'react'
import {
  DndContext,
  closestCenter,
  KeyboardSensor,
  PointerSensor,
  useSensor,
  useSensors,
} from '@dnd-kit/core'
import {
  arrayMove,
  SortableContext,
  sortableKeyboardCoordinates,
  verticalListSortingStrategy,
  useSortable,
} from '@dnd-kit/sortable'
import { CSS } from '@dnd-kit/utilities'
import { motion, AnimatePresence } from 'framer-motion'
import { HiPlus, HiPencil, HiTrash, HiViewList, HiX } from 'react-icons/hi'
import api from '../services/api'

const AdminModules = () => {
  const [modules, setModules] = useState([])
  const [loading, setLoading] = useState(true)
  const [editingModule, setEditingModule] = useState(null)
  const [selectedModule, setSelectedModule] = useState(null)
  const [scaffoldings, setScaffoldings] = useState([])
  const [rightPanelMode, setRightPanelMode] = useState(null) // 'form', 'scaffolding', or 'scaffolding-form'
  const [editingScaffolding, setEditingScaffolding] = useState(null)

  const sensors = useSensors(
    useSensor(PointerSensor, {
      activationConstraint: {
        distance: 8,
      },
    }),
    useSensor(KeyboardSensor, {
      coordinateGetter: sortableKeyboardCoordinates,
    })
  )

  const fetchModules = async () => {
    try {
      setLoading(true)
      const response = await api.get('/admin/modules')
      setModules(response.data.data || [])
    } catch (error) {
      console.error('Failed to fetch modules:', error)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchModules()
  }, [])

  const handleCreateModule = async (moduleData) => {
    try {
      await api.post('/admin/modules', moduleData)
      await fetchModules()
      closeRightPanel()
    } catch (error) {
      console.error('Failed to create module:', error)
      alert('모듈 생성 중 오류가 발생했습니다.')
    }
  }

  const handleUpdateModule = async (moduleId, moduleData) => {
    try {
      const response = await api.put(`/admin/modules/${moduleId}`, moduleData)
      const updatedModule = response.data.data
      if (updatedModule) {
        setModules(modules.map(m => m.id === moduleId ? updatedModule : m))
      } else {
        console.error('No data in response')
      }
      closeRightPanel()
    } catch (error) {
      console.error('Failed to update module:', error)
      alert('모듈 수정 중 오류가 발생했습니다.')
    }
  }

  const handleDeleteModule = async (moduleId) => {
    if (window.confirm('정말로 이 모듈을 삭제하시겠습니까?')) {
      try {
        await api.delete(`/admin/modules/${moduleId}`)
        setModules(modules.filter(m => m.id !== moduleId))
      } catch (error) {
        console.error('Failed to delete module:', error)
        alert('모듈 삭제 중 오류가 발생했습니다.')
      }
    }
  }

  const handleDragEnd = async (event) => {
    const { active, over } = event

    if (active.id !== over.id) {
      const oldIndex = modules.findIndex(item => item.id === active.id)
      const newIndex = modules.findIndex(item => item.id === over.id)
      
      const newModules = arrayMove(modules, oldIndex, newIndex)
      setModules(newModules)

      try {
        const updates = newModules.map((module, index) => ({
          id: module.id,
          order_index: index + 1
        }))
        
        for (const update of updates) {
          await api.put(`/admin/modules/${update.id}`, { order_index: update.order_index })
        }
      } catch (error) {
        console.error('Failed to update module order:', error)
        fetchModules()
      }
    }
  }

  const openFormPanel = (module = null) => {
    setEditingModule(module)
    setRightPanelMode('form')
  }

  const openScaffoldingsPanel = async (module) => {
    setSelectedModule(module)
    
    try {
      const response = await api.get(`/admin/modules/${module.id}/scaffoldings`)
      setScaffoldings(response.data.data || [])
    } catch (error) {
      console.error('Failed to fetch scaffoldings:', error)
      setScaffoldings([])
    }
    
    setRightPanelMode('scaffolding')
  }

  const closeRightPanel = () => {
    setRightPanelMode(null)
    setEditingModule(null)
    setSelectedModule(null)
    setScaffoldings([])
    setEditingScaffolding(null)
  }

  const openScaffoldingFormPanel = (scaffolding = null) => {
    setEditingScaffolding(scaffolding)
    setRightPanelMode('scaffolding-form')
  }

  const handleCreateScaffolding = async (scaffoldingData) => {
    if (!selectedModule) return
    
    try {
      console.log('Creating scaffolding...', scaffoldingData)
      const response = await api.post(`/admin/modules/${selectedModule.id}/scaffoldings`, scaffoldingData)
      console.log('Response:', response)
      console.log('Response data:', response.data)
      
      const newScaffolding = response.data.data
      console.log('New scaffolding:', newScaffolding)
      
      if (newScaffolding) {
        setScaffoldings([...scaffoldings, newScaffolding])
        console.log('Updated scaffoldings')
      } else {
        console.error('No data in response')
      }
      
      setRightPanelMode('scaffolding')
      setEditingScaffolding(null)
      console.log('Scaffolding created successfully')
    } catch (error) {
      console.error('Failed to create scaffolding:', error)
      console.error('Error response:', error.response)
      alert('스캐폴딩 생성 중 오류가 발생했습니다: ' + (error.response?.data?.message || error.message))
    }
  }

  const handleUpdateScaffolding = async (scaffoldingId, scaffoldingData) => {
    try {
      console.log('Updating scaffolding...', scaffoldingId, scaffoldingData)
      const response = await api.put(`/admin/scaffoldings/${scaffoldingId}`, scaffoldingData)
      console.log('Update response:', response.data)
      const updatedScaffolding = response.data.data
      if (updatedScaffolding) {
        setScaffoldings(scaffoldings.map(s => s.id === scaffoldingId ? updatedScaffolding : s))
      } else {
        console.error('No data in response')
      }
      setRightPanelMode('scaffolding')
      setEditingScaffolding(null)
    } catch (error) {
      console.error('Failed to update scaffolding:', error)
      console.error('Error response:', error.response)
      alert('스캐폴딩 수정 중 오류가 발생했습니다: ' + (error.response?.data?.message || error.message))
    }
  }

  const handleDeleteScaffolding = async (scaffoldingId) => {
    if (window.confirm('정말로 이 스캐폴딩을 삭제하시겠습니까?')) {
      try {
        await api.delete(`/admin/scaffoldings/${scaffoldingId}`)
        setScaffoldings(scaffoldings.filter(s => s.id !== scaffoldingId))
      } catch (error) {
        console.error('Failed to delete scaffolding:', error)
        alert('스캐폴딩 삭제 중 오류가 발생했습니다.')
      }
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">로딩 중...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="flex gap-6" style={{ minHeight: '600px', maxHeight: '80vh' }}>
        {/* Left Panel - Module List */}
        <motion.div 
          animate={{ 
            width: rightPanelMode ? '40%' : '100%'
          }}
          transition={{ duration: 0.3, ease: "easeInOut" }}
          className="flex-shrink-0"
          style={{ minWidth: rightPanelMode ? '400px' : 'auto' }}
        >
          <div className="flex justify-between items-center mb-6">
            <h1 className="text-3xl font-bold text-gray-800">모듈 관리</h1>
            <button
              onClick={() => openFormPanel(null)}
              className="flex items-center gap-2 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors shadow-md"
            >
              <HiPlus className="text-xl" />
              모듈 추가
            </button>
          </div>

          <DndContext
            sensors={sensors}
            collisionDetection={closestCenter}
            onDragEnd={handleDragEnd}
          >
            <SortableContext
              items={(modules || []).map(m => m.id)}
              strategy={verticalListSortingStrategy}
            >
              <div className="space-y-4">
                {(modules || []).map((module) => (
                  <SortableModuleItem
                    key={module.id}
                    module={module}
                    onEdit={openFormPanel}
                    onDelete={handleDeleteModule}
                    onManageScaffoldings={openScaffoldingsPanel}
                  />
                ))}
              </div>
            </SortableContext>
          </DndContext>

          {(!modules || modules.length === 0) && (
            <div className="text-center py-12 bg-gray-50 rounded-lg">
              <p className="text-gray-500">등록된 모듈이 없습니다.</p>
            </div>
          )}
        </motion.div>

        {/* Right Panel - Form or Scaffolding Management */}
        <AnimatePresence mode="wait">
          {rightPanelMode && (
            <motion.div
              key="right-panel"
              initial={{ opacity: 0, x: 50, scale: 0.95 }}
              animate={{ opacity: 1, x: 0, scale: 1 }}
              exit={{ opacity: 0, x: 50, scale: 0.95 }}
              transition={{ duration: 0.3, ease: "easeInOut" }}
              className="flex-1 bg-white rounded-lg shadow-lg p-6 overflow-y-auto"
              style={{ minWidth: '350px', maxHeight: '80vh' }}
            >
              <div className="flex justify-between items-center mb-4 pb-4 border-b sticky top-0 bg-white z-10">
                <h2 className="text-xl font-semibold text-gray-800">
                  {rightPanelMode === 'form' 
                    ? (editingModule ? '모듈 수정' : '새 모듈 추가')
                    : rightPanelMode === 'scaffolding-form'
                    ? (editingScaffolding ? '스캐폴딩 수정' : '새 스캐폴딩 추가')
                    : `스캐폴딩 관리 - ${selectedModule?.title}`
                  }
                </h2>
                <button
                  onClick={closeRightPanel}
                  className="text-gray-400 hover:text-gray-600 transition-colors"
                >
                  <HiX className="text-2xl" />
                </button>
              </div>

              <AnimatePresence mode="wait">
                {rightPanelMode === 'form' ? (
                  <motion.div
                    key="form-panel"
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -20 }}
                    transition={{ duration: 0.2 }}
                  >
                    <ModuleForm
                      module={editingModule}
                      onSubmit={editingModule 
                        ? (data) => handleUpdateModule(editingModule.id, data)
                        : handleCreateModule
                      }
                      onCancel={closeRightPanel}
                    />
                  </motion.div>
                ) : rightPanelMode === 'scaffolding-form' ? (
                  <motion.div
                    key="scaffolding-form-panel"
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -20 }}
                    transition={{ duration: 0.2 }}
                  >
                    <ScaffoldingForm
                      scaffolding={editingScaffolding}
                      onSubmit={editingScaffolding 
                        ? (data) => handleUpdateScaffolding(editingScaffolding.id, data)
                        : handleCreateScaffolding
                      }
                      onCancel={() => setRightPanelMode('scaffolding')}
                    />
                  </motion.div>
                ) : (
                  <motion.div
                    key="scaffolding-panel"
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -20 }}
                    transition={{ duration: 0.2 }}
                  >
                    <ScaffoldingPanel
                      scaffoldings={scaffoldings}
                      module={selectedModule}
                      onAdd={() => openScaffoldingFormPanel(null)}
                      onEdit={openScaffoldingFormPanel}
                      onDelete={handleDeleteScaffolding}
                    />
                  </motion.div>
                )}
              </AnimatePresence>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  )
}

const SortableModuleItem = ({ module, onEdit, onDelete, onManageScaffoldings }) => {
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging,
  } = useSortable({ id: module.id })

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0.5 : 1,
  }

  return (
    <div
      ref={setNodeRef}
      style={style}
      className="bg-white border border-gray-200 rounded-lg p-4 shadow-sm hover:shadow-md transition-shadow cursor-grab active:cursor-grabbing"
    >
      <div className="flex justify-between items-start">
        <div className="flex-1" {...attributes} {...listeners}>
          <h3 className="text-lg font-semibold text-gray-800 mb-2">{module.title}</h3>
          {module.description && (
            <p className="text-gray-600 text-sm mb-3">{module.description}</p>
          )}
          <div className="flex flex-wrap gap-2 text-xs">
            <span className="px-2 py-1 bg-blue-100 text-blue-700 rounded">
              순서: {module.order_index}
            </span>
            <span className="px-2 py-1 bg-purple-100 text-purple-700 rounded">
              모드: {module.scaffolding_mode}
            </span>
            <span className={`px-2 py-1 rounded ${module.is_active ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-700'}`}>
              {module.is_active ? '활성' : '비활성'}
            </span>
          </div>
        </div>
        <div className="flex gap-2 ml-4">
          <button
            onClick={(e) => {
              e.stopPropagation()
              onManageScaffoldings(module)
            }}
            className="p-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
            title="스캐폴딩 관리"
          >
            <HiViewList className="text-lg" />
          </button>
          <button
            onClick={(e) => {
              e.stopPropagation()
              onEdit(module)
            }}
            className="p-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition-colors"
            title="수정"
          >
            <HiPencil className="text-lg" />
          </button>
          <button
            onClick={(e) => {
              e.stopPropagation()
              onDelete(module.id)
            }}
            className="p-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
            title="삭제"
          >
            <HiTrash className="text-lg" />
          </button>
        </div>
      </div>
    </div>
  )
}

const ModuleForm = ({ module, onSubmit, onCancel }) => {
  const [formData, setFormData] = useState({
    title: module?.title || '',
    youtube_url: module?.youtube_url || '',
    description: module?.description || '',
    scaffolding_mode: module?.scaffolding_mode || 'none',
    is_active: module?.is_active ?? true,
    learning_enabled: module?.learning_enabled ?? false,
    order_index: module?.order_index || 0,
    survey_url: module?.survey_url || '',
    intro_text: module?.intro_text || ''
  })

  const handleSubmit = (e) => {
    e.preventDefault()
    onSubmit(formData)
  }

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }))
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            제목 *
          </label>
          <input
            type="text"
            name="title"
            value={formData.title}
            onChange={handleChange}
            required
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            YouTube URL *
          </label>
          <input
            type="url"
            name="youtube_url"
            value={formData.youtube_url}
            onChange={handleChange}
            required
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            설명
          </label>
          <textarea
            name="description"
            value={formData.description}
            onChange={handleChange}
            rows={3}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent resize-none"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            학습 모드
          </label>
          <select
            name="scaffolding_mode"
            value={formData.scaffolding_mode}
            onChange={handleChange}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
          >
            <option value="none">없음</option>
            <option value="prompt">프롬프트</option>
            <option value="chat">채팅</option>
          </select>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="flex items-center gap-2">
              <input
                type="checkbox"
                name="is_active"
                checked={formData.is_active}
                onChange={handleChange}
                className="w-4 h-4 text-primary-600 rounded focus:ring-2 focus:ring-primary-500"
              />
              <span className="text-sm font-medium text-gray-700">활성</span>
            </label>
          </div>
          <div>
            <label className="flex items-center gap-2">
              <input
                type="checkbox"
                name="learning_enabled"
                checked={formData.learning_enabled}
                onChange={handleChange}
                className="w-4 h-4 text-primary-600 rounded focus:ring-2 focus:ring-primary-500"
              />
              <span className="text-sm font-medium text-gray-700">학습 가능</span>
            </label>
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            순서
          </label>
          <input
            type="number"
            name="order_index"
            value={formData.order_index}
            onChange={handleChange}
            min="0"
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            설문 URL
          </label>
          <input
            type="url"
            name="survey_url"
            value={formData.survey_url}
            onChange={handleChange}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            도입 텍스트
          </label>
          <textarea
            name="intro_text"
            value={formData.intro_text}
            onChange={handleChange}
            rows={3}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent resize-none"
          />
        </div>
      </div>

      <div className="flex gap-3 justify-end pt-4 border-t sticky bottom-0 bg-white">
        <button
          type="button"
          onClick={onCancel}
          className="px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition-colors"
        >
          취소
        </button>
        <button
          type="submit"
          className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors"
        >
          {module ? '수정' : '추가'}
        </button>
      </div>
    </form>
  )
}

const ScaffoldingPanel = ({ scaffoldings, module, onAdd, onEdit, onDelete }) => {
  return (
    <div className="space-y-4">
      <button
        onClick={onAdd}
        className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
      >
        <HiPlus />
        스캐폴딩 추가
      </button>

      {scaffoldings.length === 0 ? (
        <div className="text-center py-8 text-gray-500">
          등록된 스캐폴딩이 없습니다.
        </div>
      ) : (
        (scaffoldings || []).filter(s => s).map((scaffolding) => (
          <div key={scaffolding.id} className="border rounded-lg p-4 hover:border-primary-300 transition-colors">
            <h3 className="font-semibold text-gray-800 mb-2">{scaffolding.title}</h3>
            {scaffolding.prompt_text && (
              <p className="text-sm text-gray-600 mb-2 line-clamp-2">{scaffolding.prompt_text}</p>
            )}
            <p className="text-xs text-gray-500 mb-3">
              순서: {scaffolding.order_index}
            </p>
            <div className="flex gap-2">
              <button
                onClick={() => onEdit(scaffolding)}
                className="flex-1 px-3 py-1.5 bg-gray-600 text-white rounded hover:bg-gray-700 transition-colors text-sm"
              >
                수정
              </button>
              <button
                onClick={() => onDelete(scaffolding.id)}
                className="flex-1 px-3 py-1.5 bg-red-600 text-white rounded hover:bg-red-700 transition-colors text-sm"
              >
                삭제
              </button>
            </div>
          </div>
        ))
      )}
    </div>
  )
}

const ScaffoldingForm = ({ scaffolding, onSubmit, onCancel }) => {
  const [formData, setFormData] = useState({
    title: scaffolding?.title || '',
    prompt_text: scaffolding?.prompt_text || '',
    order_index: scaffolding?.order_index || 1
  })

  const handleSubmit = (e) => {
    e.preventDefault()
    // order_index를 숫자로 변환
    const submitData = {
      ...formData,
      order_index: parseInt(formData.order_index, 10)
    }
    console.log('Submitting scaffolding form data:', submitData)
    onSubmit(submitData)
  }

  const handleChange = (e) => {
    const { name, value } = e.target
    setFormData(prev => ({
      ...prev,
      [name]: name === 'order_index' ? parseInt(value, 10) || 1 : value
    }))
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          제목 *
        </label>
        <input
          type="text"
          name="title"
          value={formData.title}
          onChange={handleChange}
          required
          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          프롬프트 텍스트
        </label>
        <textarea
          name="prompt_text"
          value={formData.prompt_text}
          onChange={handleChange}
          rows={6}
          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent resize-none"
          placeholder="학습자에게 표시할 질문이나 지시사항을 입력하세요"
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          순서
        </label>
        <input
          type="number"
          name="order_index"
          value={formData.order_index}
          onChange={handleChange}
          min="1"
          required
          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
        />
      </div>

      <div className="flex gap-3 justify-end pt-4 border-t">
        <button
          type="button"
          onClick={onCancel}
          className="px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition-colors"
        >
          취소
        </button>
        <button
          type="submit"
          className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
        >
          {scaffolding ? '수정' : '추가'}
        </button>
      </div>
    </form>
  )
}

export default AdminModules
