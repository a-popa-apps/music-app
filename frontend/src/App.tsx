import { useState } from 'react'

const BACKEND_URL = import.meta.env.VITE_BACKEND_URL ?? 'http://localhost:8000'

function App() {
  const [status, setStatus] = useState<string>('Not tested yet')

  async function pingBackend() {
    setStatus('Checking...')
    try {
      const res = await fetch(`${BACKEND_URL}/health`)
      const data = await res.json()
      setStatus(`Backend says: ${data.status}`)
    } catch (err) {
      setStatus(`Failed to reach backend: ${(err as Error).message}`)
    }
  }

  return (
    <div className="mx-auto flex min-h-screen max-w-xl flex-col items-center justify-center gap-4 text-center">
      <h1 className="text-3xl font-semibold">Quickie</h1>
      <p className="text-gray-500">Track organizer for DJs — setup check</p>
      <button
        type="button"
        onClick={pingBackend}
        className="rounded-md bg-purple-600 px-4 py-2 text-white hover:bg-purple-700"
      >
        Test backend connection
      </button>
      <p className="text-sm text-gray-600">{status}</p>
    </div>
  )
}

export default App
