import { describe, expect, it } from "vitest";
import { InvalidTimeSlotError, TimeSlot } from "../value-objects/time-slot";

describe("TimeSlot Value Object (Invariant I1)", () => {
  it("creates a valid TimeSlot aligned to 15-minute grid", () => {
    const start = new Date("2026-11-10T09:00:00Z");
    const end = new Date("2026-11-10T10:30:00Z");
    const slot = TimeSlot.create(start, end);

    expect(slot.start).toEqual(start);
    expect(slot.end).toEqual(end);
    expect(slot.durationMinutes).toBe(90);
    expect(slot.durationHours).toBe(1.5);
  });

  it("throws InvalidTimeSlotError when minutes are not aligned to 15-minute boundary", () => {
    const start = new Date("2026-11-10T09:05:00Z");
    const end = new Date("2026-11-10T10:00:00Z");
    expect(() => TimeSlot.create(start, end)).toThrow(InvalidTimeSlotError);
  });

  it("throws InvalidTimeSlotError when seconds or milliseconds are non-zero", () => {
    const start = new Date("2026-11-10T09:00:01Z");
    const end = new Date("2026-11-10T10:00:00Z");
    expect(() => TimeSlot.create(start, end)).toThrow(InvalidTimeSlotError);
  });

  it("throws InvalidTimeSlotError when start is not strictly before end", () => {
    const start = new Date("2026-11-10T10:00:00Z");
    const end = new Date("2026-11-10T09:00:00Z");
    expect(() => TimeSlot.create(start, end)).toThrow(InvalidTimeSlotError);

    const same = new Date("2026-11-10T10:00:00Z");
    expect(() => TimeSlot.create(same, same)).toThrow(InvalidTimeSlotError);
  });

  it("throws InvalidTimeSlotError when slot spans multiple calendar days", () => {
    const start = new Date("2026-11-10T17:45:00Z");
    const end = new Date("2026-11-11T08:15:00Z");
    expect(() => TimeSlot.create(start, end)).toThrow(InvalidTimeSlotError);
  });

  it("detects overlaps between slots correctly", () => {
    const slot1 = TimeSlot.create(
      new Date("2026-11-10T09:00:00Z"),
      new Date("2026-11-10T10:30:00Z")
    );
    const slot2 = TimeSlot.create(
      new Date("2026-11-10T10:00:00Z"),
      new Date("2026-11-10T11:00:00Z")
    );
    const slot3 = TimeSlot.create(
      new Date("2026-11-10T10:30:00Z"),
      new Date("2026-11-10T11:30:00Z")
    );

    expect(slot1.overlaps(slot2)).toBe(true);
    expect(slot2.overlaps(slot1)).toBe(true);
    expect(slot1.overlaps(slot3)).toBe(false);
  });

  it("breaks slot into 15-minute sub-intervals", () => {
    const slot = TimeSlot.create(
      new Date("2026-11-10T09:00:00Z"),
      new Date("2026-11-10T10:00:00Z")
    );
    const intervals = slot.to15MinIntervals();
    expect(intervals).toHaveLength(4);
    expect(intervals[0]?.toISOString()).toBe("2026-11-10T09:00:00.000Z");
    expect(intervals[3]?.toISOString()).toBe("2026-11-10T09:45:00.000Z");
  });
});

