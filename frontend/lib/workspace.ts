export type WorkspaceDraft = {
  workspaceId: string;
  workspaceName?: string;
  brandName: string;
  website: string;
  industry: string;
  category?: string;
  geography?: string;
  positioning: string;
  additionalDetails?: string;
  brandSummary?: string;
  brandAnalysis?: Record<string, string>;
  keyPages: string[];
  docs: Array<{
    name: string;
    content: string;
    contentType: string;
    sizeBytes: number;
    kind: string;
  }>;
};

type WorkspaceIndexEntry = {
  workspaceId: string;
  workspaceName: string;
  brandName: string;
  updatedAt: string;
};

const LEGACY_KEY = "marketing_agents_workspace_v1";
const ACTIVE_KEY = "marketing_agents_active_workspace";
const INDEX_KEY = "marketing_agents_workspaces_index_v1";
const PREFIX = "marketing_agents_workspace_v2_";

function getCryptoKey(seed: string): string {
  return btoa(seed).slice(0, 24);
}

function bytesToBase64(bytes: Uint8Array): string {
  let binary = "";
  const chunkSize = 0x8000;
  for (let i = 0; i < bytes.length; i += chunkSize) {
    const chunk = bytes.subarray(i, i + chunkSize);
    binary += String.fromCharCode(...chunk);
  }
  return btoa(binary);
}

function base64ToBytes(base64: string): Uint8Array {
  const binary = atob(base64);
  const bytes = new Uint8Array(binary.length);
  for (let i = 0; i < binary.length; i += 1) {
    bytes[i] = binary.charCodeAt(i);
  }
  return bytes;
}

export function encryptLocal(payload: string, seed: string): string {
  const key = getCryptoKey(seed);
  const payloadBytes = new TextEncoder().encode(payload);
  const outBytes = new Uint8Array(payloadBytes.length);
  for (let i = 0; i < payloadBytes.length; i += 1) {
    outBytes[i] = payloadBytes[i] ^ key.charCodeAt(i % key.length);
  }
  return bytesToBase64(outBytes);
}

export function decryptLocal(payload: string, seed: string): string {
  const key = getCryptoKey(seed);
  const rawBytes = base64ToBytes(payload);
  const outBytes = new Uint8Array(rawBytes.length);
  for (let i = 0; i < rawBytes.length; i += 1) {
    outBytes[i] = rawBytes[i] ^ key.charCodeAt(i % key.length);
  }
  return new TextDecoder().decode(outBytes);
}

function workspaceStorageKey(workspaceId: string): string {
  return `${PREFIX}${workspaceId}`;
}

function readIndex(): WorkspaceIndexEntry[] {
  if (typeof window === "undefined") return [];
  const raw = localStorage.getItem(INDEX_KEY);
  if (!raw) return [];
  try {
    const parsed = JSON.parse(raw) as WorkspaceIndexEntry[];
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
}

function writeIndex(rows: WorkspaceIndexEntry[]): void {
  if (typeof window === "undefined") return;
  localStorage.setItem(INDEX_KEY, JSON.stringify(rows));
}

export function setActiveWorkspaceId(workspaceId: string): void {
  if (typeof window === "undefined") return;
  localStorage.setItem(ACTIVE_KEY, workspaceId);
}

export function getActiveWorkspaceId(): string {
  if (typeof window === "undefined") return "ws_local_demo";
  return localStorage.getItem(ACTIVE_KEY) || "ws_local_demo";
}

export function saveWorkspaceLocal(draft: WorkspaceDraft): void {
  if (typeof window === "undefined") return;
  const seed = draft.workspaceId || "default";
  const encrypted = encryptLocal(JSON.stringify(draft), seed);
  localStorage.setItem(workspaceStorageKey(draft.workspaceId), encrypted);
  setActiveWorkspaceId(draft.workspaceId);

  const now = new Date().toISOString();
  const current = readIndex().filter((item) => item.workspaceId !== draft.workspaceId);
  current.unshift({
    workspaceId: draft.workspaceId,
    workspaceName: draft.workspaceName || draft.brandName || draft.workspaceId,
    brandName: draft.brandName,
    updatedAt: now,
  });
  writeIndex(current);
}

export function listWorkspaceLocalIndex(): WorkspaceIndexEntry[] {
  return readIndex();
}

export function loadWorkspaceLocal(workspaceId: string): WorkspaceDraft | null {
  if (typeof window === "undefined") return null;
  const encrypted = localStorage.getItem(workspaceStorageKey(workspaceId));
  if (encrypted) {
    try {
      const decrypted = decryptLocal(encrypted, workspaceId || "default");
      return JSON.parse(decrypted) as WorkspaceDraft;
    } catch {
      return null;
    }
  }

  // Backward compatibility for single-workspace legacy storage.
  const legacy = localStorage.getItem(LEGACY_KEY);
  if (!legacy) return null;
  try {
    const decrypted = decryptLocal(legacy, workspaceId || "default");
    const parsed = JSON.parse(decrypted) as WorkspaceDraft;
    saveWorkspaceLocal(parsed);
    localStorage.removeItem(LEGACY_KEY);
    return parsed;
  } catch {
    return null;
  }
}
