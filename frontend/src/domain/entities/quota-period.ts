import { z } from "zod";
import { QuotaExceededError } from "../errors";

export { QuotaExceededError };

export const QuotaPeriodSchema = z.object({
  costCenterId: z.string().uuid().or(z.string()),
  periodStart: z.coerce.date(),
  periodEnd: z.coerce.date(),
  totalHours: z.number().nonnegative(),
  consumedHours: z.number().nonnegative().default(0),
});

export type QuotaPeriodData = z.infer<typeof QuotaPeriodSchema>;

export class QuotaPeriod {
  readonly costCenterId: string;
  readonly periodStart: Date;
  readonly periodEnd: Date;
  readonly totalHours: number;
  readonly consumedHours: number;

  private constructor(params: {
    costCenterId: string;
    periodStart: Date;
    periodEnd: Date;
    totalHours: number;
    consumedHours: number;
  }) {
    this.costCenterId = params.costCenterId;
    this.periodStart = params.periodStart;
    this.periodEnd = params.periodEnd;
    this.totalHours = params.totalHours;
    this.consumedHours = params.consumedHours;
  }

  static create(params: {
    costCenterId: string;
    periodStart: Date | string;
    periodEnd: Date | string;
    totalHours: number;
    consumedHours?: number;
  }): QuotaPeriod {
    return new QuotaPeriod({
      costCenterId: params.costCenterId,
      periodStart:
        typeof params.periodStart === "string"
          ? new Date(params.periodStart)
          : params.periodStart,
      periodEnd:
        typeof params.periodEnd === "string"
          ? new Date(params.periodEnd)
          : params.periodEnd,
      totalHours: params.totalHours,
      consumedHours: params.consumedHours ?? 0,
    });
  }

  get remainingHours(): number {
    return Math.max(0, this.totalHours - this.consumedHours);
  }

  get usagePercent(): number {
    if (this.totalHours <= 0) return 0;
    return Number(((this.consumedHours / this.totalHours) * 100).toFixed(1));
  }

  getAlertLevel(): 80 | 95 | null {
    if (this.usagePercent >= 95) return 95;
    if (this.usagePercent >= 80) return 80;
    return null;
  }

  consume(hours: number): QuotaPeriod {
    if (hours < 0) {
      throw new Error("Cannot consume negative hours. Use refund() instead.");
    }
    const newConsumed = this.consumedHours + hours;
    if (newConsumed > this.totalHours) {
      throw new QuotaExceededError(
        `Monthly quota limit exceeded. Available: ${this.remainingHours.toFixed(1)}h, Requested: ${hours.toFixed(1)}h.`
      );
    }
    return new QuotaPeriod({
      ...this,
      consumedHours: newConsumed,
    });
  }

  refund(hours: number): QuotaPeriod {
    if (hours < 0) {
      throw new Error("Refund amount must be positive.");
    }
    if (hours > this.consumedHours) {
      throw new Error(
        `Cannot refund ${hours}h because only ${this.consumedHours}h were consumed.`
      );
    }
    return new QuotaPeriod({
      ...this,
      consumedHours: this.consumedHours - hours,
    });
  }
}

