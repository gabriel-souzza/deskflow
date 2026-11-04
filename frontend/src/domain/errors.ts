export class DomainError extends Error {
  constructor(message: string) {
    super(message);
    this.name = this.constructor.name;
    Object.setPrototypeOf(this, new.target.prototype);
  }
}

export class InvalidTimeSlotError extends DomainError {}
export class InvalidStateTransitionError extends DomainError {}
export class InvalidCancellationError extends DomainError {}
export class QuotaExceededError extends DomainError {}
export class InvalidWorkspaceError extends DomainError {}

