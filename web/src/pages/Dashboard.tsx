import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../api'
import Brand, { ModePill } from '../components/Brand'
import CourseCard from '../components/dashboard/CourseCard'
import { Chick } from '../components/Mascots'

export default function Dashboard() {
  const [data, setData] = useState<Awaited<ReturnType<typeof api.courses>> | null>(null)
  const [error, setError] = useState<string | null>(null)
  const nav = useNavigate()

  useEffect(() => { api.courses().then(setData).catch(e => setError(e.message)) }, [])

  const reviews = data?.courses.flatMap(c => (c.reviews ?? []).map(r => ({ ...r, course: c }))) ?? []

  return (
    <div className="page">
      <header className="topbar">
        <Brand />
        {data && <ModePill mode={data.mode} />}
      </header>

      <main className="dash">
        <section className="dash-hero">
          <div>
            <h1>Don't reread it.<br />Explain it.</h1>
            <p className="lede">Pick a course and teach the topic you fear to the Sub-student: it only knows what you tell it.
              The Teacher knows the slides and corrects you.</p>
          </div>
          <Chick size={112} />
        </section>

        {error && <p className="alert" role="alert">The server is not responding ({error}). Start it with <code>python -m server</code>.</p>}

        {reviews.length > 0 && (
          <section className="reviews" aria-label="Today's reviews">
            <h2>To review today</h2>
            <ul>
              {reviews.map(r => (
                <li key={r.course.id + r.concept_id}>
                  <button className="review-chip" onClick={() => nav(`/course/${r.course.id}`)}>
                    <span className={`dot s-${r.status}`} />{r.name}
                    <small>{r.course.title.split(' - ')[0]}</small>
                  </button>
                </li>
              ))}
            </ul>
          </section>
        )}

        <section aria-label="Your courses">
          <h2 className="section-title">Your courses</h2>
          <div className="courses">
            {!data && !error && [0, 1, 2].map(i => <div key={i} className="course skeleton" />)}
            {data?.courses.map(c => <CourseCard key={c.id} c={c} onOpen={() => nav(`/course/${c.id}`)} />)}
            {data && (
              <div className="course course-new">
                <span className="plus" aria-hidden="true">+</span>
                <h3>Create a course</h3>
                <p>Upload your own material: the concepts the AI proposes stay "not validated" until a lecturer checks them.</p>
                <span className="soon">Not yet active in the prototype</span>
              </div>
            )}
          </div>
        </section>
      </main>
    </div>
  )
}
