
import { useEffect, useState } from 'react'
import './App.css'

const API_URL = '/api/disagreements/'

function App() {
  const [orgId, setOrgId] = useState('ORG-A')
  const [reason, setReason] = useState('')
  const [sort, setSort] = useState('asc')
  const [records, setRecords] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    const fetchDisagreements = async () => {
      setLoading(true)
      setError('')

      try {
        const params = new URLSearchParams({
          org_id: orgId,
          sort: sort,
        })

        if (reason) {
          params.append('reason', reason)
        }

        const response = await fetch(`${API_URL}?${params.toString()}`)

        if (!response.ok) {
          throw new Error(`API error: ${response.status}`)
        }

        const data = await response.json()

        if (!Array.isArray(data)) {
          throw new Error('Unexpected API response.')
        }

        setRecords(data)
      } catch (err) {
        console.error('Failed to fetch disagreements:', err)
        setRecords([])
        setError(
          'Unable to load records. Check whether the Django backend is running.'
        )
      } finally {
        setLoading(false)
      }
    }

    fetchDisagreements()
  }, [orgId, reason, sort])

  return (
    <main className="dashboard">
      <header className="header">
        <div>
          <h1>DealerOS</h1>
          <p>Data Reconciliation Dashboard</p>
        </div>

        <span className="status">System Online</span>
      </header>

      <section className="summary">
        <div className="summary-card">
          <h3>Total Disagreements</h3>
          <p>{records.length}</p>
        </div>

        <div className="summary-card">
          <h3>Organization</h3>
          <p>{orgId}</p>
        </div>
      </section>

      <section className="filters">
        <div>
          <label htmlFor="org">Organization</label>

          <select
            id="org"
            value={orgId}
            onChange={(e) => setOrgId(e.target.value)}
          >
            <option value="ORG-A">ORG-A</option>
            <option value="ORG-B">ORG-B</option>
          </select>
        </div>

        <div>
          <label htmlFor="reason">Disagreement Reason</label>

          <select
            id="reason"
            value={reason}
            onChange={(e) => setReason(e.target.value)}
          >
            <option value="">All Reasons</option>
            <option value="MISSING_IN_SYSTEM_B">Missing in System B</option>
            <option value="ORPHAN_IN_SYSTEM_B">Orphan in System B</option>
            <option value="DUPLICATE_IN_SYSTEM_B">
              Duplicate in System B
            </option>
            <option value="VALUE_MISMATCH">Value Mismatch</option>
            <option value="DATE_MISMATCH">Date Mismatch</option>
            <option value="LOCATION_MISMATCH">Location Mismatch</option>
            <option value="VOIDED_RECORD_PRESENT_IN_SYSTEM_B">
              Voided Record
            </option>
          </select>
        </div>

        <div>
          <label htmlFor="sort">Sort by Value</label>

          <select
            id="sort"
            value={sort}
            onChange={(e) => setSort(e.target.value)}
          >
            <option value="asc">Low to High</option>
            <option value="desc">High to Low</option>
          </select>
        </div>
      </section>

      {loading && (
        <p className="message">Loading records...</p>
      )}

      {error && (
        <p className="error">{error}</p>
      )}

      {!loading && !error && (
        <section className="table-section">
          <h2>Disagreement Records</h2>

          <div className="table-wrapper">
            <table>
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Reason</th>
                  <th>Reference</th>
                  <th>Organization</th>
                  <th>Location</th>
                  <th>System A Values</th>
                  <th>System B Values</th>
                  <th>Description</th>
                </tr>
              </thead>

              <tbody>
                {records.map((record) => (
                  <tr key={record.id}>
                    <td>{record.id}</td>

                    <td>
                      <span className="reason">
                        {record.reason}
                      </span>
                    </td>

                    <td>{record.normalized_ref || '-'}</td>

                    <td>{record.tenant_org_id}</td>

                    <td>{record.location || '-'}</td>

                    <td>
                      <pre>
                        {JSON.stringify(
                          record.system_a_values,
                          null,
                          2
                        )}
                      </pre>
                    </td>

                    <td>
                      <pre>
                        {JSON.stringify(
                          record.system_b_values,
                          null,
                          2
                        )}
                      </pre>
                    </td>

                    <td>{record.description || '-'}</td>
                  </tr>
                ))}

                {records.length === 0 && (
                  <tr>
                    <td colSpan="8">
                      No disagreement records found.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </section>
      )}
    </main>
  )
}

export default App
