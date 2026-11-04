import { describe, expect, it } from "vitest";
import { QuotaExceededError, QuotaPeriod } from "../entities/quota-period";

describe("QuotaPeriod Entity (Invariant I3)", () => {
  const createQuota = () =>
    QuotaPeriod.create({
      costCenterId: "cc-1",
      periodStart: new Date("2026-11-01T00:00:00Z"),
      periodEnd: new Date("2026-11-30T23:59:59Z"),
      totalHours: 100,
      consumedHours: 20,
    });

  it("calculates remaining hours and usage percentage", () => {
    const quota = createQuota();
    expect(quota.remainingHours).toBe(80);
    expect(quota.usagePercent).toBe(20);
    expect(quota.getAlertLevel()).toBeNull();
  });

  it("consumes quota monotonically", () => {
    const quota = createQuota();
    const updated = quota.consume(30);
    expect(updated.consumedHours).toBe(50);
    expect(updated.remainingHours).toBe(50);
    expect(updated.usagePercent).toBe(50);
  });

  it("throws QuotaExceededError when consuming beyond total limit", () => {
    const quota = createQuota();
    expect(() => quota.consume(85)).toThrow(QuotaExceededError);
  });

  it("detects 80% and 95% quota alert thresholds", () => {
    const quota = createQuota();
    const at82 = quota.consume(62);
    expect(at82.usagePercent).toBe(82);
    expect(at82.getAlertLevel()).toBe(80);

    const at96 = at82.consume(14);
    expect(at96.usagePercent).toBe(96);
    expect(at96.getAlertLevel()).toBe(95);
  });

  it("refunds consumed hours on booking cancellation", () => {
    const quota = createQuota();
    const refunded = quota.refund(10);
    expect(refunded.consumedHours).toBe(10);
    expect(refunded.remainingHours).toBe(90);
  });

  it("throws when attempting to refund more than consumed", () => {
    const quota = createQuota();
    expect(() => quota.refund(25)).toThrow(Error);
  });
});

