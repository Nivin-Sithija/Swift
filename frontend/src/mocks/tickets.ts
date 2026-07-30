import type { Ticket } from "../types";

const now = Date.now();
const ago = (hours: number) => new Date(now - hours * 3_600_000).toISOString();
const categories = [
  "card_payment_wrong_exchange_rate",
  "cash_withdrawal",
  "cash_withdrawal_not_received",
  "pending_transfer",
  "beneficiary_not_allowed",
  "cash_withdrawal",
  "cash_withdrawal_not_received",
  "pending_transfer",
  "beneficiary_not_allowed",
  "cash_withdrawal",
  "cash_withdrawal_not_received",
  "pending_transfer",
  "beneficiary_not_allowed",
  "cash_withdrawal",
  "cash_withdrawal_not_received",
];
const samples = [
  ["Card payment reversed", "My card payment failed at the shop but the amount is still deducted.", "english"],
  ["ATM issue", "ATM එකෙන් සල්ලි ආවේ නැහැ, නමුත් account එකෙන් amount එක අඩු වෙලා.", "mixed"],
  ["பணம் கிடைக்கவில்லை", "ATM இல் பணம் எடுக்க முயன்றேன், ஆனால் பணம் வரவில்லை.", "tamil"],
  ["Transfer pending", "mage transfer eka dawas dekak thisse pending. check karanna.", "singlish"],
  ["Beneficiary blocked", "en beneficiary add panna mudiyala. error kaatudhu.", "tanglish"],
  ["Cannot access account", "I cannot sign in after changing my phone.", "english"],
  ["PIN අමතක වුණා", "මගේ card PIN එක අමතක වුණා. Reset කරන්නේ කොහොමද?", "mixed"],
  ["Suspicious transaction", "I do not recognise a card transaction made this morning.", "english"],
  ["Card dispute", "කාඩ් ගනුදෙනුවක් සම්බන්ධයෙන් පැමිණිල්ලක් කරන්න ඕන.", "sinhala"],
  ["Cash transfer problem", "cash transfer eka recipient ta gihin naha.", "singlish"],
  ["Loan enquiry", "What documents are required for a personal loan?", "english"],
  ["அடையாள சரிபார்ப்பு", "எனது அடையாளச் சரிபார்ப்பு தொடர்ந்து தோல்வியடைகிறது.", "tamil"],
  ["Cash deposit missing", "I deposited cash but it is not shown in my account.", "english"],
  ["Card delivery late", "en card delivery innum varala. status sollunga.", "tanglish"],
  ["Account information", "කරුණාකර savings account fees ගැන විස්තර දෙන්න.", "mixed"],
] as const;
const statuses = ["new", "assigned", "escalated", "in_review", "resolved", "closed", "reopened"] as const;
const priorities = ["critical", "high", "high", "medium", "medium", "low"] as const;
const sentiments = ["negative", "negative", "neutral", "positive"] as const;

export const mockTickets: Ticket[] = samples.map(([subject, message, language], index) => {
  const id = `SW-2026-${String(1042 - index).padStart(4, "0")}`;
  const status = statuses[index % statuses.length];
  const priority = priorities[index % priorities.length];
  const categoryConfidence = [94, 87, 72, 54, 83][index % 5];
  const hasImage = index % 3 === 0;
  const resolved = status === "resolved" || status === "closed";
  return {
    id,
    customerId: `CUST-••${String(4110 + index).slice(-4)}`,
    customerName: ["Maya Silva", "Nimal Perera", "Arun Kumar", "Sara Nizam"][index % 4],
    subject,
    message,
    preferredResponseLanguage: language === "tamil" || language === "tanglish" ? "tamil" : language === "sinhala" ? "sinhala" : "english",
    language,
    category: { value: categories[index], confidence: categoryConfidence, modelVersion: "classifier-preview-0.4", predictedAt: ago(index + 1) },
    priority: { value: priority, confidence: 68 + (index * 3) % 29, modelVersion: "priority-preview-0.3", predictedAt: ago(index + 1) },
    sentiment: { value: sentiments[index % sentiments.length], confidence: 61 + (index * 7) % 37, modelVersion: "sentiment-preview-0.5", predictedAt: ago(index + 1) },
    status,
    assignedQueue: priority === "critical" ? "Fraud & Security" : index % 2 ? "Payments" : "General Support",
    assignedAgent: index % 4 ? ["Anika Fernando", "Dilan Jay", "Meera Ravi"][index % 3] : null,
    createdAt: ago(index * 7 + 2),
    updatedAt: ago(index + 1),
    attachment: hasImage ? { id: `a-${index}`, name: `evidence-${index + 1}.png`, size: 284000, type: "image/png", url: `/mock-receipt.svg` } : undefined,
    imageEvidence: hasImage
      ? index === 3
        ? { status: "failed" }
        : { status: "processed", ocrText: `Transaction ref: MOCK-${18320 + index}\nStatus: Failed\nAmount: LKR ••••`, confidence: 82 + (index % 10) }
      : { status: "none" },
    events: [
      { id: `${id}-1`, label: "Submitted", detail: "Ticket received securely", at: ago(index * 7 + 2), customerVisible: true },
      { id: `${id}-2`, label: "Analysis completed", detail: "Advisory predictions prepared", at: ago(index * 7 + 1.8), customerVisible: true },
      ...(status !== "new" ? [{ id: `${id}-3`, label: status === "escalated" ? "Escalated" : "Assigned", detail: status === "escalated" ? "Forwarded for specialist review" : "Support team is reviewing", at: ago(index * 4 + 1), customerVisible: true }] : []),
    ],
    notes: index % 3 === 0 ? [{ id: `n-${index}`, author: "Anika Fernando", text: "Checked supplied evidence; reference is legible.", at: ago(index + 0.5) }] : [],
    draft: { text: `Hello, thank you for contacting Swift Support about “${subject}”. We have reviewed the information you provided. A support specialist will verify the relevant records and update you through this ticket.`, language: "english", updatedAt: ago(0.5), status: resolved ? "approved" : "draft" },
    approvedResponse: resolved ? { text: "We reviewed the details you shared and have completed the support review. Please contact us through this ticket if you need further assistance.", approvedBy: "Meera Ravi", approvedAt: ago(1) } : undefined,
    requiresManualReview: categoryConfidence < 60,
    escalationReason: status === "escalated" ? "Security-related category requires specialist review." : undefined,
  } satisfies Ticket;
});
