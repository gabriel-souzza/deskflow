import { z } from "zod";

export enum EmployeeRole {
  EMPLOYEE = "employee",
  ADMIN = "admin",
}

export const EmployeeSchema = z.object({
  id: z.string().uuid().or(z.string()),
  name: z.string().min(1),
  email: z.string().email(),
  role: z.nativeEnum(EmployeeRole).default(EmployeeRole.EMPLOYEE),
  costCenterId: z.string().uuid().or(z.string()).nullable().optional(),
  costCenterName: z.string().nullable().optional(),
  isEligibleForBooking: z.boolean().default(false),
});

export type EmployeeData = z.infer<typeof EmployeeSchema>;

export class Employee {
  readonly id: string;
  readonly name: string;
  readonly email: string;
  readonly role: EmployeeRole;
  readonly costCenterId: string | null;
  readonly costCenterName: string | null;
  readonly isEligibleForBooking: boolean;

  constructor(data: EmployeeData) {
    this.id = data.id;
    this.name = data.name;
    this.email = data.email;
    this.role = data.role;
    this.costCenterId = data.costCenterId ?? null;
    this.costCenterName = data.costCenterName ?? null;
    this.isEligibleForBooking = data.isEligibleForBooking;
  }

  isAdmin(): boolean {
    return this.role === EmployeeRole.ADMIN;
  }
}

