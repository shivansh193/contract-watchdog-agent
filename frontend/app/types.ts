export interface RiskMatch {
  phrase: string;
  reason: string;
}

export interface ContractRecord {
  id: string;
  counterparty: string;
  type: string;
  description: string;
  status: "flagged" | "reviewed";
  urgency: string | null;
  hasPrice: boolean;
  prevPrice: number;
  currPrice: number;
  pctChange: number;
  renewalDate: string;
  noticeDeadline: string | null;
  daysUntil: number | null;
  risks: RiskMatch[];
  reasoning: string | null;
  recommendedAction: string | null;
  hasEmail: boolean;
  emailSubject: string | null;
  emailBody: string | null;
  referencePricingNote: string | null;
  reviewedAt: string | null;
}

export interface PortfolioSnapshot {
  generatedAt: string;
  contracts: ContractRecord[];
}

export interface AuditEntry {
  timestamp: string;
  contractId: string;
  decision: string;
  notes: string;
}
