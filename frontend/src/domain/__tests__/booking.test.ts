import { describe, expect, it } from "vitest";
import {
  Booking,
  BookingStatus,
  InvalidCancellationError,
  InvalidStateTransitionError,
} from "../entities/booking";
import { TimeSlot } from "../value-objects/time-slot";

describe("Booking Entity (Invariant I4)", () => {
  const slot = TimeSlot.create(
    new Date("2026-11-10T14:00:00Z"),
    new Date("2026-11-10T16:00:00Z")
  );

  const createPendingBooking = () =>
    Booking.create({
      id: "booking-123",
      workspaceId: "ws-1",
      employeeId: "emp-1",
      costCenterId: "cc-1",
      slot,
      status: BookingStatus.PENDING,
    });

  it("creates a pending booking successfully", () => {
    const booking = createPendingBooking();
    expect(booking.id).toBe("booking-123");
    expect(booking.status).toBe(BookingStatus.PENDING);
    expect(booking.isPending()).toBe(true);
  });

  it("confirms a pending booking", () => {
    const booking = createPendingBooking();
    const confirmed = booking.confirm();
    expect(confirmed.status).toBe(BookingStatus.CONFIRMED);
    expect(confirmed.isConfirmed()).toBe(true);
  });

  it("cannot confirm an already confirmed or cancelled booking", () => {
    const booking = createPendingBooking().confirm();
    expect(() => booking.confirm()).toThrow(InvalidStateTransitionError);

    const cancelled = createPendingBooking().cancel(new Date("2026-11-10T10:00:00Z"));
    expect(() => cancelled.confirm()).toThrow(InvalidStateTransitionError);
  });

  it("cancels booking with >= 2h advance notice", () => {
    const booking = createPendingBooking();
    const now = new Date("2026-11-10T11:59:00Z");
    const cancelled = booking.cancel(now);
    expect(cancelled.status).toBe(BookingStatus.CANCELLED);
    expect(cancelled.isCancelled()).toBe(true);
  });

  it("throws InvalidCancellationError when attempting to cancel with < 2h notice", () => {
    const booking = createPendingBooking();
    const late = new Date("2026-11-10T12:01:00Z");
    expect(() => booking.cancel(late)).toThrow(InvalidCancellationError);
  });

  it("expires a pending booking", () => {
    const booking = createPendingBooking();
    const expired = booking.expire();
    expect(expired.status).toBe(BookingStatus.EXPIRED);
    expect(expired.isExpired()).toBe(true);
  });
});

