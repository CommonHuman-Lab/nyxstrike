// ── Credentials ────────────────────────────────────────────────────────────────

export type CredentialType =
  | 'plaintext'
  | 'hash'
  | 'key'
  | 'token'
  | 'cookie'
  | 'certificate'
  | 'other';

export interface Credential {
  cred_id: string;
  type: CredentialType;
  username?: string;
  secret?: string;
  hash_type?: string;
  service?: string;
  host?: string;
  port?: number;
  source_tool?: string;
  evidence?: string;
  tags?: string[];
  verified?: boolean;
  notes?: string;
  session_id?: string;
  created_at: number;
  updated_at: number;
}

export interface CredentialsResponse {
  success: boolean;
  credentials: Credential[];
  total: number;
  error?: string;
}

export interface CredentialMutationResponse {
  success: boolean;
  credential?: Credential;
  timestamp?: string;
  error?: string;
}

export interface CredentialDeleteResponse {
  success: boolean;
  cred_id?: string;
  timestamp?: string;
  error?: string;
}

export type CreateCredentialPayload = {
  type: CredentialType;
  username?: string;
  secret?: string;
  hash_type?: string;
  service?: string;
  host?: string;
  port?: number;
  source_tool?: string;
  evidence?: string;
  tags?: string[];
  verified?: boolean;
  notes?: string;
  session_id?: string;
};

export type UpdateCredentialPayload = Partial<CreateCredentialPayload>;

// ── Loot ───────────────────────────────────────────────────────────────────────

export type LootType =
  | 'flag'
  | 'file'
  | 'config'
  | 'hash'
  | 'key'
  | 'secret'
  | 'screenshot'
  | 'other';

export interface LootItem {
  loot_id: string;
  loot_type: LootType;
  title: string;
  content?: string;
  path?: string;
  host?: string;
  source_tool?: string;
  tags?: string[];
  notes?: string;
  session_id?: string;
  created_at: number;
  updated_at: number;
}

export interface LootResponse {
  success: boolean;
  loot: LootItem[];
  total: number;
  error?: string;
}

export interface LootMutationResponse {
  success: boolean;
  loot?: LootItem;
  timestamp?: string;
  error?: string;
}

export interface LootDeleteResponse {
  success: boolean;
  loot_id?: string;
  timestamp?: string;
  error?: string;
}

export type CreateLootPayload = {
  loot_type: LootType;
  title: string;
  content?: string;
  path?: string;
  host?: string;
  source_tool?: string;
  tags?: string[];
  notes?: string;
  session_id?: string;
};

export type UpdateLootPayload = Partial<CreateLootPayload>;
