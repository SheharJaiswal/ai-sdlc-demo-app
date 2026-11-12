namespace InvoiceApp.Domain;

public enum ApprovalRole
{
    Manager,
    Director
}

/// <summary>Stable, authenticated identity and role used for an approval decision.</summary>
public sealed record ApprovalActor(string Identity, ApprovalRole Role);

/// <summary>An immutable audit entry for an accepted approval.</summary>
public sealed record ApprovalRecord(string Identity, ApprovalRole Role, DateTimeOffset ApprovedAt);
