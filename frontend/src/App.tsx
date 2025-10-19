import React, { useCallback, useEffect, useRef, useState } from 'react'

type StatusResp = { status: string; progress: number; message: string; started_at?: string; finished_at?: string }

type ResultItem = { filename: string; size_bytes: number; download_url: string }

const API_BASE = import.meta.env.VITE_API_BASE || '' // same origin by default (vite proxy recommended)

function bytesToMB(n: number) { return (n / (1024*1024)).toFixed(2) }

export default function App() {
  // Fixed required inputs mapping
  const REQUIRED_KEYS = [
    'centrale',
    'succursale',
    'tabella_aule',
    'tabella_classi',
    'tabella_materie',
    'tabella_sostegno',
  ] as const
  type Key = typeof REQUIRED_KEYS[number]
  const NAMING: Record<Key, string> = {
    centrale: 'centrale.xlsx',
    succursale: 'succursale.xlsx',
    tabella_aule: 'tabella_aule.xlsx',
    tabella_classi: 'tabella_classi.xlsx',
    tabella_materie: 'tabella_materie.xlsx',
    tabella_sostegno: 'tabella_sostegno.xlsx',
  }
  const [inputs, setInputs] = useState<Record<Key, File | null>>({
    centrale: null,
    succursale: null,
    tabella_aule: null,
    tabella_classi: null,
    tabella_materie: null,
    tabella_sostegno: null,
  })
  const [sessionId, setSessionId] = useState<string>('')
  const [jobId, setJobId] = useState<string>('')
  const [status, setStatus] = useState<StatusResp | null>(null)
  const [logText, setLogText] = useState<string>('')
  const [results, setResults] = useState<ResultItem[]>([])
  const [options, setOptions] = useState<any>({ check_schema: false, locale: 'it', header_text: '' })
  const [error, setError] = useState<string>('')
  const [uploadMsg, setUploadMsg] = useState<string>('')
  const [runMsg, setRunMsg] = useState<string>('')
  const [isUploading, setUploading] = useState<boolean>(false)
  const [committedHeader, setCommittedHeader] = useState<string>('')
  const [headerMsg, setHeaderMsg] = useState<string>('')
  const pollRef = useRef<number | null>(null)

  // Remove DnD multi-upload in favor of fixed slots
  const onDrop = useCallback((e: React.DragEvent) => { e.preventDefault() }, [])

  function setFileFor(k: Key, f: File | null) {
    setInputs(prev => ({ ...prev, [k]: f }))
  }

  async function doUpload() {
    if (isUploading) return
    setError(''); setUploadMsg(''); setRunMsg(''); setSessionId(''); setJobId(''); setStatus(null); setLogText(''); setResults([])
    // Validate presence of all required files and extension
    for (const k of REQUIRED_KEYS) {
      const f = inputs[k]
      if (!f) { setError('Manca il file: ' + k.replace('_',' ')); return }
      if (!f.name.toLowerCase().endsWith('.xlsx')) { setError('Estensione non valida per ' + k + ': ' + f.name); return }
    }
    // Build form data with expected filenames for backend mapping
    const fd = new FormData()
    for (const k of REQUIRED_KEYS) {
      const f = inputs[k] as File
      // Pass explicit filename to FormData so server sees the standardized name
      fd.append('files', f, NAMING[k])
    }
    const url = `${API_BASE}/upload`
    try {
      setUploading(true)
      console.log('[Upload] URL:', url)
      console.log('[Upload] Files:', REQUIRED_KEYS.map(k=>`${NAMING[k]} <= ${inputs[k]?.name}`))
      const res = await fetch(url, { method: 'POST', body: fd })
      const text = await res.text()
      if (!res.ok) {
        console.error('[Upload] Failed', res.status, text)
        setError(`Upload fallito (${res.status}): ${text}`)
        return
      }
      let data: any
      try { data = JSON.parse(text) } catch {
        console.warn('[Upload] Non-JSON response, raw text:', text)
        setError('Risposta non valida dal server durante upload')
        return
      }
      console.log('[Upload] Success. session_id=', data.session_id)
      setSessionId(data.session_id)
      setUploadMsg('Caricamento effettuato correttamente')
    } catch (e: any) {
      console.error('[Upload] Exception', e)
      setError(`Errore di rete durante upload: ${e?.message || e}`)
    } finally {
      setUploading(false)
    }
  }

  async function runJob() {
    if (!sessionId) { setError('Sessione non valida'); return }
    if (!options.header_text || !String(options.header_text).trim()) { setError('Imposta l\'Header nei Parametri'); return }
    const optsToSend = { ...options, header_text: committedHeader }
    const res = await fetch(`${API_BASE}/run`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ session_id: sessionId, options: optsToSend }) })
    if (!res.ok) { setError('Avvio job fallito'); return }
    const data = await res.json(); setJobId(data.job_id); setRunMsg('Programma lanciato correttamente')
  }

  async function poll() {
    if (!jobId) return
    const sres = await fetch(`${API_BASE}/status/${jobId}`)
    if (sres.ok) {
      const s: StatusResp = await sres.json(); setStatus(s)
      const lres = await fetch(`${API_BASE}/logs/${jobId}`)
      if (lres.ok) setLogText(await lres.text())
      if (s.status === 'succeeded') {
        const rres = await fetch(`${API_BASE}/results/${jobId}`)
        if (rres.ok) setResults(await rres.json())
        stopPolling()
      } else if (s.status === 'failed') {
        stopPolling();
      }
    }
  }

  function startPolling() {
    if (pollRef.current) return
    pollRef.current = window.setInterval(poll, 2500)
  }

  function stopPolling() {
    if (pollRef.current) { window.clearInterval(pollRef.current); pollRef.current = null }
  }

  useEffect(() => {
    if (jobId) { startPolling(); poll() }
    return () => stopPolling()
  }, [jobId])

  function resetForNewRun() {
    setInputs({
      centrale: null,
      succursale: null,
      tabella_aule: null,
      tabella_classi: null,
      tabella_materie: null,
      tabella_sostegno: null,
    });
    setSessionId(''); setJobId(''); setStatus(null); setLogText(''); setResults([]); setError(''); setUploadMsg(''); setRunMsg(''); setCommittedHeader(''); setHeaderMsg('')
  }

  const cleanLogText = (logText || '').replace(/^=== Job.*$\n?/gm, '').replace(/^Inputs:.*$\n?/gm, '')

  return (
    <div className="container">
      <h1>App Orario</h1>

      <section className="card">
        <h2>Upload</h2>
        <p>
          Carica i sei file richiesti. Ogni volta che ne carichi uno la riga corrispondente mostrerà una spunta verde. Per ogni file richiesto è possibile scaricare un esempio cliccando sul pulsante nella riga corrispondente, così da rispettare la struttura e la formattazione richiesta.
        </p>
        <div className="upload-rows">
          {([
            {k:'centrale', label:'Centrale.xlsx'},
            {k:'succursale', label:'Succursale.xlsx'},
            {k:'tabella_aule', label:'Tabella_Aule.xlsx'},
            {k:'tabella_classi', label:'Tabella_Classi.xlsx'},
            {k:'tabella_materie', label:'Tabella_Materie.xlsx'},
            {k:'tabella_sostegno', label:'Tabella_Sostegno.xlsx'},
          ] as {k: Key, label: string}[]).map(row => (
            <div key={row.k} className={`upload-row ${inputs[row.k] ? 'filled' : ''}`}>
              <div><b>{row.label}</b></div>
              <div style={{display:'flex', alignItems:'center', gap:12}}>
                <input style={{width:'50%'}} type="file" accept=".xlsx" onChange={(e: React.ChangeEvent<HTMLInputElement>)=>{
                  const f = (e.target.files && e.target.files[0]) || null
                  setFileFor(row.k, f)
                }} />
                {inputs[row.k] && <div className="muted">{inputs[row.k]?.name} — {bytesToMB(inputs[row.k]!.size)} MB</div>}
              </div>
              <div style={{display:'flex', alignItems:'center', gap:8, justifyContent:'flex-end'}}>
                {inputs[row.k] ? <span className="ok">✔</span> : <span className="dash">—</span>}
                {inputs[row.k] && <button className="btn-secondary" onClick={()=>setFileFor(row.k as Key, null)}>Rimuovi</button>}
                <a href={`${API_BASE}/examples/${NAMING[row.k as Key]}`} download><button className="btn-secondary">Esempio</button></a>
              </div>
            </div>
          ))}
        </div>
        <div style={{marginTop:12}}>
          <button onClick={doUpload} disabled={isUploading || !REQUIRED_KEYS.every(k=>!!inputs[k])}>{isUploading ? 'Caricamento...' : 'Carica'}</button>
          {uploadMsg && <div className="alert success" style={{marginTop:8}}>{uploadMsg}</div>}
        </div>
      </section>

      <section className="card">
        <h2>Parametri</h2>
        <div style={{marginTop:8}}>
          <label>Header (intestazione da stampare negli Excel): </label>
          <input
            type="text"
            value={options.header_text || ''}
            onChange={(e: React.ChangeEvent<HTMLInputElement>)=>{ setOptions((o:any)=>({...o, header_text: e.target.value})); setCommittedHeader(''); setHeaderMsg(''); }}
            placeholder="Es: I.I.S. Via dei Papareschi - Orario valido dal ..."
            style={{width:'100%', padding:'6px', boxSizing:'border-box', marginTop:12}}
          />
        </div>
        <div style={{marginTop:8}}>
          <button className="btn-secondary" disabled={!sessionId || !String(options.header_text||'').trim()} onClick={()=>{
            const txt = String(options.header_text||'').trim()
            if (!txt) return
            setCommittedHeader(txt)
            setHeaderMsg('Intestazione impostata correttamente')
          }}>Imposta</button>
          {headerMsg && <div className="alert success" style={{marginTop:8}}>{headerMsg}</div>}
        </div>
      </section>

      <section className="card">
        <h2>Esecuzione</h2>
        <div style={{marginTop:4}}>
          <button onClick={runJob} disabled={!sessionId || !committedHeader || !String(committedHeader).trim()}>Esegui</button>
          {runMsg && <div className="alert success" style={{marginTop:8}}>{runMsg}</div>}
        </div>
      </section>

      {status && (
        <section className="card">
          <h2>Stato</h2>
          <div style={{display:'flex', alignItems:'center', gap:12}}>
            <div className="progress" style={{flex:1}}>
              <div className="bar" style={{width:`${status.progress}%`, background: status.status==='failed'?'#f66':undefined}} />
            </div>
            <div>{status.progress}%</div>
          </div>
          {status.status === 'succeeded' && (
            <div className="alert success" style={{marginTop:8}}>Programma terminato correttamente</div>
          )}
          {status.status !== 'succeeded' && status.status !== 'failed' && (
            <div className="muted" style={{marginTop:8}}>{status.message}</div>
          )}
          {status.status === 'failed' && (
            <>
              <div className="muted" style={{marginTop:8}}>{status.message}</div>
              <pre style={{background:'#f6fbf7', padding:12, borderRadius:10, border:'1px solid var(--border)', maxHeight:240, overflow:'auto'}}>{cleanLogText}</pre>
            </>
          )}
        </section>
      )}

      {results.length>0 && (
        <section className="card">
          <h2>Risultati</h2>
          <div style={{marginBottom:8}}>
            <a href={`${API_BASE}/download/${jobId}/all.zip`}><button>Scarica tutto (.zip)</button></a>
          </div>
          <table className="results-table">
            <thead>
              <tr>
                <th className="col-name">Nome</th>
                <th className="col-size">Dimensione</th>
                <th className="col-actions">Azioni</th>
              </tr>
            </thead>
            <tbody>
              {results.map((r, i)=> (
                <tr key={i}>
                  <td className="col-name">{r.filename}</td>
                  <td className="col-size">{bytesToMB(r.size_bytes)} MB</td>
                  <td className="col-actions">
                    <a href={`${API_BASE}${r.download_url}`}><button>Download</button></a>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          <div style={{marginTop:12}}>
            <button onClick={resetForNewRun}>Nuova esecuzione</button>
          </div>
        </section>
      )}
    </div>
  )
}
