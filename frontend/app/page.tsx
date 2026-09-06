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

type Stage =
  | 'upload'
  | 'analysis'
  | 'searching'
  | 'results'
  | 'fingerprint'
  | 'recording'
  | 'verified'
  | 'mismatch'

const candidates = [
  {
    source: 'Instagram',
    type: 'Public post',
    title: 'A quiet portrait from the coast',
    score: '94.2%',
    image:
      'https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&w=180&q=80',
  },
  {
    source: 'Personal blog',
    type: 'Article image',
    title: 'Field notes: faces in public spaces',
    score: '88.7%',
    image:
      'https://images.unsplash.com/photo-1506794778202-cad84cf45f1d?auto=format&fit=crop&w=180&q=80',
  },
  {
    source: 'Reddit',
    type: 'Community post',
    title: 'The light was perfect today',
    score: '81.4%',
    image:
      'https://images.unsplash.com/photo-1544005313-94ddf0286df2?auto=format&fit=crop&w=180&q=80',
  },
]

const fingerprint = '9f8a7c2e4d8b91ac7f2e0a16c81d'

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
function AnalysisState({ image, onSearch }: { image: string; onSearch: () => void }) {
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
            <strong>92.8%</strong>
          </div>
          <div>
            <span>Embedding</span>
            <strong>Generated</strong>
          </div>
        </div>
        <Button onClick={onSearch}>Search the Web</Button>
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
      <h2>Searching for matching content</h2>
      <p className="intro">Discovering visually similar content across public sources...</p>
      <div className="progress-list" role="status" aria-live="polite">
        <div className="done">
          <Check size={15} /> Face detected
        </div>
        <div className="active">
          {/* FIX: spin class applied to Loader2 so it actually rotates */}
          <span className="spin" aria-hidden="true">
            <Loader2 size={15} />
          </span>{' '}
          Searching public web sources
        </div>
        <div>
          <Circle size={11} /> Comparing candidate faces
        </div>
        <div>
          <Circle size={11} /> Selecting strongest match
        </div>
      </div>
    </section>
  )
}

/* ─── Results stage ─── */
function ResultsState({ onSelect }: { onSelect: () => void }) {
  return (
    <section className="workspace results-workspace">
      <div className="eyebrow cyan">
        <Globe2 size={15} /> SEARCH COMPLETE
      </div>
      <h2>Matching content discovered</h2>
      <p className="intro">
        7 candidate sources were discovered and evaluated. The strongest visual match is ready for
        evidence review.
      </p>
      <div className="result-list" role="list">
        {candidates.map((candidate, i) => (
          <button
            // FIX: only the best match (i === 0) is clickable; others are disabled
            className={`result-row ${i === 0 ? 'best' : ''}`}
            key={candidate.source}
            onClick={i === 0 ? onSelect : undefined}
            disabled={i !== 0}
            aria-label={
              i === 0
                ? `Select best match: ${candidate.source} — ${candidate.score} visual match`
                : `${candidate.source} — ${candidate.score} visual match (not the best match)`
            }
            role="listitem"
          >
            <img src={candidate.image} alt="" aria-hidden="true" />
            <span className="result-detail">
              <b>{candidate.source}</b>
              <small>
                {candidate.type} · {candidate.title}
              </small>
            </span>
            <span className="match-score">
              {i === 0 && <label aria-hidden="true">BEST MATCH</label>}
              <strong>{candidate.score}</strong>
              <small>VISUAL MATCH</small>
            </span>
            {i === 0 && <ArrowRight size={16} aria-hidden="true" />}
          </button>
        ))}
      </div>
    </section>
  )
}

/* ─── Evidence stage ─── */
function EvidenceState({ onFingerprint }: { onFingerprint: () => void }) {
  return (
    <section className="workspace evidence-workspace">
      <div className="evidence-image">
        <img src={candidates[0].image} alt="Best visual match from Instagram" />
        <span>BEST MATCH</span>
      </div>
      <div className="evidence-copy">
        <div className="eyebrow cyan">EVIDENCE REVIEW</div>
        <h2>Best visual match</h2>
        <div className="big-score">
          94.2%<small>SIMILARITY</small>
        </div>
        <div className="metadata">
          <div>
            <span>Source</span>
            <strong>Instagram</strong>
          </div>
          <div>
            <span>Content</span>
            <strong>Public post</strong>
          </div>
          <div>
            <span>Discovered</span>
            <strong>06 Sep 2026</strong>
          </div>
        </div>
        {/* FIX: href points to a real demo anchor instead of "#source" with preventDefault */}
        <a
          href="https://unsplash.com/photos/a-quiet-portrait-from-the-coast"
          target="_blank"
          rel="noopener noreferrer"
        >
          Open source <ExternalLink size={14} />
        </a>
        <Button onClick={onFingerprint}>Create Integrity Record</Button>
      </div>
    </section>
  )
}

/* ─── Fingerprint stage ─── */
function FingerprintState({
  onRecord,
  onSimulateTamper,
}: {
  onRecord: () => void
  onSimulateTamper: () => void
}) {
  return (
    <section className="workspace fingerprint-workspace">
      <div className="eyebrow cyan">
        <Fingerprint size={15} /> CRYPTOGRAPHIC PROCESSING
      </div>
      <h2>Creating content fingerprint</h2>
      <p className="intro">
        A cryptographic fingerprint is generated from the discovered content before it is recorded
        on-chain.
      </p>
      <div className="hash-box" aria-label="SHA-256 content fingerprint">
        <span>SHA-256 CONTENT FINGERPRINT</span>
        <code>
          {fingerprint.slice(0, 22)}...{fingerprint.slice(-5)}
        </code>
        <div className="hash-line" aria-hidden="true">
          <i /><i /><i /><i /><i /><i /><i />
        </div>
      </div>
      {/* FIX: added "Simulate Tampered Content" button to make mismatch stage reachable */}
      <div className="fingerprint-actions">
        <Button onClick={onRecord}>Record on Blockchain</Button>
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
        <span className="active">
          {/* FIX: spin class applied to Loader2 so it actually rotates */}
          <span className="spin" aria-hidden="true">
            <Loader2 size={15} />
          </span>{' '}
          Transaction submitted
        </span>
        <span>
          <Circle size={11} /> Blockchain confirmation
        </span>
      </div>
      <small className="network">
        NETWORK <b>Ethereum Sepolia</b>
      </small>
    </section>
  )
}

/* ─── Verified / Mismatch stage ─── */
function VerificationState({
  mismatch,
  onAgain,
}: {
  mismatch: boolean
  onAgain: () => void
}) {
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
          ? 'The current content fingerprint does not match the fingerprint stored on-chain.'
          : 'The fingerprint of the discovered content matches the fingerprint recorded on-chain.'}
      </p>
      <div className="comparison" aria-label="Fingerprint comparison">
        <div>
          <span>LOCAL CONTENT</span>
          <code>{mismatch ? '4c21d9...a194' : '9f8a7c2e4d8b...c81d'}</code>
        </div>
        <b aria-label={mismatch ? 'does not equal' : 'equals'}>{mismatch ? '≠' : '='}</b>
        <div>
          <span>ON-CHAIN RECORD</span>
          <code>9f8a7c2e4d8b...c81d</code>
        </div>
      </div>
      <strong className="verification-status">{mismatch ? 'CONTENT CHANGED' : 'MATCH — VERIFIED'}</strong>
      {!mismatch && (
        <div className="chain-meta" aria-label="On-chain transaction details">
          <span>Ethereum Sepolia Testnet</span>
          <span>TX 0x82ab...7f21</span>
          <span>BLOCK #8,421,907</span>
          <span>06 Sep 2026, 19:42</span>
        </div>
      )}
      <div className="verification-actions">
        <Button onClick={onAgain}>{mismatch ? 'Run Verification Again' : 'Verify Again'}</Button>
        {/* FIX: "View Transaction" shown for both verified and mismatch; disabled for mismatch */}
        <Button
          secondary
          onClick={() => window.open('https://sepolia.etherscan.io/tx/0x82ab', '_blank')}
          disabled={mismatch}
        >
          View Transaction <ExternalLink size={14} />
        </Button>
      </div>
      {!mismatch && <Timeline />}
    </section>
  )
}

/* ─── Timeline ─── */
function Timeline() {
  return (
    <div className="timeline" aria-label="Investigation timeline">
      <div><b>01</b><span>Face detected</span></div>
      <div><b>02</b><span>Web search completed</span></div>
      <div><b>03</b><span>Matching content discovered</span></div>
      <div><b>04</b><span>SHA-256 fingerprint generated</span></div>
      <div><b>05</b><span>Blockchain record confirmed</span></div>
      <div><b>06</b><span>Integrity verified</span></div>
    </div>
  )
}

/* ─── Root page ─── */
export default function Page() {
  const [stage, setStage] = useState<Stage>('upload')
  const [image, setImage] = useState<string | null>(null)

  const upload = (file: File) => {
    setImage(URL.createObjectURL(file))
    setStage('analysis')
  }

  const reset = () => {
    setStage('upload')
    setImage(null)
  }

  // Automatically advance searching → results after 2.2s
  const advanceSearch = () => {
    setStage('searching')
    window.setTimeout(() => setStage('results'), 2200)
  }

  // Automatically advance recording → verified after 2.3s
  const advanceRecord = () => {
    setStage('recording')
    window.setTimeout(() => setStage('verified'), 2300)
  }

  // Simulate tampered content → mismatch state (was previously unreachable)
  const simulateTamper = () => {
    setStage('recording')
    window.setTimeout(() => setStage('mismatch'), 2300)
  }

  return (
    <main className="app-shell">
      <Header stage={stage} onReset={reset} />
      {/* FIX: aria-live so screen readers announce stage changes */}
      <div className="main-content" aria-live="polite" aria-atomic="true">
        {stage === 'upload' && <UploadState onUpload={upload} />}
        {stage === 'analysis' && image && (
          <AnalysisState image={image} onSearch={advanceSearch} />
        )}
        {stage === 'searching' && <SearchState />}
        {stage === 'results' && (
          <ResultsState onSelect={() => setStage('fingerprint')} />
        )}
        {stage === 'fingerprint' && (
          <FingerprintState onRecord={advanceRecord} onSimulateTamper={simulateTamper} />
        )}
        {stage === 'recording' && <RecordingState />}
        {(stage === 'verified' || stage === 'mismatch') && (
          <VerificationState mismatch={stage === 'mismatch'} onAgain={reset} />
        )}
      </div>
      <footer>
        <span>FACECHAIN VERIFY</span>
        <span>DISCOVER. FINGERPRINT. VERIFY.</span>
        <span>v1.0 / DEMO MODE</span>
      </footer>
    </main>
  )
}
