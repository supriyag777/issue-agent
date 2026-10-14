import { useEffect, useState } from 'react'
import { Bot, ChevronDown, HelpCircle, Loader2, Send, ShieldCheck, X } from 'lucide-react'
import { useLocation } from 'react-router-dom'
import { api } from '../services/api'

type GuideAnswer = { answer: string; provider_mode: string; suggestions: string[] }

export function GuidePanel() {
  const location = useLocation()
  const [open, setOpen] = useState(false)
  const [question, setQuestion] = useState('')
  const [answer, setAnswer] = useState<GuideAnswer | null>(null)
  const [busy, setBusy] = useState(false)

  useEffect(() => {
    let active = true
    api.guideContext(location.pathname).then(result => { if (active) setAnswer(result) }).catch(() => undefined)
    return () => { active = false }
  }, [location.pathname])

  async function ask(questionText = question) {
    const trimmed = questionText.trim()
    if (!trimmed || busy) return
    setBusy(true)
    try {
      const result = await api.askGuide(trimmed, location.pathname)
      setAnswer(result)
      setQuestion('')
    } finally {
      setBusy(false)
    }
  }

  return <div className={`guide-widget ${open ? 'is-open' : ''}`}>
    {open && <section className="guide-panel panel" aria-label="AI workflow guide">
      <div className="guide-head"><div><div className="eyebrow"><HelpCircle size={13} /> WORKFLOW GUIDE</div><strong>What should I do next?</strong></div><button className="icon-btn" onClick={() => setOpen(false)} aria-label="Close guide"><X size={16} /></button></div>
      <div className="guide-answer"><div className="guide-answer-icon"><ShieldCheck size={15} /></div><div><span className="guide-mode">{answer?.provider_mode === 'openai' ? 'OPENAI GUIDE' : answer?.provider_mode === 'built-in-fallback' ? 'BUILT-IN FALLBACK' : 'BUILT-IN GUIDE'}</span><p>{answer?.answer || 'Loading contextual guidance…'}</p></div></div>
      {!!answer?.suggestions.length && <div className="guide-suggestions">{answer.suggestions.map(suggestion => <button key={suggestion} className="guide-suggestion" onClick={() => ask(suggestion)}>{suggestion}<ChevronDown size={13} /></button>)}</div>}
      <form className="guide-form" onSubmit={event => { event.preventDefault(); void ask() }}><input value={question} onChange={event => setQuestion(event.target.value)} placeholder="Ask the guide…" aria-label="Ask the workflow guide" /><button className="btn btn-ai" type="submit" disabled={busy || !question.trim()} aria-label="Ask guide">{busy ? <Loader2 className="spin" size={15} /> : <Send size={15} />}</button></form>
      <small className="guide-foot">Built-in help always works. OpenAI answers are used only when configured.</small>
    </section>}
    <button className="guide-launcher" onClick={() => setOpen(value => !value)} aria-expanded={open}><Bot size={17} /><span>AI Guide</span>{open ? <X size={14} /> : <HelpCircle size={14} />}</button>
  </div>
}
