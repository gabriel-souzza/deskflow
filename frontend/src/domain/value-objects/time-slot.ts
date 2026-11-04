import { z } from "zod";
import { InvalidTimeSlotError } from "../errors";

export { InvalidTimeSlotError };

export const TimeSlotSchema = z
  .object({
    start: z.coerce.date(),
    end: z.coerce.date(),
  })
  .refine((data) => data.start < data.end, {
    message: "Start must be strictly before end",
  });

export type TimeSlotData = z.infer<typeof TimeSlotSchema>;

export class TimeSlot {
  readonly start: Date;
  readonly end: Date;

  private constructor(start: Date, end: Date) {
    this.validate(start, end);
    this.start = new Date(start.getTime());
    this.end = new Date(end.getTime());
  }

  static create(start: Date | string, end: Date | string): TimeSlot {
    const s = typeof start === "string" ? new Date(start) : start;
    const e = typeof end === "string" ? new Date(end) : end;
    return new TimeSlot(s, e);
  }

  private validate(start: Date, end: Date): void {
    if (isNaN(start.getTime()) || isNaN(end.getTime())) {
      throw new InvalidTimeSlotError("Start and end must be valid dates");
    }

    if (start.getTime() >= end.getTime()) {
      throw new InvalidTimeSlotError("Start time must be strictly before end time");
    }

    if (
      start.getSeconds() !== 0 ||
      start.getMilliseconds() !== 0 ||
      end.getSeconds() !== 0 ||
      end.getMilliseconds() !== 0
    ) {
      throw new InvalidTimeSlotError(
        "Seconds and milliseconds must be zero in 15-minute grid"
      );
    }

    if (start.getMinutes() % 15 !== 0 || end.getMinutes() % 15 !== 0) {
      throw new InvalidTimeSlotError(
        "Minutes must align to 15-minute boundary (00, 15, 30, 45)"
      );
    }

    const isSameDay =
      start.getUTCFullYear() === end.getUTCFullYear() &&
      start.getUTCMonth() === end.getUTCMonth() &&
      start.getUTCDate() === end.getUTCDate();

    if (!isSameDay) {
      throw new InvalidTimeSlotError("TimeSlot cannot span multiple calendar days");
    }
  }

  get durationMinutes(): number {
    return (this.end.getTime() - this.start.getTime()) / (1000 * 60);
  }

  get durationHours(): number {
    return this.durationMinutes / 60;
  }

  overlaps(other: TimeSlot): boolean {
    return !(
      other.end.getTime() <= this.start.getTime() ||
      other.start.getTime() >= this.end.getTime()
    );
  }

  contains(other: TimeSlot): boolean {
    return (
      other.start.getTime() >= this.start.getTime() &&
      other.end.getTime() <= this.end.getTime()
    );
  }

  to15MinIntervals(): Date[] {
    const intervals: Date[] = [];
    let current = this.start.getTime();
    const end = this.end.getTime();

    while (current < end) {
      intervals.push(new Date(current));
      current += 15 * 60 * 1000;
    }
    return intervals;
  }

  toISOString(): string {
    return `${this.start.toISOString()}_${this.end.toISOString()}`;
  }
}

