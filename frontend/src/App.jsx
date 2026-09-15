import { useState } from 'react'
import './App.css'

function App() {
  const [jobs, setJobs] = useState([])
    const [matches, setMatches] = useState([])
  const [showProfile, setShowProfile] = useState(false)
  const [skills, setSkills] = useState('')
    const [jobTitle, setJobTitle] = useState('')
    const [company, setCompany] = useState('')
    const [startDate, setStartDate] = useState('')
    const [qualification, setQualification] = useState('')
    const [institution, setInstitution] = useState('')

  const loadJobs = async () => {
    const response = await fetch('http://127.0.0.1:8000/api/v1/jobs/')
    const data = await response.json()
    setJobs(data)
  }

    const loadMatches = async () => {
        const response = await fetch('http://127.0.0.1:8000/api/v1/matches', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                candidate_id: 'test-candidate',
                limit: 5,
            }),
        })

        const data = await response.json()
        setMatches(data.matches || [])
        console.log(data)
    }

  const saveProfile = async () => {
    const response = await fetch(
        'http://127.0.0.1:8000/api/v1/candidates/test-candidate/profile',
        {
          method: 'PUT',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            skills: skills
                .split(',')
                .map((skill) => skill.trim())
                .filter((skill) => skill),

              experience: [
                  {
                      title: jobTitle,
                      company: company,
                      start_date: startDate,
                  },
              ],
              education: [
                  {
                      qualification: qualification,
                      institution: institution,
                  },
              ],

          }),
        }
    )

    const data = await response.json()
    console.log(data)
  }
  return (
      <div className="app">
        <header className="hero">
          <p className="eyebrow">AI-Powered Job Matching System</p>
          <h1>Find jobs that match your skills</h1>
          <p className="hero-text">
            Create your candidate profile, review available jobs, and view ranked
            matches based on your skills.
          </p>
        </header>

        <main className="dashboard">
          <section className="card">
            <h2>Candidate Profile</h2>
            <p>Add your skills, education, and experience.</p>
            <button type="button" onClick={() => setShowProfile(!showProfile)}>
              Manage Profile
            </button>
            {showProfile && (
                <div>
                  <label>
                    Skills:
                    <input
                        type="text"
                        value={skills}
                        onChange={(e) => setSkills(e.target.value)}
                        placeholder="Python, React, SQL"
                    />
                  </label>

                    <label>
                        Job Title:
                        <input
                            type="text"
                            value={jobTitle}
                            onChange={(e) => setJobTitle(e.target.value)}
                            placeholder="Software Developer"
                        />
                    </label>

                    <label>
                        Company:
                        <input
                            type="text"
                            value={company}
                            onChange={(e) => setCompany(e.target.value)}
                            placeholder="Company Name"
                        />
                    </label>

                    <label>
                        Start Date:
                        <input
                            type="date"
                            value={startDate}
                            onChange={(e) => setStartDate(e.target.value)}
                        />
                    </label>

                    <label>
                        Qualification:
                        <input
                            type="text"
                            value={qualification}
                            onChange={(e) => setQualification(e.target.value)}
                            placeholder="Bachelor's Degree"
                        />
                    </label>

                    <label>
                        Institution:
                        <input
                            type="text"
                            value={institution}
                            onChange={(e) => setInstitution(e.target.value)}
                            placeholder="University Name"
                        />
                    </label>

                  <button type="button" onClick={saveProfile}>
                    Save Profile
                  </button>
                </div>
            )}
          </section>

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

          <section className="card">
            <h2>Job Matches</h2>
            <p>See ranked jobs based on your candidate profile.</p>
              <button type="button" onClick={loadMatches}>Find Matches</button>
              {matches.map((match) => (
                  <div key={match.job_id}>
                      <h3>#{match.rank} - {match.job_id}</h3>
                      <p>Score: {match.score}%</p>
                      <p>{match.reasons.join(', ')}</p>
                  </div>
              ))}
          </section>
        </main>
      </div>
  )
}

export default App