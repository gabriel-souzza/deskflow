import { z } from "zod";
import { InvalidWorkspaceError } from "../errors";

export { InvalidWorkspaceError };

export enum WorkspaceType {
  STATION = "estacao",
  MEETING_ROOM = "sala",
}

export const WorkspaceSchema = z.object({
  id: z.string().uuid().or(z.string()),
  code: z.string().min(1),
  floor: z.string().min(1),
  zone: z.string().min(1),
  type: z.nativeEnum(WorkspaceType),
  capacity: z.number().int().positive(),
  resources: z.union([z.array(z.string()), z.record(z.unknown())]).default([]),
  isActive: z.boolean().default(true),
});

export type WorkspaceData = z.infer<typeof WorkspaceSchema>;

export class Workspace {
  readonly id: string;
  readonly code: string;
  readonly floor: string;
  readonly zone: string;
  readonly type: WorkspaceType;
  readonly capacity: number;
  readonly resources: string[] | Record<string, unknown>;
  readonly isActive: boolean;

  private constructor(params: {
    id: string;
    code: string;
    floor: string;
    zone: string;
    type: WorkspaceType;
    capacity: number;
    resources?: string[] | Record<string, unknown>;
    isActive?: boolean;
  }) {
    this.validate(params.type, params.capacity);
    this.id = params.id;
    this.code = params.code;
    this.floor = params.floor;
    this.zone = params.zone;
    this.type = params.type;
    this.capacity = params.capacity;
    this.resources = params.resources ?? [];
    this.isActive = params.isActive ?? true;
  }

  static create(params: {
    id: string;
    code: string;
    floor: string;
    zone: string;
    type: WorkspaceType;
    capacity: number;
    resources?: string[] | Record<string, unknown>;
    isActive?: boolean;
  }): Workspace {
    return new Workspace(params);
  }

  getResourceList(): string[] {
    if (Array.isArray(this.resources)) {
      return this.resources;
    }
    if (this.resources && typeof this.resources === "object") {
      return Object.keys(this.resources);
    }
    return [];
  }

  private validate(type: WorkspaceType, capacity: number): void {
    if (capacity <= 0 || !Number.isInteger(capacity)) {
      throw new InvalidWorkspaceError("Workspace capacity must be a positive integer.");
    }
    if (type === WorkspaceType.STATION && capacity !== 1) {
      throw new InvalidWorkspaceError(
        "Individual workstations ('estacao') must have a capacity of exactly 1 seat."
      );
    }
  }

  isStation(): boolean {
    return this.type === WorkspaceType.STATION;
  }

  isMeetingRoom(): boolean {
    return this.type === WorkspaceType.MEETING_ROOM;
  }
}

