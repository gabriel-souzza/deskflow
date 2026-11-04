import { describe, expect, it } from "vitest";
import { WaitlistEntry } from "../entities/waitlist";
import { TimeSlot } from "../value-objects/time-slot";

describe("Waitlist Entry (UC05 / Anti-Sniping)", () => {
  const slot = TimeSlot.create(
    new Date("2026-11-10T09:00:00Z"),
    new Date("2026-11-10T10:00:00Z")
  );

  it("checks if hold is active within 5 minutes of notification", () => {
    const notifiedAt = new Date("2026-11-10T08:00:00Z");
    const entry = WaitlistEntry.create({
      id: "wl-1",
      workspaceId: "ws-1",
      employeeId: "emp-1",
      desiredSlot: slot,
      createdAt: new Date("2026-11-09T18:00:00Z"),
      notifiedAt,
    });

    expect(entry.isNotified()).toBe(true);

    const twoMinutesLater = new Date("2026-11-10T08:02:00Z");
    expect(entry.isHoldActive(twoMinutesLater)).toBe(true);
    expect(entry.remainingHoldSeconds(twoMinutesLater)).toBe(180);

    const sixMinutesLater = new Date("2026-11-10T08:06:00Z");
    expect(entry.isHoldActive(sixMinutesLater)).toBe(false);
    expect(entry.remainingHoldSeconds(sixMinutesLater)).toBe(0);
  });
});

