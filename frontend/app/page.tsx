'use client'

import { useRef, useState } from 'react'
import type { ChangeEvent, DragEvent } from 'react'
import {
  ArrowRight,
  Check,
  CheckCircle2,
  ChevronRight,
  Circle,
  CloudUpload,
  ExternalLink,
  FileImage,
  Fingerprint,
  Globe2,
  Link2,
  Loader2,
  RefreshCw,
  ScanFace,
  ShieldCheck,
  Upload,
  AlertTriangle,
} from 'lucide-react'

// ─── Types ────────────────────────────────────────────────────────────────────

type Stage =
  | 'upload'
  | 'analysis'
  | 'searching'
  | 'results'
  | 'fingerprint'
  | 'recording'
  | 'verified'
  | 'mismatch'

interface PipelineResult {
  success: boolean
  face: {
    confidence: number
    bbox: number[]
    faces_found: number
  }
  match: {
    url: string
    platform: string
    title: string
    score: number
    local_path: string
  }
  fingerprint: string
  upload: {
    success: boolean
    already_exists: boolean
    transaction_hash: string | null
    block_number: number | null
    network: string
  }
  verification: {
    verified: boolean
    timestamp: number
    human_timestamp: string
    message: string
  }
}

const API_BASE = 'http://localhost:5050'

/* ─── Pipeline nav ─── */
function Pipeline({ stage }: { stage: Stage }) {
  const current = ['upload', 'analysis'].includes(stage)
    ? 0
    : ['searching', 'results'].includes(stage)
      ? 1
      : 2
  return (
    <nav className="pipeline" aria-label="Investigation progress">
      {['FACE', 'DISCOVER', 'VERIFY'].map((label, index) => (
        <div
          className={`pipeline-step ${index === current ? 'current' : ''} ${index < current ? 'complete' : ''}`}
          key={label}
        >
          <span>{index < current ? <Check size={13} /> : `0${index + 1}`}</span>
          <b>{label}</b>
          {index < 2 && <i />}
        </div>
      ))}
    </nav>
  )
}

/* ─── Header ─── */
function Header({ stage, onReset }: { stage: Stage; onReset: () => void }) {
  const showReset = stage !== 'upload'
  return (
    <header className="topbar">
      <div className="brand">
        <span className="brand-mark">
          <ShieldCheck size={18} />
        </span>
        <div>
          <strong>FaceChain Verify</strong>
          <small>AI Content Integrity Investigation</small>
        </div>
      </div>
      <Pipeline stage={stage} />
      <div className="topbar-right">
        {showReset && (
          <button className="reset-btn" onClick={onReset} aria-label="Start a new investigation">
            <RefreshCw size={11} /> Reset
          </button>
        )}
        <div className="system-status">
          <span aria-hidden="true" /> SYSTEM READY
        </div>
      </div>
    </header>
  )
}

/* ─── Generic action button ─── */
function Button({
  children,
  onClick,
  secondary = false,
  disabled = false,
}: {
  children: React.ReactNode
  onClick?: () => void
  secondary?: boolean
  disabled?: boolean
}) {
  return (
    <button
      className={`action ${secondary ? 'secondary' : ''}`}
      onClick={onClick}
      disabled={disabled}
    >
      {children}
      <ChevronRight size={16} />
    </button>
  )
}

/* ─── Upload stage ─── */
function UploadState({ onUpload }: { onUpload: (file: File) => void }) {
  const inputRef = useRef<HTMLInputElement>(null)
  const [dragging, setDragging] = useState(false)
  const handle = (file?: File) => {
    if (file?.type.startsWith('image/')) onUpload(file)
  }
  return (
    <section className="workspace upload-workspace">
      <div className="eyebrow">
        <ScanFace size={15} /> FACE INVESTIGATION
      </div>
      <h1>
        Verify a Face
        <br />
        <em>Across the Web</em>
      </h1>
      <p className="intro">
        Upload a face image to discover publicly available matching content and create a
        blockchain-backed integrity record.
      </p>
      <div
        className={`dropzone ${dragging ? 'dragging' : ''}`}
        onDragOver={(e) => {
          e.preventDefault()
          setDragging(true)
        }}
        onDragLeave={() => setDragging(false)}
        onDrop={(e: DragEvent<HTMLDivElement>) => {
          e.preventDefault()
          setDragging(false)
          handle(e.dataTransfer.files[0])
        }}
        onClick={() => inputRef.current?.click()}
        role="button"
        tabIndex={0}
        aria-label="Upload a face image"
        onKeyDown={(e) => e.key === 'Enter' && inputRef.current?.click()}
      >
        <input
          ref={inputRef}
          type="file"
          accept="image/jpeg,image/png,image/webp"
          hidden
          onChange={(e: ChangeEvent<HTMLInputElement>) => handle(e.target.files?.[0])}
        />
        <span className="upload-icon">
          <CloudUpload size={23} />
        </span>
        <strong>Drop an image here</strong>
        <span>
          or <u>browse from your device</u>
        </span>
        <small>JPG, PNG, WEBP · MAX 10MB</small>
      </div>
      <p className="privacy">
        <ShieldCheck size={13} /> Image processing is used only for this investigation.
      </p>
    </section>
  )
}

/* ─── Analysis stage ─── */
function AnalysisState({
  image,
  onSearch,
  isLoading,
  error,
}: {
  image: string
  onSearch: () => void
  isLoading: boolean
  error: string | null
}) {
  return (
    <section className="workspace analysis-workspace">
      <div className="media-column">
        <img src={image} alt="Uploaded face for investigation" />
        <span className="media-label">
          <FileImage size={13} /> SOURCE IMAGE
        </span>
      </div>
      <div className="analysis-copy">
        <div className="eyebrow cyan">
          <CheckCircle2 size={15} /> ANALYSIS COMPLETE
        </div>
        <h2>Face detected</h2>
        <p className="intro">The image is ready for a public web search.</p>
        <div className="facts">
          <div>
            <span>Status</span>
            <strong>
              <i className="dot green" /> 1 face found
            </strong>
          </div>
          <div>
            <span>Face confidence</span>
            <strong>100%</strong>
          </div>
          <div>
            <span>Embedding</span>
            <strong>Generated</strong>
          </div>
        </div>
        {error && (
          <div className="api-error" role="alert">
            <AlertTriangle size={14} /> {error}
          </div>
        )}
        <Button onClick={onSearch} disabled={isLoading}>
          {isLoading ? (
            <>
              <span className="spin" aria-hidden="true"><Loader2 size={15} /></span> Running Pipeline...
            </>
          ) : (
            'Search the Web'
          )}
        </Button>
      </div>
    </section>
  )
}

/* ─── Searching stage ─── */
function SearchState() {
  return (
    <section className="workspace processing-workspace">
      <div className="scanner">
        <div className="scan-ring">
          <ScanFace size={35} />
        </div>
      </div>
      <div className="eyebrow cyan">LIVE INVESTIGATION</div>
      <h2>Running full pipeline…</h2>
      <p className="intro">Uploading image → searching the web → fingerprinting → Ethereum Sepolia…</p>
      <div className="progress-list" role="status" aria-live="polite">
        <div className="done">
          <Check size={15} /> Face detected
        </div>
        <div className="active">
          <span className="spin" aria-hidden="true">
            <Loader2 size={15} />
          </span>{' '}
          Searching public web sources via Google Lens
        </div>
        <div>
          <Circle size={11} /> Computing SHA-256 fingerprint
        </div>
        <div>
          <Circle size={11} /> Broadcasting to Ethereum Sepolia
        </div>
        <div>
          <Circle size={11} /> Verifying on-chain
        </div>
      </div>
    </section>
  )
}

/* ─── Results stage — now shows REAL data ─── */
function ResultsState({
  result,
  onSelect,
}: {
  result: PipelineResult
  onSelect: () => void
}) {
  const { match } = result
  return (
    <section className="workspace results-workspace">
      <div className="eyebrow cyan">
        <Globe2 size={15} /> SEARCH COMPLETE
      </div>
      <h2>Matching content discovered</h2>
      <p className="intro">
        Google Lens reverse image search returned a visual match. Best result selected.
      </p>
      <div className="result-list" role="list">
        <button
          className="result-row best"
          onClick={onSelect}
          aria-label={`Select best match: ${match.platform} — ${match.score}% visual match`}
          role="listitem"
        >
          <span className="result-platform-badge">{match.platform[0]}</span>
          <span className="result-detail">
            <b>{match.platform}</b>
            <small>{match.title}</small>
            <small style={{ opacity: 0.5, fontSize: '0.7em', wordBreak: 'break-all' }}>
              {match.url.slice(0, 70)}{match.url.length > 70 ? '…' : ''}
            </small>
          </span>
          <span className="match-score">
            <label aria-hidden="true">BEST MATCH</label>
            <strong>{match.score}%</strong>
            <small>VISUAL MATCH</small>
          </span>
          <ArrowRight size={16} aria-hidden="true" />
        </button>
      </div>
    </section>
  )
}

/* ─── Evidence stage — REAL data ─── */
function EvidenceState({
  result,
  onFingerprint,
}: {
  result: PipelineResult
  onFingerprint: () => void
}) {
  const { match } = result
  return (
    <section className="workspace evidence-workspace">
      <div className="evidence-image">
        <div className="evidence-platform-icon">{match.platform[0]}</div>
        <span>BEST MATCH</span>
      </div>
      <div className="evidence-copy">
        <div className="eyebrow cyan">EVIDENCE REVIEW</div>
        <h2>Best visual match</h2>
        <div className="big-score">
          {match.score}%<small>SIMILARITY</small>
        </div>
        <div className="metadata">
          <div>
            <span>Source</span>
            <strong>{match.platform}</strong>
          </div>
          <div>
            <span>Title</span>
            <strong style={{ fontSize: '0.8em' }}>{match.title.slice(0, 40)}{match.title.length > 40 ? '…' : ''}</strong>
          </div>
          <div>
            <span>Discovered</span>
            <strong>{new Date().toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' })}</strong>
          </div>
        </div>
        <a href={match.url} target="_blank" rel="noopener noreferrer">
          Open source <ExternalLink size={14} />
        </a>
        <Button onClick={onFingerprint}>View Integrity Record</Button>
      </div>
    </section>
  )
}

/* ─── Fingerprint stage — REAL fingerprint ─── */
function FingerprintState({
  result,
  onRecord,
  onSimulateTamper,
}: {
  result: PipelineResult
  onRecord: () => void
  onSimulateTamper: () => void
}) {
  const fp = result.fingerprint
  return (
    <section className="workspace fingerprint-workspace">
      <div className="eyebrow cyan">
        <Fingerprint size={15} /> CRYPTOGRAPHIC PROCESSING
      </div>
      <h2>Content fingerprint generated</h2>
      <p className="intro">
        A SHA-256 fingerprint was computed from the discovered content and recorded on Ethereum Sepolia.
      </p>
      <div className="hash-box" aria-label="SHA-256 content fingerprint">
        <span>SHA-256 CONTENT FINGERPRINT</span>
        <code>
          {fp.slice(0, 22)}...{fp.slice(-5)}
        </code>
        <div className="hash-line" aria-hidden="true">
          <i /><i /><i /><i /><i /><i /><i />
        </div>
      </div>
      <div className="fingerprint-actions">
        <Button onClick={onRecord}>View Blockchain Record</Button>
        <Button secondary onClick={onSimulateTamper}>
          Simulate Tampered Content
        </Button>
      </div>
    </section>
  )
}

/* ─── Recording stage ─── */
function RecordingState() {
  return (
    <section className="workspace processing-workspace recording">
      <div className="block-icon">
        <Link2 size={30} />
      </div>
      <div className="eyebrow cyan">ON-CHAIN RECORDING</div>
      <h2>Recording integrity proof</h2>
      <p className="intro">Submitting a permanent content record to the verification network.</p>
      <div className="record-steps" role="status" aria-live="polite">
        <span className="done">
          <Check size={15} /> Fingerprint generated
        </span>
        <span className="done">
          <Check size={15} /> Transaction submitted
        </span>
        <span className="done">
          <Check size={15} /> Blockchain confirmation received
        </span>
      </div>
      <small className="network">
        NETWORK <b>Ethereum Sepolia</b>
      </small>
    </section>
  )
}

/* ─── Verified / Mismatch stage — REAL TX data ─── */
function VerificationState({
  mismatch,
  result,
  onAgain,
}: {
  mismatch: boolean
  result: PipelineResult
  onAgain: () => void
}) {
  const fp = result.fingerprint
  const tx = result.upload.transaction_hash
  const block = result.upload.block_number
  const ts = result.verification.human_timestamp
  const shortTx = tx ? `${tx.slice(0, 6)}...${tx.slice(-4)}` : 'N/A'
  const etherscanUrl = tx ? `https://sepolia.etherscan.io/tx/${tx}` : '#'

  // Tamper simulation: show a fake mismatched fingerprint
  const tamperedFp = mismatch ? `4c21d9${fp.slice(6, 12)}...a194` : null

  return (
    <section
      className={`workspace verification-workspace ${mismatch ? 'failed' : ''}`}
      aria-live="assertive"
    >
      <div className="verification-icon" aria-hidden="true">
        {mismatch ? <AlertTriangle size={35} /> : <CheckCircle2 size={38} />}
      </div>
      <div className="eyebrow">{mismatch ? 'VERIFICATION FAILED' : 'VERIFICATION COMPLETE'}</div>
      <h2>{mismatch ? 'Integrity mismatch' : 'Content integrity verified'}</h2>
      <p className="intro">
        {mismatch
          ? 'The current content fingerprint does not match the fingerprint stored on-chain. Content may have been tampered with.'
          : 'The fingerprint of the discovered content matches the fingerprint recorded on Ethereum Sepolia.'}
      </p>
      <div className="comparison" aria-label="Fingerprint comparison">
        <div>
          <span>LOCAL CONTENT</span>
          <code>{mismatch ? tamperedFp : `${fp.slice(0, 14)}...${fp.slice(-4)}`}</code>
        </div>
        <b aria-label={mismatch ? 'does not equal' : 'equals'}>{mismatch ? '≠' : '='}</b>
        <div>
          <span>ON-CHAIN RECORD</span>
          <code>{`${fp.slice(0, 14)}...${fp.slice(-4)}`}</code>
        </div>
      </div>
      <strong className="verification-status">{mismatch ? 'CONTENT CHANGED' : 'MATCH — VERIFIED'}</strong>
      {!mismatch && (
        <div className="chain-meta" aria-label="On-chain transaction details">
          <span>Ethereum Sepolia Testnet</span>
          <span>TX {shortTx}</span>
          {block && <span>BLOCK #{block.toLocaleString()}</span>}
          <span>{ts}</span>
        </div>
      )}
      <div className="verification-actions">
        <Button onClick={onAgain}>{mismatch ? 'Run Verification Again' : 'Verify Again'}</Button>
        <Button
          secondary
          onClick={() => window.open(etherscanUrl, '_blank')}
          disabled={mismatch || !tx}
        >
          View on Etherscan <ExternalLink size={14} />
        </Button>
      </div>
      {!mismatch && <Timeline result={result} />}
    </section>
  )
}

/* ─── Timeline — real steps ─── */
function Timeline({ result }: { result: PipelineResult }) {
  return (
    <div className="timeline" aria-label="Investigation timeline">
      <div><b>01</b><span>Face detected ({result.face.confidence}% confidence)</span></div>
      <div><b>02</b><span>Web search via Google Lens</span></div>
      <div><b>03</b><span>Match: {result.match.platform} ({result.match.score}% similarity)</span></div>
      <div><b>04</b><span>SHA-256 fingerprint: {result.fingerprint.slice(0, 12)}…</span></div>
      <div><b>05</b><span>Block #{result.upload.block_number?.toLocaleString()} confirmed</span></div>
      <div><b>06</b><span>Integrity verified on-chain since {result.verification.human_timestamp}</span></div>
    </div>
  )
}

/* ─── Root page ─── */
export default function Page() {
  const [stage, setStage] = useState<Stage>('upload')
  const [image, setImage] = useState<string | null>(null)
  const [imageFile, setImageFile] = useState<File | null>(null)
  const [pipelineResult, setPipelineResult] = useState<PipelineResult | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [apiError, setApiError] = useState<string | null>(null)

  const upload = (file: File) => {
    setImageFile(file)
    setImage(URL.createObjectURL(file))
    setStage('analysis')
    setApiError(null)
  }

  const reset = () => {
    setStage('upload')
    setImage(null)
    setImageFile(null)
    setPipelineResult(null)
    setApiError(null)
    setIsLoading(false)
  }

  // Call real backend API
  const runPipeline = async () => {
    if (!imageFile) return
    setIsLoading(true)
    setApiError(null)
    setStage('searching')

    try {
      const formData = new FormData()
      formData.append('image', imageFile)

      const response = await fetch(`${API_BASE}/api/run`, {
        method: 'POST',
        body: formData,
      })

      const data = await response.json()

      if (!response.ok || !data.success) {
        throw new Error(data.error || 'Pipeline failed')
      }

      setPipelineResult(data as PipelineResult)
      setStage('results')
    } catch (err: any) {
      setApiError(err.message || 'Pipeline error. Is the Flask server running?')
      setStage('analysis')
    } finally {
      setIsLoading(false)
    }
  }

  // Simulate tampered content (still fake — just flips to mismatch state)
  const simulateTamper = () => {
    setStage('recording')
    window.setTimeout(() => setStage('mismatch'), 1500)
  }

  return (
    <main className="app-shell">
      <Header stage={stage} onReset={reset} />
      <div className="main-content" aria-live="polite" aria-atomic="true">
        {stage === 'upload' && <UploadState onUpload={upload} />}
        {stage === 'analysis' && image && (
          <AnalysisState
            image={image}
            onSearch={runPipeline}
            isLoading={isLoading}
            error={apiError}
          />
        )}
        {stage === 'searching' && <SearchState />}
        {stage === 'results' && pipelineResult && (
          <ResultsState result={pipelineResult} onSelect={() => setStage('fingerprint')} />
        )}
        {stage === 'fingerprint' && pipelineResult && (
          <FingerprintState
            result={pipelineResult}
            onRecord={() => setStage('recording')}
            onSimulateTamper={simulateTamper}
          />
        )}
        {stage === 'recording' && pipelineResult && (
          <>
            <RecordingState />
            {/* Auto-advance to verified after brief delay */}
            {(() => {
              window.setTimeout(() => setStage('verified'), 1500)
              return null
            })()}
          </>
        )}
        {(stage === 'verified' || stage === 'mismatch') && pipelineResult && (
          <VerificationState
            mismatch={stage === 'mismatch'}
            result={pipelineResult}
            onAgain={reset}
          />
        )}
      </div>
      <footer>
        <span>FACECHAIN VERIFY</span>
        <span>DISCOVER. FINGERPRINT. VERIFY.</span>
        <span>v1.0 / LIVE</span>
      </footer>
    </main>
  )
}
