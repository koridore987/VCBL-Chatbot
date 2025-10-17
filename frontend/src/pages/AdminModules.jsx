import { useEffect, useState } from 'react'
import CodeMirror from '@uiw/react-codemirror'
import { javascript } from '@codemirror/lang-javascript'
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
} from '@dnd-kit/sortable'
import {
  useSortable,
} from '@dnd-kit/sortable'
import { CSS } from '@dnd-kit/utilities'
import { motion, AnimatePresence } from 'framer-motion'
import api from '../services/api'

// 재사용 가능한 2-Column 레이아웃 컴포넌트
const TwoColumnLayout = ({ 
  leftPanel, 
  rightPanel, 
  showRightPanel, 
  onCloseRightPanel,
  rightPanelTitle,
  rightPanelContent 
}) => {
  return (
    <div style={{ 
      display: 'flex', 
      gap: '20px', 
      height: '80vh',
      minHeight: '600px',
      maxHeight: '800px'
    }}>
      {/* Left Panel */}
      <div style={{ 
        flex: showRightPanel ? '0 0 40%' : '1', 
        display: 'flex', 
        flexDirection: 'column',
        borderRight: showRightPanel ? '1px solid #e5e7eb' : 'none',
        paddingRight: showRightPanel ? '20px' : '0',
        transition: 'all 0.4s ease-in-out'
      }}>
        {leftPanel}
      </div>

      {/* Right Panel */}
      <AnimatePresence>
        {showRightPanel && (
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: 20 }}
            style={{ 
              flex: '1',
              display: 'flex',
              flexDirection: 'column',
              minWidth: '0'
            }}
          >
            <div style={{ 
              display: 'flex', 
              justifyContent: 'space-between', 
              alignItems: 'center',
              marginBottom: '20px',
              paddingBottom: '10px',
              borderBottom: '1px solid #e5e7eb'
            }}>
              <h3 style={{ margin: 0, fontSize: '18px', fontWeight: '600' }}>
                {rightPanelTitle}
              </h3>
              <button
                onClick={onCloseRightPanel}
                style={{
                  background: 'none',
                  border: 'none',
                  fontSize: '20px',
                  cursor: 'pointer',
                  padding: '5px',
                  borderRadius: '4px',
                  color: '#6b7280'
                }}
              >
                ×
              </button>
            </div>
            <div style={{ flex: 1, overflow: 'auto' }}>
              {rightPanelContent}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}

const AdminModules = () => {
  const [activeTab, setActiveTab] = useState('modules')
  const [modules, setModules] = useState([])
  const [loading, setLoading] = useState(true)
  const [editingModule, setEditingModule] = useState(null)
  const [showForm, setShowForm] = useState(false)
  const [selectedModule, setSelectedModule] = useState(null)
  const [scaffoldings, setScaffoldings] = useState([])
  const [showRightPanel, setShowRightPanel] = useState(false)
  const [rightPanelTitle, setRightPanelTitle] = useState('')
  const [rightPanelContent, setRightPanelContent] = useState(null)

  const sensors = useSensors(
    useSensor(PointerSensor),
    useSensor(KeyboardSensor, {
      coordinateGetter: sortableKeyboardCoordinates,
    })
  )

  const fetchModules = async () => {
    try {
      const response = await api.get('/admin/modules')
      setModules(response.data.data || [])
    } catch (error) {
      console.error('Failed to fetch modules:', error)
    }
  }

  const fetchPrompts = async () => {
    try {
      const response = await api.get('/admin/prompts')
      // Handle prompts if needed
    } catch (error) {
      console.error('Failed to fetch prompts:', error)
    }
  }

  useEffect(() => {
    fetchModules()
    fetchPrompts()
  }, [])

  const handleCreateModule = async (moduleData) => {
    try {
      const response = await api.post('/admin/modules', moduleData)
      setModules([...modules, response.data.data])
      setShowForm(false)
    } catch (error) {
      console.error('Failed to create module:', error)
    }
  }

  const handleUpdateModule = async (moduleId, moduleData) => {
    try {
      const response = await api.put(`/admin/modules/${moduleId}`, moduleData)
      setModules(modules.map(m => m.id === moduleId ? response.data.data : m))
      setEditingModule(null)
      setShowForm(false)
    } catch (error) {
      console.error('Failed to update module:', error)
    }
  }

  const handleDeleteModule = async (moduleId) => {
    if (window.confirm('정말로 이 모듈을 삭제하시겠습니까?')) {
      try {
        await api.delete(`/admin/modules/${moduleId}`)
        setModules(modules.filter(m => m.id !== moduleId))
      } catch (error) {
        console.error('Failed to delete module:', error)
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

      // Update order_index in backend
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
        // Revert on error
        fetchModules()
      }
    }
  }

  const openScaffoldingsPanel = async (module) => {
    setSelectedModule(module)
    setRightPanelTitle(`스캐폴딩 관리 - ${module.title}`)
    
    try {
      const response = await api.get(`/admin/modules/${module.id}/scaffoldings`)
      setScaffoldings(response.data.data || [])
    } catch (error) {
      console.error('Failed to fetch scaffoldings:', error)
      setScaffoldings([])
    }
    
    setRightPanelContent(
      <div>
        <div style={{ marginBottom: '20px' }}>
          <button
            onClick={() => {/* Add scaffolding logic */}}
            style={{
              background: '#3b82f6',
              color: 'white',
              border: 'none',
              padding: '8px 16px',
              borderRadius: '6px',
              cursor: 'pointer'
            }}
          >
            스캐폴딩 추가
          </button>
        </div>
        <div>
          {scaffoldings.map((scaffolding, index) => (
            <div key={scaffolding.id} style={{
              border: '1px solid #e5e7eb',
              borderRadius: '6px',
              padding: '12px',
              marginBottom: '8px'
            }}>
              <h4 style={{ margin: '0 0 8px 0' }}>{scaffolding.title}</h4>
              <p style={{ margin: '0 0 8px 0', color: '#6b7280' }}>
                순서: {scaffolding.order_index}
              </p>
              <div style={{ display: 'flex', gap: '8px' }}>
                <button
                  onClick={() => {/* Edit scaffolding logic */}}
                  style={{
                    background: '#6b7280',
                    color: 'white',
                    border: 'none',
                    padding: '4px 8px',
                    borderRadius: '4px',
                    cursor: 'pointer',
                    fontSize: '12px'
                  }}
                >
                  수정
                </button>
                <button
                  onClick={() => {/* Delete scaffolding logic */}}
                  style={{
                    background: '#ef4444',
                    color: 'white',
                    border: 'none',
                    padding: '4px 8px',
                    borderRadius: '4px',
                    cursor: 'pointer',
                    fontSize: '12px'
                  }}
                >
                  삭제
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>
    )
    setShowRightPanel(true)
  }

  const closeRightPanel = () => {
    setShowRightPanel(false)
    setSelectedModule(null)
    setScaffoldings([])
    setRightPanelContent(null)
  }

  const leftPanel = (
    <div>
      <div style={{ 
        display: 'flex', 
        justifyContent: 'space-between', 
        alignItems: 'center',
        marginBottom: '20px'
      }}>
        <h2 style={{ margin: 0 }}>모듈 관리</h2>
        <button
          onClick={() => {
            setEditingModule(null)
            setShowForm(true)
          }}
          style={{
            background: '#3b82f6',
            color: 'white',
            border: 'none',
            padding: '8px 16px',
            borderRadius: '6px',
            cursor: 'pointer'
          }}
        >
          모듈 추가
        </button>
      </div>

      {showForm && (
        <ModuleForm
          module={editingModule}
          onSubmit={editingModule ? 
            (data) => handleUpdateModule(editingModule.id, data) :
            handleCreateModule
          }
          onCancel={() => {
            setShowForm(false)
            setEditingModule(null)
          }}
        />
      )}

      <DndContext
        sensors={sensors}
        collisionDetection={closestCenter}
        onDragEnd={handleDragEnd}
      >
        <SortableContext
          items={modules.map(m => m.id)}
          strategy={verticalListSortingStrategy}
        >
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            {modules.map((module) => (
              <SortableModuleItem
                key={module.id}
                module={module}
                onEdit={(module) => {
                  setEditingModule(module)
                  setShowForm(true)
                }}
                onDelete={handleDeleteModule}
                onManageScaffoldings={openScaffoldingsPanel}
              />
            ))}
          </div>
        </SortableContext>
      </DndContext>
    </div>
  )

  return (
    <div style={{ padding: '20px' }}>
      <TwoColumnLayout
        leftPanel={leftPanel}
        rightPanel={null}
        showRightPanel={showRightPanel}
        onCloseRightPanel={closeRightPanel}
        rightPanelTitle={rightPanelTitle}
        rightPanelContent={rightPanelContent}
      />
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
      style={{
        ...style,
        border: '1px solid #e5e7eb',
        borderRadius: '8px',
        padding: '16px',
        background: 'white',
        cursor: 'grab',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center'
      }}
      {...attributes}
      {...listeners}
    >
      <div style={{ flex: 1 }}>
        <h3 style={{ margin: '0 0 8px 0', fontSize: '16px' }}>{module.title}</h3>
        <p style={{ margin: '0 0 8px 0', color: '#6b7280', fontSize: '14px' }}>
          {module.description}
        </p>
        <div style={{ display: 'flex', gap: '8px', fontSize: '12px', color: '#6b7280' }}>
          <span>순서: {module.order_index}</span>
          <span>•</span>
          <span>모드: {module.scaffolding_mode}</span>
          <span>•</span>
          <span>{module.is_active ? '활성' : '비활성'}</span>
        </div>
      </div>
      <div style={{ display: 'flex', gap: '8px' }}>
        <button
          onClick={(e) => {
            e.stopPropagation()
            onManageScaffoldings(module)
          }}
          style={{
            background: '#10b981',
            color: 'white',
            border: 'none',
            padding: '6px 12px',
            borderRadius: '4px',
            cursor: 'pointer',
            fontSize: '12px'
          }}
        >
          스캐폴딩
        </button>
        <button
          onClick={(e) => {
            e.stopPropagation()
            onEdit(module)
          }}
          style={{
            background: '#6b7280',
            color: 'white',
            border: 'none',
            padding: '6px 12px',
            borderRadius: '4px',
            cursor: 'pointer',
            fontSize: '12px'
          }}
        >
          수정
        </button>
        <button
          onClick={(e) => {
            e.stopPropagation()
            onDelete(module.id)
          }}
          style={{
            background: '#ef4444',
            color: 'white',
            border: 'none',
            padding: '6px 12px',
            borderRadius: '4px',
            cursor: 'pointer',
            fontSize: '12px'
          }}
        >
          삭제
        </button>
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
    <div style={{
      border: '1px solid #e5e7eb',
      borderRadius: '8px',
      padding: '20px',
      marginBottom: '20px',
      background: 'white'
    }}>
      <h3 style={{ margin: '0 0 16px 0' }}>
        {module ? '모듈 수정' : '새 모듈 추가'}
      </h3>
      <form onSubmit={handleSubmit}>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px', marginBottom: '16px' }}>
          <div>
            <label style={{ display: 'block', marginBottom: '4px', fontSize: '14px', fontWeight: '500' }}>
              제목 *
            </label>
            <input
              type="text"
              name="title"
              value={formData.title}
              onChange={handleChange}
              required
              style={{
                width: '100%',
                padding: '8px',
                border: '1px solid #d1d5db',
                borderRadius: '4px',
                fontSize: '14px'
              }}
            />
          </div>
          <div>
            <label style={{ display: 'block', marginBottom: '4px', fontSize: '14px', fontWeight: '500' }}>
              YouTube URL *
            </label>
            <input
              type="url"
              name="youtube_url"
              value={formData.youtube_url}
              onChange={handleChange}
              required
              style={{
                width: '100%',
                padding: '8px',
                border: '1px solid #d1d5db',
                borderRadius: '4px',
                fontSize: '14px'
              }}
            />
          </div>
        </div>

        <div style={{ marginBottom: '16px' }}>
          <label style={{ display: 'block', marginBottom: '4px', fontSize: '14px', fontWeight: '500' }}>
            학습 모드
          </label>
          <select
            name="scaffolding_mode"
            value={formData.scaffolding_mode}
            onChange={handleChange}
            style={{
              width: '100%',
              padding: '8px',
              border: '1px solid #d1d5db',
              borderRadius: '4px',
              fontSize: '14px'
            }}
          >
            <option value="none">없음</option>
            <option value="prompt">프롬프트</option>
            <option value="chat">채팅</option>
          </select>
        </div>

        <div style={{ marginBottom: '16px' }}>
          <label style={{ display: 'block', marginBottom: '4px', fontSize: '14px', fontWeight: '500' }}>
            설명
          </label>
          <textarea
            name="description"
            value={formData.description}
            onChange={handleChange}
            rows={3}
            style={{
              width: '100%',
              padding: '8px',
              border: '1px solid #d1d5db',
              borderRadius: '4px',
              fontSize: '14px',
              resize: 'vertical'
            }}
          />
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '16px', marginBottom: '16px' }}>
          <div>
            <label style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <input
                type="checkbox"
                name="is_active"
                checked={formData.is_active}
                onChange={handleChange}
              />
              <span style={{ fontSize: '14px' }}>활성</span>
            </label>
          </div>
          <div>
            <label style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <input
                type="checkbox"
                name="learning_enabled"
                checked={formData.learning_enabled}
                onChange={handleChange}
              />
              <span style={{ fontSize: '14px' }}>학습 가능</span>
            </label>
          </div>
          <div>
            <label style={{ display: 'block', marginBottom: '4px', fontSize: '14px', fontWeight: '500' }}>
              순서
            </label>
            <input
              type="number"
              name="order_index"
              value={formData.order_index}
              onChange={handleChange}
              min="0"
              style={{
                width: '100%',
                padding: '8px',
                border: '1px solid #d1d5db',
                borderRadius: '4px',
                fontSize: '14px'
              }}
            />
          </div>
        </div>

        <div style={{ marginBottom: '16px' }}>
          <label style={{ display: 'block', marginBottom: '4px', fontSize: '14px', fontWeight: '500' }}>
            설문 URL
          </label>
          <input
            type="url"
            name="survey_url"
            value={formData.survey_url}
            onChange={handleChange}
            style={{
              width: '100%',
              padding: '8px',
              border: '1px solid #d1d5db',
              borderRadius: '4px',
              fontSize: '14px'
            }}
          />
        </div>

        <div style={{ marginBottom: '16px' }}>
          <label style={{ display: 'block', marginBottom: '4px', fontSize: '14px', fontWeight: '500' }}>
            도입 텍스트
          </label>
          <textarea
            name="intro_text"
            value={formData.intro_text}
            onChange={handleChange}
            rows={3}
            style={{
              width: '100%',
              padding: '8px',
              border: '1px solid #d1d5db',
              borderRadius: '4px',
              fontSize: '14px',
              resize: 'vertical'
            }}
          />
        </div>

        <div style={{ display: 'flex', gap: '8px', justifyContent: 'flex-end' }}>
          <button
            type="button"
            onClick={onCancel}
            style={{
              background: '#6b7280',
              color: 'white',
              border: 'none',
              padding: '8px 16px',
              borderRadius: '6px',
              cursor: 'pointer'
            }}
          >
            취소
          </button>
          <button
            type="submit"
            style={{
              background: '#3b82f6',
              color: 'white',
              border: 'none',
              padding: '8px 16px',
              borderRadius: '6px',
              cursor: 'pointer'
            }}
          >
            {module ? '수정' : '추가'}
          </button>
        </div>
      </form>
    </div>
  )
}

export default AdminModules




