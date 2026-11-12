namespace InvoiceApp.Domain;

/// <summary>
/// Moves an invoice through its lifecycle: Draft -> PendingApproval -> Approved or Rejected.
/// Approval and rejection policy is evaluated and recorded atomically by the repository.
/// </summary>
public class ApprovalService
{
    private readonly IInvoiceRepository _repository;

    public ApprovalService(IInvoiceRepository repository)
    {
        _repository = repository;
    }

    public Invoice Submit(string invoiceId)
    {
        var invoice = Find(invoiceId);

        if (invoice.Status != InvoiceStatus.Draft)
        {
            throw new InvalidOperationException(
                $"Invoice {invoiceId} is {invoice.Status}; only drafts can be submitted.");
        }

        invoice.Status = InvoiceStatus.PendingApproval;
        _repository.Update(invoice);
        return invoice;
    }

    public Invoice Approve(string invoiceId, ApprovalActor actor)
    {
        ValidateActor(actor);
        return _repository.TransitionAtomically(invoiceId, invoice => ApprovePendingInvoice(invoice, actor));
    }

    public Invoice Reject(string invoiceId, ApprovalActor actor, string reason)
    {
        if (string.IsNullOrWhiteSpace(reason))
        {
            throw new ArgumentException("A reason is required to reject an invoice.", nameof(reason));
        }

        return _repository.TransitionAtomically(invoiceId, invoice =>
        {
            EnsurePending(invoice);

            invoice.Status = InvoiceStatus.Rejected;
            invoice.DecidedBy = actor.Identity;
            invoice.DecidedAt = DateTime.UtcNow;
            invoice.DecisionNote = reason;
            return invoice;
        });
    }

    private Invoice Find(string invoiceId) =>
        _repository.GetById(invoiceId)
        ?? throw new KeyNotFoundException($"Invoice {invoiceId} was not found.");

    private static void EnsurePending(Invoice invoice)
    {
        if (invoice.Status != InvoiceStatus.PendingApproval)
        {
            throw new InvalidOperationException(
                $"Invoice {invoice.Id} is {invoice.Status}; only pending invoices can be decided.");
        }
    }

    private static Invoice ApprovePendingInvoice(Invoice invoice, ApprovalActor actor)
    {
        EnsurePending(invoice);

        if (invoice.Amount <= 50_000m)
        {
            CompleteApproval(invoice, actor);
            return invoice;
        }

        if (invoice.Amount <= 500_000m)
        {
            if (actor.Role != ApprovalRole.Director)
            {
                throw new InvalidOperationException("Invoices above 50,000 require Director approval.");
            }

            CompleteApproval(invoice, actor);
            return invoice;
        }

        if (invoice.ApprovalHistory.Any(approval => approval.Identity == actor.Identity))
        {
            throw new InvalidOperationException("The same authenticated user cannot approve an invoice twice.");
        }

        if (invoice.ApprovalHistory.Count == 0)
        {
            invoice.RecordApproval(actor, DateTimeOffset.UtcNow);
            return invoice;
        }

        if (invoice.ApprovalHistory.Count != 1)
        {
            throw new InvalidOperationException("Invoice approval history is not valid for another approval.");
        }

        if (actor.Role != ApprovalRole.Director)
        {
            throw new InvalidOperationException("The second approval for an invoice above 500,000 must be from a different Director.");
        }

        CompleteApproval(invoice, actor);
        return invoice;
    }

    private static void CompleteApproval(Invoice invoice, ApprovalActor actor)
    {
        var approvedAt = DateTimeOffset.UtcNow;
        invoice.RecordApproval(actor, approvedAt);
        invoice.Status = InvoiceStatus.Approved;
        invoice.DecidedBy = actor.Identity;
        invoice.DecidedAt = approvedAt.UtcDateTime;
    }

    private static void ValidateActor(ApprovalActor actor)
    {
        if (string.IsNullOrWhiteSpace(actor.Identity))
        {
            throw new ArgumentException("An authenticated approver identity is required.", nameof(actor));
        }

        if (actor.Role is not ApprovalRole.Manager and not ApprovalRole.Director)
        {
            throw new ArgumentException("Approvals require a Manager or Director role.", nameof(actor));
        }
    }
}
