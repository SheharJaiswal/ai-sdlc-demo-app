namespace InvoiceApp.Domain;

public class Invoice
{
    public string Id { get; set; } = string.Empty;
    public string CustomerName { get; set; } = string.Empty;
    public decimal Amount { get; set; }
    public InvoiceStatus Status { get; set; } = InvoiceStatus.Draft;
    public DateTime CreatedAt { get; set; } = DateTime.UtcNow;
    public string? DecidedBy { get; set; }
    public DateTime? DecidedAt { get; set; }
    public string? DecisionNote { get; set; }
    public IReadOnlyList<ApprovalRecord> ApprovalHistory { get; private set; } = Array.Empty<ApprovalRecord>();

    public void RecordApproval(ApprovalActor actor, DateTimeOffset timestamp) =>
        ApprovalHistory = ApprovalHistory.Append(new ApprovalRecord(actor.Identity, actor.Role, timestamp)).ToArray();

    public Invoice Copy()
    {
        return new Invoice
        {
            Id = Id,
            CustomerName = CustomerName,
            Amount = Amount,
            Status = Status,
            CreatedAt = CreatedAt,
            DecidedBy = DecidedBy,
            DecidedAt = DecidedAt,
            DecisionNote = DecisionNote,
            ApprovalHistory = ApprovalHistory.ToArray()
        };
    }
}
