import { z } from "zod";
import {
  InvalidCancellationError,
  InvalidStateTransitionError,
} from "../errors";
import { TimeSlot, TimeSlotSchema } from "../value-objects/time-slot";

export { InvalidCancellationError, InvalidStateTransitionError };

export enum BookingStatus {
  PENDING = "PENDING",
  CONFIRMED = "CONFIRMED",
  CANCELLED = "CANCELLED",
  EXPIRED = "EXPIRED",
}

export const BookingSchema = z.object({
  id: z.string().uuid().or(z.string()),
  workspaceId: z.string().uuid().or(z.string()),
  employeeId: z.string().uuid().or(z.string()),
  costCenterId: z.string().uuid().or(z.string()),
  slot: TimeSlotSchema,
  status: z.nativeEnum(BookingStatus).default(BookingStatus.PENDING),
  createdAt: z.coerce.date().default(() => new Date()),
  confirmedAt: z.coerce.date().nullable().optional(),
  cancelledAt: z.coerce.date().nullable().optional(),
});

export type BookingData = z.infer<typeof BookingSchema>;

export class Booking {
  readonly id: string;
  readonly workspaceId: string;
  readonly employeeId: string;
  readonly costCenterId: string;
  readonly slot: TimeSlot;
  readonly status: BookingStatus;
  readonly createdAt: Date;
  readonly confirmedAt: Date | null;
  readonly cancelledAt: Date | null;

  private constructor(params: {
    id: string;
    workspaceId: string;
    employeeId: string;
    costCenterId: string;
    slot: TimeSlot;
    status: BookingStatus;
    createdAt?: Date;
    confirmedAt?: Date | null;
    cancelledAt?: Date | null;
  }) {
    this.id = params.id;
    this.workspaceId = params.workspaceId;
    this.employeeId = params.employeeId;
    this.costCenterId = params.costCenterId;
    this.slot = params.slot;
    this.status = params.status;
    this.createdAt = params.createdAt ?? new Date();
    this.confirmedAt = params.confirmedAt ?? null;
    this.cancelledAt = params.cancelledAt ?? null;
  }

  static create(params: {
    id: string;
    workspaceId: string;
    employeeId: string;
    costCenterId: string;
    slot: TimeSlot;
    status?: BookingStatus;
    createdAt?: Date;
    confirmedAt?: Date | null;
    cancelledAt?: Date | null;
  }): Booking {
    return new Booking({
      ...params,
      status: params.status ?? BookingStatus.PENDING,
    });
  }

  isPending(): boolean {
    return this.status === BookingStatus.PENDING;
  }

  isConfirmed(): boolean {
    return this.status === BookingStatus.CONFIRMED;
  }

  isCancelled(): boolean {
    return this.status === BookingStatus.CANCELLED;
  }

  isExpired(): boolean {
    return this.status === BookingStatus.EXPIRED;
  }

  confirm(now: Date = new Date()): Booking {
    if (this.status !== BookingStatus.PENDING) {
      throw new InvalidStateTransitionError(
        `Cannot confirm booking in state '${this.status}'. Only PENDING bookings can be confirmed.`
      );
    }
    return new Booking({
      ...this,
      status: BookingStatus.CONFIRMED,
      confirmedAt: now,
    });
  }

  cancel(now: Date = new Date()): Booking {
    if (
      this.status !== BookingStatus.PENDING &&
      this.status !== BookingStatus.CONFIRMED
    ) {
      throw new InvalidStateTransitionError(
        `Cannot cancel booking in state '${this.status}'.`
      );
    }

    const twoHoursMs = 2 * 60 * 60 * 1000;
    const diff = this.slot.start.getTime() - now.getTime();

    if (diff < twoHoursMs) {
      throw new InvalidCancellationError(
        "Cancellation is only allowed with at least 2 hours of advance notice."
      );
    }

    return new Booking({
      ...this,
      status: BookingStatus.CANCELLED,
      cancelledAt: now,
    });
  }

  expire(): Booking {
    if (this.status !== BookingStatus.PENDING) {
      throw new InvalidStateTransitionError(
        `Cannot expire booking in state '${this.status}'. Only PENDING bookings can expire.`
      );
    }
    return new Booking({
      ...this,
      status: BookingStatus.EXPIRED,
    });
  }
}

