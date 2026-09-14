// Direct port of src/contract_watchdog/tools/analysis.py's risk-phrase
// dictionaries. Same logic as the real agent, kept in sync by hand — if you
// change the Python source, update this too.

export const GENERAL_RISK_PHRASES: Record<string, string> = {
  "automatically renew": "Auto-renews without active opt-in from the counterparty.",
  "auto-renew": "Auto-renews without active opt-in from the counterparty.",
  "sole discretion": "Other party can change terms unilaterally.",
  "without notice": "Other party may act (e.g. change price) without warning.",
  "unilaterally": "Other party can change terms unilaterally.",
  "no refund": "No refund path if you cancel after billing.",
  "non-refundable": "No refund path if you cancel after billing.",
  "written notice": "Cancellation requires formal written notice — easy to miss the window.",
};

export const TYPE_SPECIFIC_RISK_PHRASES: Record<string, Record<string, string>> = {
  lease: {
    "security deposit is non-refundable": "Deposit forfeiture regardless of unit condition.",
    "joint and several liability": "Any one tenant can be held liable for the full amount.",
    "landlord may enter without": "Landlord can enter with little/no notice.",
    "early termination fee": "Breaking the lease early carries a penalty — check the amount.",
  },
  employment: {
    "non-compete": "Restricts working for competitors after leaving.",
    "at-will": "Employment can be terminated without cause.",
    "assignment of inventions": "Broad IP assignment — check scope (may extend beyond work hours/projects).",
    "no severance": "No severance obligation on termination.",
  },
  nda: {
    perpetual: "Confidentiality obligation never expires.",
    "survives termination": "Obligations continue indefinitely after the relationship ends.",
    "liquidated damages": "Pre-set penalty for breach, regardless of actual harm.",
  },
  vendor_saas: {},
};

export interface RiskMatch {
  phrase: string;
  reason: string;
}

export function scanForRisks(excerpt: string, contractType: string): RiskMatch[] {
  const lower = excerpt.toLowerCase();
  const phrases = { ...GENERAL_RISK_PHRASES, ...(TYPE_SPECIFIC_RISK_PHRASES[contractType] ?? {}) };
  return Object.entries(phrases)
    .filter(([phrase]) => lower.includes(phrase))
    .map(([phrase, reason]) => ({ phrase, reason }));
}

export const CONTRACT_TYPE_OPTIONS = [
  { value: "vendor_saas", label: "Vendor / SaaS" },
  { value: "lease", label: "Lease" },
  { value: "employment", label: "Employment" },
  { value: "nda", label: "NDA" },
];

export interface SampleContract {
  label: string;
  type: string;
  excerpt: string;
}

// A small pool of varied examples for the "Randomize example" button —
// intentionally different from the seeded portfolio contracts above, so
// this section feels like its own thing, not a copy of the real run.
export const SAMPLE_CONTRACTS: SampleContract[] = [
  {
    label: "Marketing analytics SaaS",
    type: "vendor_saas",
    excerpt:
      "This Agreement automatically renews for successive one-year terms. Vendor may, in its sole discretion, adjust subscription pricing for any renewal term. All fees are non-refundable once billed.",
  },
  {
    label: "Coworking space membership",
    type: "lease",
    excerpt:
      "Membership renews automatically each month. The security deposit is non-refundable upon termination. Management may enter the workspace without notice for maintenance purposes.",
  },
  {
    label: "Contractor engagement letter",
    type: "employment",
    excerpt:
      "This is an at-will engagement. Contractor agrees to a 12-month non-compete covering the same industry following termination. No severance is owed under any circumstance.",
  },
  {
    label: "Vendor mutual NDA",
    type: "nda",
    excerpt:
      "Confidential Information disclosed under this Agreement shall remain confidential in perpetuity. This obligation survives termination of the underlying commercial relationship indefinitely.",
  },
  {
    label: "Payroll platform renewal",
    type: "vendor_saas",
    excerpt:
      "Subscription fees are fixed for the initial term. Either party may cancel with thirty (30) days written notice prior to renewal. No automatic price escalation applies.",
  },
];
