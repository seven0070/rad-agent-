import { createContext, useContext } from "react";
import type { AuthoritySnapshot, ObjectiveRow, RadClient, Status } from "./api";

export interface RadCtx {
  client: RadClient;
  status: Status | null;
  auth: AuthoritySnapshot;
  selectedId: string | null;
  selected: ObjectiveRow | null;
  select: (id: string | null) => void;
  onAuth: (a: AuthoritySnapshot) => void;
  refresh: () => Promise<void>;
}

export const Ctx = createContext<RadCtx>(null as unknown as RadCtx);

export function useRad(): RadCtx {
  return useContext(Ctx);
}
