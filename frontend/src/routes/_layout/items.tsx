import { useQuery } from "@tanstack/react-query"
import { createFileRoute } from "@tanstack/react-router"
import { useState } from "react"

import { ItemsService, type ItemPublic } from "@/client"
import AddItem from "@/components/Items/AddItem"
import EditItem from "@/components/Items/EditItem"
import DeleteItem from "@/components/Items/DeleteItem"

export const Route = createFileRoute("/_layout/items")({
  component: Items,
})

const colors = [
  '#FF6B6B', // Red
  '#4ECDC4', // Teal
  '#45B7D1', // Blue
  '#FFA07A', // Salmon
  '#98D8C8', // Mint
  '#F7DC6F', // Yellow
  '#BB8FCE', // Purple
  '#85C1E2', // Sky
]

function Items() {
  const { data, isLoading } = useQuery({
    queryFn: () => ItemsService.readItems({ skip: 0, limit: 100 }),
    queryKey: ["items"],
  })

  const items = data?.data ?? []

  const getCategoryColor = (title: string) => {
    const hash = title.split('').reduce((acc, char) => acc + char.charCodeAt(0), 0)
    return colors[hash % colors.length]
  }

  if (isLoading) {
    return (
      <div className="travel-notes-page">
        <div className="notes-header">
          <div>
            <h1 className="notes-title">Travel Notes</h1>
            <p className="notes-subtitle">Loading your notes...</p>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="travel-notes-page">
      <div className="notes-header">
        <div>
          <h1 className="notes-title">Travel Notes</h1>
          <p className="notes-subtitle">Capture your travel ideas, reminders, and checklists</p>
        </div>
        <AddItem />
      </div>

      {items.length === 0 ? (
        <div className="empty-state">
          <div className="empty-icon">✈️</div>
          <h2>No notes yet</h2>
          <p>Start capturing your travel thoughts!</p>
        </div>
      ) : (
        <div className="notes-grid">
          {items.map((item) => {
            const color = getCategoryColor(item.title)
            return <NoteCard key={item.id} item={item} color={color} />
          })}
        </div>
      )}

      <style>{`
        .travel-notes-page {
          width: 100%;
          min-height: calc(100vh - 60px);
          padding: 40px;
          background: linear-gradient(to bottom, #1a1a1a 0%, #0a0a0a 100%);
        }

        .notes-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 40px;
        }

        .notes-title {
          font-size: 36px;
          font-weight: 600;
          color: #ffffff;
          margin: 0 0 8px 0;
          letter-spacing: -0.5px;
        }

        .notes-subtitle {
          font-size: 17px;
          color: #86868b;
          margin: 0;
        }

        .notes-grid {
          display: grid;
          grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
          gap: 24px;
        }

        .empty-state {
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          padding: 80px 40px;
          text-align: center;
        }

        .empty-icon {
          font-size: 80px;
          margin-bottom: 24px;
        }

        .empty-state h2 {
          font-size: 24px;
          font-weight: 600;
          color: #ffffff;
          margin: 0 0 12px 0;
        }

        .empty-state p {
          font-size: 16px;
          color: #86868b;
          margin: 0;
        }

        @media (max-width: 768px) {
          .travel-notes-page {
            padding: 24px;
          }

          .notes-header {
            flex-direction: column;
            align-items: flex-start;
            gap: 20px;
          }

          .notes-title {
            font-size: 28px;
          }

          .notes-grid {
            grid-template-columns: 1fr;
          }
        }
      `}</style>
    </div>
  )
}

function NoteCard({ item, color }: { item: ItemPublic, color: string }) {
  const [isHovered, setIsHovered] = useState(false)

  return (
    <>
      <div 
        className="note-card"
        style={{ '--note-color': color } as React.CSSProperties}
        onMouseEnter={() => setIsHovered(true)}
        onMouseLeave={() => setIsHovered(false)}
      >
        <div className="note-content">
          <h3 className="note-title">{item.title}</h3>
          {item.description && (
            <div 
              className="note-description"
              dangerouslySetInnerHTML={{ __html: item.description.replace(/\n/g, '<br/>') }}
            />
          )}
        </div>

        {isHovered && (
          <div className="note-actions">
            <EditItem item={item} />
            <DeleteItem id={item.id} />
          </div>
        )}
      </div>

      <style>{`
        .note-card {
          position: relative;
          min-height: 280px;
          background: rgba(255, 255, 255, 0.05);
          backdrop-filter: blur(20px);
          border-left: 6px solid var(--note-color);
          border-radius: 8px 16px 16px 8px;
          padding: 20px;
          transition: all 0.3s ease;
          cursor: pointer;
          overflow: hidden;
          box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
        }
        
        .note-card::after {
          content: '';
          position: absolute;
          top: 0;
          left: 0;
          right: 0;
          bottom: 0;
          background: linear-gradient(135deg, var(--note-color)15, transparent);
          pointer-events: none;
        }

        .note-card::before {
          content: '';
          position: absolute;
          top: 0;
          right: 0;
          width: 60px;
          height: 60px;
          background: linear-gradient(135deg, rgba(255, 255, 255, 0.1), transparent);
          border-radius: 0 0 0 60px;
        }

        .note-card:hover {
          transform: translateY(-8px) rotate(-1deg);
          box-shadow: 0 12px 40px rgba(0, 0, 0, 0.5);
        }

        .note-content {
          height: 100%;
          display: flex;
          flex-direction: column;
          position: relative;
          z-index: 1;
        }

        .note-title {
          font-size: 20px;
          font-weight: 600;
          color: #ffffff;
          margin: 0 0 12px 0;
          line-height: 1.3;
        }

        .note-description {
          font-size: 14px;
          color: #e0e0e0;
          line-height: 1.6;
          margin: 0;
          flex: 1;
          overflow: hidden;
          white-space: pre-wrap;
        }

        .note-actions {
          position: absolute;
          top: 16px;
          right: 16px;
          display: flex;
          gap: 8px;
          background: rgba(0, 0, 0, 0.6);
          backdrop-filter: blur(10px);
          padding: 8px;
          border-radius: 8px;
          border: 1px solid rgba(255, 255, 255, 0.1);
          z-index: 10;
        }

        .note-action-btn {
          display: flex;
          align-items: center;
          justify-content: center;
          width: 32px;
          height: 32px;
          background: rgba(255, 255, 255, 0.1);
          border: none;
          border-radius: 6px;
          color: #ffffff;
          cursor: pointer;
          transition: all 0.2s ease;
        }

        .note-action-btn:hover {
          background: rgba(255, 255, 255, 0.2);
          transform: scale(1.1);
        }
      `}</style>
    </>
  )
}

export default Items
