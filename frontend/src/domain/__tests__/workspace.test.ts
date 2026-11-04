import { describe, expect, it } from "vitest";
import { InvalidWorkspaceError, Workspace, WorkspaceType } from "../entities/workspace";

describe("Workspace Entity", () => {
  it("creates a valid station workspace with capacity 1", () => {
    const ws = Workspace.create({
      id: "ws-1",
      code: "ST-01",
      floor: "2",
      zone: "open",
      type: WorkspaceType.STATION,
      capacity: 1,
      isActive: true,
    });
    expect(ws.isStation()).toBe(true);
    expect(ws.capacity).toBe(1);
  });

  it("throws InvalidWorkspaceError if station capacity is not 1", () => {
    expect(() =>
      Workspace.create({
        id: "ws-2",
        code: "ST-02",
        floor: "2",
        zone: "open",
        type: WorkspaceType.STATION,
        capacity: 2,
      })
    ).toThrow(InvalidWorkspaceError);
  });

  it("creates a valid meeting room workspace with capacity >= 1", () => {
    const ws = Workspace.create({
      id: "ws-room",
      code: "MR-01",
      floor: "3",
      zone: "meeting",
      type: WorkspaceType.MEETING_ROOM,
      capacity: 8,
    });
    expect(ws.isMeetingRoom()).toBe(true);
    expect(ws.capacity).toBe(8);
  });

  it("throws InvalidWorkspaceError if meeting room capacity is 0 or negative", () => {
    expect(() =>
      Workspace.create({
        id: "ws-bad",
        code: "MR-BAD",
        floor: "3",
        zone: "meeting",
        type: WorkspaceType.MEETING_ROOM,
        capacity: 0,
      })
    ).toThrow(InvalidWorkspaceError);
  });
});

