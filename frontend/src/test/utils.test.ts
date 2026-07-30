import { mockTickets } from "../mocks/tickets";
import { confidenceBand, filterTickets, sortTickets } from "../lib/utils";
describe("ticket utilities", () => {
  it("sorts by each queue order the sort control offers", () => {
    expect(sortTickets(mockTickets, "priority")[0].priority.value).toBe(
      "critical",
    );
    const newest = sortTickets(mockTickets, "newest");
    expect(+new Date(newest[0].createdAt)).toBeGreaterThanOrEqual(
      +new Date(newest[newest.length - 1].createdAt),
    );
    const waiting = sortTickets(mockTickets, "waiting");
    expect(waiting[0].id).toBe(newest[newest.length - 1].id);
    const confidence = sortTickets(mockTickets, "confidence");
    expect(confidence[0].category.confidence).toBeLessThanOrEqual(
      confidence[confidence.length - 1].category.confidence,
    );
  });
  it("does not mutate the source list while sorting", () => {
    const before = mockTickets.map((t) => t.id);
    sortTickets(mockTickets, "confidence");
    expect(mockTickets.map((t) => t.id)).toEqual(before);
  });
  it("uses specified confidence thresholds", () => {
    expect(confidenceBand(80)).toBe("high");
    expect(confidenceBand(79)).toBe("medium");
    expect(confidenceBand(60)).toBe("medium");
    expect(confidenceBand(59)).toBe("low");
  });
  it("filters ticket text and priority together", () => {
    const result = filterTickets(mockTickets, {
      search: "ATM",
      priority: "high",
    });
    expect(result.length).toBeGreaterThan(0);
    expect(
      result.every(
        (t) =>
          t.priority.value === "high" &&
          `${t.id} ${t.subject} ${t.customerName}`
            .toLowerCase()
            .includes("atm"),
      ),
    ).toBe(true);
  });
  it("preserves multilingual messages exactly", () => {
    expect(mockTickets[1].message).toBe(
      "ATM එකෙන් සල්ලි ආවේ නැහැ, නමුත් account එකෙන් amount එක අඩු වෙලා.",
    );
    expect(mockTickets[2].message).toContain("பணம் வரவில்லை");
  });
});
