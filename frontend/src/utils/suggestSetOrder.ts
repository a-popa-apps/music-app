export interface MixableTrack {
  name: string
  bpm: number | null
  key: string | null // Camelot notation, e.g. "8A"
  energy: number | null
}

const CAMELOT = /^(\d{1,2})([AB])$/i

function camelotDistance(a: string, b: string): number {
  const ma = CAMELOT.exec(a)
  const mb = CAMELOT.exec(b)
  if (!ma || !mb) return Infinity

  const [numA, letterA] = [parseInt(ma[1], 10), ma[2].toUpperCase()]
  const [numB, letterB] = [parseInt(mb[1], 10), mb[2].toUpperCase()]

  if (numA === numB && letterA === letterB) return 0 // same key
  if (letterA === letterB) {
    const diff = Math.min(Math.abs(numA - numB), 12 - Math.abs(numA - numB))
    if (diff === 1) return 1 // adjacent on the wheel
  }
  if (numA === numB && letterA !== letterB) return 1 // relative major/minor
  return 2 // clash
}

function bpmDistance(a: number, b: number): number {
  const direct = Math.abs(a - b)
  const halfDouble = Math.min(Math.abs(a * 2 - b), Math.abs(a - b * 2))
  return Math.min(direct, halfDouble)
}

/** Lower is a better transition. Missing bpm/key data on either side just
 * drops that dimension rather than penalizing it -- a track with no key
 * detected shouldn't look "incompatible" with everything. */
function transitionCost(a: MixableTrack, b: MixableTrack): number {
  let cost = 0
  if (a.key && b.key) cost += camelotDistance(a.key, b.key) * 10
  if (a.bpm !== null && b.bpm !== null) cost += Math.min(bpmDistance(a.bpm, b.bpm), 20)
  return cost
}

const MIN_TRACKS_FOR_SET_ORDER = 3

/** Greedy nearest-neighbor set order: start from the lowest-energy usable
 * track (a natural opener) and repeatedly pick whichever remaining track
 * mixes best out of the current one. Not a globally optimal ordering (that's
 * an NP-hard TSP) but instant even at 50 tracks, and this is the same
 * greedy heuristic harmonic-mixing tools use in practice.
 *
 * Tracks with no bpm/key/energy at all (failed detection) are left where
 * they were and appended at the end, since there's nothing to order them
 * by -- returns the input unchanged if too few tracks have usable data. */
export function suggestSetOrder<T extends MixableTrack>(tracks: T[]): T[] {
  const usable = tracks.filter((t) => t.bpm !== null || t.key !== null)
  const unusable = tracks.filter((t) => t.bpm === null && t.key === null)

  if (usable.length < MIN_TRACKS_FOR_SET_ORDER) return tracks

  const remaining = [...usable]
  remaining.sort((a, b) => (a.energy ?? 5) - (b.energy ?? 5))
  const ordered: T[] = [remaining.shift() as T]

  while (remaining.length > 0) {
    const current = ordered[ordered.length - 1]
    let bestIndex = 0
    let bestCost = Infinity
    for (let i = 0; i < remaining.length; i++) {
      const cost = transitionCost(current, remaining[i])
      if (cost < bestCost) {
        bestCost = cost
        bestIndex = i
      }
    }
    ordered.push(remaining.splice(bestIndex, 1)[0])
  }

  return [...ordered, ...unusable]
}
