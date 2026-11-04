import { z } from "zod";
import { TimeSlot, TimeSlotSchema } from "../value-objects/time-slot";

export const WaitlistEntrySchema = z.object({
  id: z.string().uuid().or(z.string()),
  workspaceId: z.string().uuid().or(z.string()),
  employeeId: z.string().uuid().or(z.string()),
  desiredSlot: TimeSlotSchema,
  createdAt: z.coerce.date().default(() => new Date()),
  notifiedAt: z.coerce.date().nullable().optional(),
});

export type WaitlistEntryData = z.infer<typeof WaitlistEntrySchema>;

export class WaitlistEntry {
  readonly id: string;
  readonly workspaceId: string;
  readonly employeeId: string;
  readonly desiredSlot: TimeSlot;
  readonly createdAt: Date;
  readonly notifiedAt: Date | null;

  private constructor(params: {
    id: string;
    workspaceId: string;
    employeeId: string;
    desiredSlot: TimeSlot;
    createdAt?: Date;
    notifiedAt?: Date | null;
  }) {
    this.id = params.id;
    this.workspaceId = params.workspaceId;
    this.employeeId = params.employeeId;
    this.desiredSlot = params.desiredSlot;
    this.createdAt = params.createdAt ?? new Date();
    this.notifiedAt = params.notifiedAt ?? null;
  }

  static create(params: {
    id: string;
    workspaceId: string;
    employeeId: string;
    desiredSlot: TimeSlot;
    createdAt?: Date;
    notifiedAt?: Date | null;
  }): WaitlistEntry {
    return new WaitlistEntry(params);
  }

  isNotified(): boolean {
    return this.notifiedAt !== null;
  }

  isHoldActive(now: Date = new Date()): boolean {
    if (!this.notifiedAt) return false;
    const fiveMinutesMs = 5 * 60 * 1000;
    const diff = now.getTime() - this.notifiedAt.getTime();
    return diff >= 0 && diff < fiveMinutesMs;
  }

  remainingHoldSeconds(now: Date = new Date()): number {
    if (!this.notifiedAt) return 0;
    const fiveMinutesMs = 5 * 60 * 1000;
    const diff = now.getTime() - this.notifiedAt.getTime();
    if (diff < 0 || diff >= fiveMinutesMs) return 0;
    return Math.floor((fiveMinutesMs - diff) / 1000);
  }
}

