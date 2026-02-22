'use client'

import { useState, useEffect } from 'react'
import { API_BASE_URL } from '../../config/api'

interface KnowledgeEntry {
  id: number
  category: string
  content: string
  is_active: boolean
  sort_order: number
}

interface PendingEntry {
  id: number
  category: string
  content: string
  status: string
  created_at: string
}

const CATEGORIES = [
  'ROLE & SUMMARY',
  'PRONOUNS',
  'TECH STACK',
  'WORK EXPERIENCE',
  'PROJECTS',
  'EDUCATION',
  'OPEN TO',
  'LINKS',
  'PERSONAL',
  'GAMING',
  'OTHER',
]

export default function AdminPage() {
  const [entries, setEntries] = useState<KnowledgeEntry[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [editingId, setEditingId] = useState<number | null>(null)
  const [editForm, setEditForm] = useState({ category: '', content: '', sort_order: 0 })
  const [newForm, setNewForm] = useState({ category: CATEGORIES[0], content: '', sort_order: 0 })
  const [showAdd, setShowAdd] = useState(false)
  const [saving, setSaving] = useState(false)
  const [filterCategory, setFilterCategory] = useState('ALL')
  const [pending, setPending] = useState<PendingEntry[]>([])
  const [activeTab, setActiveTab] = useState<'knowledge' | 'pending'>('knowledge')

  const apiBase = typeof window !== 'undefined' && window.location.hostname === 'localhost'
    ? 'http://localhost:8000'
    : API_BASE_URL

  async function fetchEntries() {
    try {
      const [knowledgeRes, pendingRes] = await Promise.all([
        fetch(`${apiBase}/knowledge`),
        fetch(`${apiBase}/pending-knowledge`),
      ])
      if (!knowledgeRes.ok) throw new Error('Failed to fetch knowledge')
      setEntries(await knowledgeRes.json())
      if (pendingRes.ok) setPending(await pendingRes.json())
    } catch {
      setError('Could not load knowledge entries. Is the backend running?')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { fetchEntries() }, [])

  async function handleApprovePending(id: number) {
    await fetch(`${apiBase}/pending-knowledge/${id}/approve`, { method: 'POST' })
    fetchEntries()
  }

  async function handleDenyPending(id: number) {
    await fetch(`${apiBase}/pending-knowledge/${id}/deny`, { method: 'POST' })
    fetchEntries()
  }

  async function handleToggleActive(entry: KnowledgeEntry) {
    await fetch(`${apiBase}/knowledge/${entry.id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ is_active: !entry.is_active }),
    })
    fetchEntries()
  }

  async function handleDelete(id: number) {
    if (!confirm('Delete this entry?')) return
    await fetch(`${apiBase}/knowledge/${id}`, { method: 'DELETE' })
    fetchEntries()
  }

  async function handleSaveEdit() {
    if (!editingId) return
    setSaving(true)
    await fetch(`${apiBase}/knowledge/${editingId}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(editForm),
    })
    setSaving(false)
    setEditingId(null)
    fetchEntries()
  }

  async function handleAdd() {
    if (!newForm.content.trim()) return
    setSaving(true)
    await fetch(`${apiBase}/knowledge`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(newForm),
    })
    setSaving(false)
    setNewForm({ category: CATEGORIES[0], content: '', sort_order: 0 })
    setShowAdd(false)
    fetchEntries()
  }

  const allCategories = ['ALL', ...Array.from(new Set(entries.map(e => e.category))).sort()]
  const filtered = filterCategory === 'ALL' ? entries : entries.filter(e => e.category === filterCategory)
  const grouped = filtered.reduce<Record<string, KnowledgeEntry[]>>((acc, e) => {
    acc[e.category] = acc[e.category] || []
    acc[e.category].push(e)
    return acc
  }, {})

  const pendingCount = pending.filter(p => p.status === 'pending').length

  return (
    <div className="min-h-screen bg-gray-950 text-gray-100 p-6">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-2xl font-bold text-white">Sasha Admin</h1>
            <p className="text-gray-400 text-sm mt-1">
              Manage what Sasha knows about Erin. Changes take effect on the next chat message.
            </p>
          </div>
          {activeTab === 'knowledge' && (
            <button
              onClick={() => setShowAdd(true)}
              className="px-4 py-2 bg-teal-600 hover:bg-teal-500 text-white rounded-lg font-medium transition-colors focus:outline-none focus:ring-2 focus:ring-teal-400"
            >
              + Add Entry
            </button>
          )}
        </div>

        {/* Tabs */}
        <div className="flex gap-1 mb-6 border-b border-gray-800">
          <button
            onClick={() => setActiveTab('knowledge')}
            className={`px-4 py-2 text-sm font-medium rounded-t-lg transition-colors focus:outline-none focus:ring-2 focus:ring-teal-400 ${
              activeTab === 'knowledge'
                ? 'bg-gray-900 text-teal-400 border border-b-gray-900 border-gray-700'
                : 'text-gray-400 hover:text-white'
            }`}
          >
            Knowledge Base
          </button>
          <button
            onClick={() => setActiveTab('pending')}
            className={`px-4 py-2 text-sm font-medium rounded-t-lg transition-colors focus:outline-none focus:ring-2 focus:ring-teal-400 flex items-center gap-2 ${
              activeTab === 'pending'
                ? 'bg-gray-900 text-teal-400 border border-b-gray-900 border-gray-700'
                : 'text-gray-400 hover:text-white'
            }`}
          >
            Pending Approval
            {pendingCount > 0 && (
              <span className="bg-yellow-500 text-gray-900 text-xs font-bold px-1.5 py-0.5 rounded-full">
                {pendingCount}
              </span>
            )}
          </button>
        </div>

        {error && (
          <div className="bg-red-900/50 border border-red-500 text-red-200 rounded-lg p-4 mb-6">
            {error}
          </div>
        )}

        {/* Pending approval tab */}
        {activeTab === 'pending' && (
          <div>
            {loading ? (
              <div className="text-center py-16 text-gray-400">Loading…</div>
            ) : pending.length === 0 ? (
              <div className="text-center py-16 text-gray-500">No pending requests.</div>
            ) : (
              <div className="flex flex-col gap-3">
                {pending.map(entry => (
                  <div
                    key={entry.id}
                    className={`bg-gray-900 border rounded-xl p-5 ${
                      entry.status === 'pending' ? 'border-yellow-700' :
                      entry.status === 'approved' ? 'border-teal-800 opacity-60' :
                      'border-gray-800 opacity-40'
                    }`}
                  >
                    <div className="flex items-start justify-between gap-4">
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-2">
                          <span className={`text-xs font-bold px-2 py-0.5 rounded-full ${
                            entry.status === 'pending' ? 'bg-yellow-900 text-yellow-300' :
                            entry.status === 'approved' ? 'bg-teal-900 text-teal-300' :
                            'bg-gray-800 text-gray-400'
                          }`}>
                            {entry.status.toUpperCase()}
                          </span>
                          <span className="text-xs text-gray-500">{entry.category}</span>
                        </div>
                        <p className="text-gray-200 text-sm leading-relaxed">{entry.content}</p>
                        <p className="text-xs text-gray-600 mt-2">
                          Proposed {new Date(entry.created_at).toLocaleString()}
                        </p>
                      </div>
                      {entry.status === 'pending' && (
                        <div className="flex flex-col gap-2 flex-shrink-0">
                          <button
                            onClick={() => handleApprovePending(entry.id)}
                            className="px-3 py-1.5 bg-teal-700 hover:bg-teal-600 text-white rounded text-sm font-medium transition-colors focus:outline-none focus:ring-2 focus:ring-teal-400"
                            aria-label="Approve"
                          >
                            ✅ Yes
                          </button>
                          <button
                            onClick={() => handleDenyPending(entry.id)}
                            className="px-3 py-1.5 bg-red-900 hover:bg-red-800 text-white rounded text-sm font-medium transition-colors focus:outline-none focus:ring-2 focus:ring-red-400"
                            aria-label="Deny"
                          >
                            ❌ No
                          </button>
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Knowledge tab */}
        {activeTab === 'knowledge' && (
          <>
        {/* Filter */}
        <div className="flex gap-2 flex-wrap mb-6">
          {allCategories.map(cat => (
            <button
              key={cat}
              onClick={() => setFilterCategory(cat)}
              className={`px-3 py-1 rounded-full text-sm font-medium transition-colors focus:outline-none focus:ring-2 focus:ring-teal-400 ${
                filterCategory === cat
                  ? 'bg-teal-600 text-white'
                  : 'bg-gray-800 text-gray-300 hover:bg-gray-700'
              }`}
            >
              {cat}
            </button>
          ))}
        </div>

        {/* Add form */}
        {showAdd && (
          <div className="bg-gray-900 border border-teal-700 rounded-xl p-5 mb-6">
            <h2 className="text-lg font-semibold text-teal-400 mb-4">New Entry</h2>
            <div className="grid grid-cols-1 gap-3">
              <div>
                <label className="block text-sm text-gray-400 mb-1">Category</label>
                <select
                  value={newForm.category}
                  onChange={e => setNewForm(f => ({ ...f, category: e.target.value }))}
                  className="w-full bg-gray-800 border border-gray-600 rounded-lg px-3 py-2 text-white focus:outline-none focus:ring-2 focus:ring-teal-400"
                >
                  {CATEGORIES.map(c => <option key={c}>{c}</option>)}
                </select>
              </div>
              <div>
                <label className="block text-sm text-gray-400 mb-1">Content</label>
                <textarea
                  value={newForm.content}
                  onChange={e => setNewForm(f => ({ ...f, content: e.target.value }))}
                  rows={3}
                  placeholder="e.g. Software Engineer at Payactiv (2024 – Present): Led architecture of..."
                  className="w-full bg-gray-800 border border-gray-600 rounded-lg px-3 py-2 text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-teal-400 resize-y"
                />
              </div>
            </div>
            <div className="flex gap-3 mt-4">
              <button
                onClick={handleAdd}
                disabled={saving || !newForm.content.trim()}
                className="px-4 py-2 bg-teal-600 hover:bg-teal-500 disabled:opacity-40 text-white rounded-lg font-medium transition-colors focus:outline-none focus:ring-2 focus:ring-teal-400"
              >
                {saving ? 'Saving…' : 'Save'}
              </button>
              <button
                onClick={() => setShowAdd(false)}
                className="px-4 py-2 bg-gray-700 hover:bg-gray-600 text-white rounded-lg font-medium transition-colors focus:outline-none focus:ring-2 focus:ring-gray-400"
              >
                Cancel
              </button>
            </div>
          </div>
        )}

        {/* Entries grouped by category */}
        {loading ? (
          <div className="text-center py-16 text-gray-400">Loading…</div>
        ) : (
          Object.entries(grouped).map(([category, items]) => (
            <div key={category} className="mb-8">
              <h2 className="text-xs font-bold uppercase tracking-widest text-teal-500 mb-3 border-b border-gray-800 pb-2">
                {category}
              </h2>
              <div className="flex flex-col gap-2">
                {items.map(entry => (
                  <div
                    key={entry.id}
                    className={`bg-gray-900 border rounded-lg p-4 transition-opacity ${
                      entry.is_active ? 'border-gray-700 opacity-100' : 'border-gray-800 opacity-50'
                    }`}
                  >
                    {editingId === entry.id ? (
                      <div className="flex flex-col gap-3">
                        <select
                          value={editForm.category}
                          onChange={e => setEditForm(f => ({ ...f, category: e.target.value }))}
                          className="bg-gray-800 border border-gray-600 rounded px-3 py-1.5 text-white text-sm focus:outline-none focus:ring-2 focus:ring-teal-400"
                        >
                          {CATEGORIES.map(c => <option key={c}>{c}</option>)}
                        </select>
                        <textarea
                          value={editForm.content}
                          onChange={e => setEditForm(f => ({ ...f, content: e.target.value }))}
                          rows={3}
                          className="bg-gray-800 border border-gray-600 rounded px-3 py-2 text-white text-sm focus:outline-none focus:ring-2 focus:ring-teal-400 resize-y"
                        />
                        <div className="flex gap-2">
                          <button
                            onClick={handleSaveEdit}
                            disabled={saving}
                            className="px-3 py-1.5 bg-teal-600 hover:bg-teal-500 disabled:opacity-40 text-white rounded text-sm font-medium focus:outline-none focus:ring-2 focus:ring-teal-400"
                          >
                            {saving ? 'Saving…' : 'Save'}
                          </button>
                          <button
                            onClick={() => setEditingId(null)}
                            className="px-3 py-1.5 bg-gray-700 hover:bg-gray-600 text-white rounded text-sm font-medium focus:outline-none focus:ring-2 focus:ring-gray-400"
                          >
                            Cancel
                          </button>
                        </div>
                      </div>
                    ) : (
                      <div className="flex items-start justify-between gap-4">
                        <p className="text-gray-200 text-sm leading-relaxed flex-1">{entry.content}</p>
                        <div className="flex items-center gap-2 flex-shrink-0">
                          <button
                            onClick={() => handleToggleActive(entry)}
                            title={entry.is_active ? 'Disable' : 'Enable'}
                            className={`w-8 h-8 rounded flex items-center justify-center text-sm transition-colors focus:outline-none focus:ring-2 focus:ring-teal-400 ${
                              entry.is_active
                                ? 'bg-teal-900 text-teal-400 hover:bg-teal-800'
                                : 'bg-gray-800 text-gray-500 hover:bg-gray-700'
                            }`}
                            aria-label={entry.is_active ? 'Disable entry' : 'Enable entry'}
                          >
                            {entry.is_active ? '✓' : '○'}
                          </button>
                          <button
                            onClick={() => {
                              setEditingId(entry.id)
                              setEditForm({ category: entry.category, content: entry.content, sort_order: entry.sort_order })
                            }}
                            className="w-8 h-8 rounded bg-gray-800 hover:bg-gray-700 text-gray-400 hover:text-white flex items-center justify-center text-sm transition-colors focus:outline-none focus:ring-2 focus:ring-teal-400"
                            aria-label="Edit entry"
                          >
                            ✎
                          </button>
                          <button
                            onClick={() => handleDelete(entry.id)}
                            className="w-8 h-8 rounded bg-gray-800 hover:bg-red-900 text-gray-400 hover:text-red-400 flex items-center justify-center text-sm transition-colors focus:outline-none focus:ring-2 focus:ring-red-400"
                            aria-label="Delete entry"
                          >
                            ✕
                          </button>
                        </div>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          ))
        )}

        {!loading && entries.length === 0 && (
          <div className="text-center py-16 text-gray-500">
            No knowledge entries yet. Add one above or restart the backend to seed from system_prompt.txt.
          </div>
        )}
          </>
        )}
      </div>
    </div>
  )
}
