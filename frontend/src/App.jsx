import { useState, useEffect } from 'react'
import './App.css'

// Stages shown while the AI runs, so the user can see the matching happening
// rather than results just appearing. The matcher itself is fast; this reveal
// is a short, honest look at the pipeline, not a fake delay.
const PIPELINE = [
  'Reading your skills',
  'Checking known synonyms',
  'Running the AI matcher',
  'Ranking the jobs',
]

// A score bar that animates from 0 up to its value when it mounts.
function ScoreBar({ score }) {
  const [w, setW] = useState(0)
  useEffect(() => {
    const id = requestAnimationFrame(() => setW(score))
    return () => cancelAnimationFrame(id)
  }, [score])
  return (
    <div className="score-row">
      <div className="score-track">
        <div className="score-fill" style={{ width: `${w}%` }} />
      </div>
      <span className="score-num">{score}%</span>
    </div>
  )
}

function App() {

  const API_URL = 'http://127.0.0.1:8000'

  const [jobs, setJobs] = useState([])
  const [matches, setMatches] = useState([])
  const [showProfile, setShowProfile] = useState(false)

  const [skills, setSkills] = useState('')
  const [jobTitle, setJobTitle] = useState('')
  const [company, setCompany] = useState('')
  const [startDate, setStartDate] = useState('')
  const [qualification, setQualification] = useState('')
  const [institution, setInstitution] = useState('')

  const [message, setMessage] = useState('')

  // Dynamic AI state
  const [analyzing, setAnalyzing] = useState(false)
  const [pipelineStep, setPipelineStep] = useState(0)
  const [engineLabel, setEngineLabel] = useState('')

  const loadJobs = async () => {
    setMessage('')
    try {
      const response = await fetch(`${API_URL}/api/v1/jobs/`)
      if (!response.ok) throw new Error('Could not load jobs')
      setJobs(await response.json())
    } catch (error) {
      console.log(error)
      setMessage('There was a problem loading the jobs.')
    }
  }

  // Get job matches, showing the AI pipeline while it runs.
  const loadMatches = async () => {
    setMessage('')
    setMatches([])
    setEngineLabel('')
    setAnalyzing(true)
    setPipelineStep(0)

    // Step the pipeline forward so the user watches the stages light up.
    let step = 0
    const stepMs = 360
    const timer = setInterval(() => {
      step += 1
      setPipelineStep(step)
      if (step >= PIPELINE.length) clearInterval(timer)
    }, stepMs)
    const started = Date.now()

    try {
      const response = await fetch(`${API_URL}/api/v1/matches`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ candidate_id: 'test-candidate', limit: 5 }),
      })
      if (!response.ok) throw new Error('Could not load job matches')
      const data = await response.json()

      // Let the pipeline animation play through before revealing results.
      const minMs = PIPELINE.length * stepMs + 300
      const elapsed = Date.now() - started
      if (elapsed < minMs) {
        await new Promise((r) => setTimeout(r, minMs - elapsed))
      }

      setEngineLabel(data.engine_label || '')
      setMatches(data.matches || [])
    } catch (error) {
      console.log(error)
      setMessage('There was a problem finding job matches.')
    } finally {
      clearInterval(timer)
      setAnalyzing(false)
    }
  }

  const saveProfile = async () => {
    setMessage('')
    try {
      const response = await fetch(
        `${API_URL}/api/v1/candidates/test-candidate/profile`,
        {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            skills: skills.split(',').map((s) => s.trim()).filter((s) => s),
            experience: [{ title: jobTitle, company: company, start_date: startDate }],
            education: [{ qualification: qualification, institution: institution }],
          }),
        }
      )
      if (!response.ok) throw new Error('Could not save profile')
      await response.json()
      setMessage('Profile saved successfully.')
    } catch (error) {
      console.log(error)
      setMessage('There was a problem saving the profile.')
    }
  }

  return (
    <div className="app">
      <style>{DYNAMIC_STYLES}</style>

      <header className="hero">
        <p className="eyebrow">AI-Powered Job Matching System</p>
        <h1>Find jobs that match your skills</h1>
        <p className="hero-text">
          Create your candidate profile, review available jobs,
          and view ranked matches based on your skills.
        </p>
      </header>

      {message && <div className="status-message">{message}</div>}

      <main className="dashboard">

        {/* Candidate Profile */}
        <section className="card">
          <h2>Candidate Profile</h2>
          <p>Add your skills, education, and experience.</p>
          <button type="button" onClick={() => setShowProfile(!showProfile)}>
            Manage Profile
          </button>

          {showProfile && (
            <div>
              <label>Skills:
                <input type="text" value={skills}
                  onChange={(e) => setSkills(e.target.value)}
                  placeholder="Python, React, SQL" />
              </label>
              <label>Job Title:
                <input type="text" value={jobTitle}
                  onChange={(e) => setJobTitle(e.target.value)}
                  placeholder="Software Developer" />
              </label>
              <label>Company:
                <input type="text" value={company}
                  onChange={(e) => setCompany(e.target.value)}
                  placeholder="Company Name" />
              </label>
              <label>Start Date:
                <input type="date" value={startDate}
                  onChange={(e) => setStartDate(e.target.value)} />
              </label>
              <label>Qualification:
                <input type="text" value={qualification}
                  onChange={(e) => setQualification(e.target.value)}
                  placeholder="Bachelor's Degree" />
              </label>
              <label>Institution:
                <input type="text" value={institution}
                  onChange={(e) => setInstitution(e.target.value)}
                  placeholder="University Name" />
              </label>
              <button type="button" onClick={saveProfile}>Save Profile</button>
            </div>
          )}
        </section>

        {/* Job Listings */}
        <section className="card">
          <h2>Job Listings</h2>
          <p>View jobs currently available in the system.</p>
          <button type="button" onClick={loadJobs}>View Jobs</button>
          {jobs.map((job) => (
            <div key={job.job_id}>
              <h3>{job.title}</h3>
              <p>{job.company}</p>
            </div>
          ))}
        </section>

        {/* Job Matches */}
        <section className="card">
          <h2>Job Matches</h2>
          <p>See ranked jobs based on your candidate profile.</p>
          <button type="button" onClick={loadMatches} disabled={analyzing}>
            {analyzing ? 'Analyzing…' : 'Find Matches'}
          </button>

          {/* Dynamic AI pipeline, shown while matching runs */}
          {analyzing && (
            <div className="ai-panel">
              <div className="ai-panel-title">
                <span className="ai-spinner" /> AI is analyzing your skills
              </div>
              {PIPELINE.map((label, i) => {
                const state = pipelineStep > i ? 'done'
                  : pipelineStep === i ? 'active' : 'pending'
                return (
                  <div key={label} className={`pipe-step ${state}`}>
                    <span className="pipe-dot">{state === 'done' ? '✓' : ''}</span>
                    {label}
                  </div>
                )
              })}
            </div>
          )}

          {/* Engine badge: which AI actually produced these matches */}
          {!analyzing && engineLabel && matches.length > 0 && (
            <div className="engine-badge">
              <span className="engine-dot" /> Powered by: {engineLabel}
            </div>
          )}

          {!analyzing && matches.map((match) => (
            <div key={match.job_id} className="match-card">
              <h3>#{match.rank} - {match.job_id}</h3>
              <ScoreBar score={match.score} />
              <ul className="reasons">
                {(match.reasons || []).map((r, i) => (
                  <li key={i}>{r}</li>
                ))}
              </ul>
            </div>
          ))}
        </section>

      </main>
    </div>
  )
}

const DYNAMIC_STYLES = `
.ai-panel {
  margin-top: 16px; padding: 14px 16px; border-radius: 10px;
  background: #eef3fb; border: 1px solid #d6e2f5;
}
.ai-panel-title {
  display: flex; align-items: center; gap: 8px;
  font-weight: bold; color: #1f3a5f; margin-bottom: 10px;
}
.ai-spinner {
  width: 14px; height: 14px; border-radius: 50%;
  border: 3px solid #c3d4ee; border-top-color: #1f3a5f;
  display: inline-block; animation: ai-spin 0.8s linear infinite;
}
@keyframes ai-spin { to { transform: rotate(360deg); } }
.pipe-step {
  display: flex; align-items: center; gap: 8px;
  padding: 5px 0; color: #94a3b8; font-size: 14px;
  transition: color 0.3s ease;
}
.pipe-step.active { color: #1f3a5f; font-weight: bold; }
.pipe-step.done { color: #15803d; }
.pipe-dot {
  width: 18px; height: 18px; border-radius: 50%;
  border: 2px solid currentColor; display: inline-flex;
  align-items: center; justify-content: center; font-size: 11px; flex: 0 0 auto;
}
.pipe-step.active .pipe-dot { animation: ai-pulse 0.8s ease-in-out infinite; }
@keyframes ai-pulse { 0%,100% { opacity: 1; } 50% { opacity: 0.35; } }
.engine-badge {
  display: inline-flex; align-items: center; gap: 8px;
  margin: 14px 0 6px; padding: 6px 12px; border-radius: 999px;
  background: #e8f5ec; color: #15803d; font-size: 13px; font-weight: bold;
}
.engine-dot {
  width: 9px; height: 9px; border-radius: 50%; background: #22c55e;
  animation: ai-pulse 1.4s ease-in-out infinite;
}
.match-card { margin-top: 14px; }
.score-row { display: flex; align-items: center; gap: 10px; margin: 4px 0 8px; }
.score-track {
  flex: 1; height: 12px; border-radius: 999px; background: #e5e9f0; overflow: hidden;
}
.score-fill {
  height: 100%; border-radius: 999px;
  background: linear-gradient(90deg, #2563eb, #22c55e);
  width: 0; transition: width 0.9s cubic-bezier(.2,.8,.2,1);
}
.score-num { font-weight: bold; color: #1f3a5f; min-width: 44px; text-align: right; }
.reasons { margin: 6px 0 0; padding-left: 18px; color: #334155; font-size: 14px; }
.reasons li { margin: 3px 0; }
`

export default App
