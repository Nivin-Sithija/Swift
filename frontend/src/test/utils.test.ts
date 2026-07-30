import { mockTickets } from "../mocks/tickets";
import { confidenceBand, filterTickets } from "../lib/utils";
describe("ticket utilities",()=>{
 it("uses specified confidence thresholds",()=>{expect(confidenceBand(80)).toBe("high");expect(confidenceBand(79)).toBe("medium");expect(confidenceBand(60)).toBe("medium");expect(confidenceBand(59)).toBe("low")});
 it("filters ticket text and priority together",()=>{const result=filterTickets(mockTickets,{search:"ATM",priority:"high"});expect(result.length).toBeGreaterThan(0);expect(result.every(t=>t.priority.value==="high"&&(`${t.id} ${t.subject} ${t.customerName}`).toLowerCase().includes("atm"))).toBe(true)});
 it("preserves multilingual messages exactly",()=>{expect(mockTickets[1].message).toBe("ATM එකෙන් සල්ලි ආවේ නැහැ, නමුත් account එකෙන් amount එක අඩු වෙලා.");expect(mockTickets[2].message).toContain("பணம் வரவில்லை")});
});
