import { create } from "zustand";
import { createJSONStorage, persist } from "zustand/middleware";

// A view convenience, not data: the jobs this browser opened, to find them again (§8.3).
// Only identifiers are kept; nothing of an invoice reaches browser storage.
const MAX_RECENT_JOBS = 8;

interface RecentJobsState {
  jobIds: string[];
  remember: (jobId: string) => void;
  forget: (jobId: string) => void;
}

export const useRecentJobs = create<RecentJobsState>()(
  persist(
    (set) => ({
      jobIds: [],
      remember: (jobId) =>
        set((state) => ({
          jobIds: [jobId, ...state.jobIds.filter((id) => id !== jobId)].slice(0, MAX_RECENT_JOBS),
        })),
      forget: (jobId) => set((state) => ({ jobIds: state.jobIds.filter((id) => id !== jobId) })),
    }),
    { name: "sextante-recent-jobs", storage: createJSONStorage(() => localStorage) },
  ),
);
