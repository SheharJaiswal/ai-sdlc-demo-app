using InvoiceApp.Api;
using InvoiceApp.Domain;
using Xunit;

namespace InvoiceApp.Tests;

public class InMemoryInvoiceRepositoryTests
{
    [Fact]
    public async Task TransitionAtomically_ConcurrentSameIdentityOnlyRecordsOneSingleApproval()
    {
        var repository = new InMemoryInvoiceRepository();
        var invoice = repository.Add(new Invoice { CustomerName = "Concurrency School", Amount = 50_000m, Status = InvoiceStatus.PendingApproval });
        var service = new ApprovalService(repository);
        var actor = new ApprovalActor("manager.one", ApprovalRole.Manager);
        var attempts = await Task.WhenAll(Enumerable.Range(0, 12).Select(_ => Task.Run(() =>
        {
            try { return service.Approve(invoice.Id, actor); }
            catch (InvalidOperationException) { return null; }
        })));
        Assert.Single(attempts, result => result is not null);
        var stored = repository.GetById(invoice.Id)!;
        Assert.Equal(InvoiceStatus.Approved, stored.Status);
        Assert.Single(stored.ApprovalHistory);
    }

    [Fact]
    public async Task TransitionAtomically_ConcurrentApprovalAndRejectionCannotOverwriteWinner()
    {
        var repository = new InMemoryInvoiceRepository();
        var invoice = repository.Add(new Invoice { CustomerName = "Concurrency School", Amount = 10_000m, Status = InvoiceStatus.PendingApproval });
        var service = new ApprovalService(repository);
        var approver = new ApprovalActor("manager.one", ApprovalRole.Manager);
        var rejector = new ApprovalActor("manager.two", ApprovalRole.Manager);

        var results = await Task.WhenAll(
            Task.Run(() => TryTransition(() => service.Approve(invoice.Id, approver))),
            Task.Run(() => TryTransition(() => service.Reject(invoice.Id, rejector, "Duplicate invoice"))));

        Assert.Single(results, result => result is not null);
        var stored = repository.GetById(invoice.Id)!;
        if (stored.Status == InvoiceStatus.Approved)
        {
            Assert.Equal(approver.Identity, stored.DecidedBy);
            Assert.Single(stored.ApprovalHistory);
            Assert.Null(stored.DecisionNote);
        }
        else
        {
            Assert.Equal(InvoiceStatus.Rejected, stored.Status);
            Assert.Equal(rejector.Identity, stored.DecidedBy);
            Assert.Empty(stored.ApprovalHistory);
            Assert.Equal("Duplicate invoice", stored.DecisionNote);
        }
    }

    private static Invoice? TryTransition(Func<Invoice> transition)
    {
        try { return transition(); }
        catch (InvalidOperationException) { return null; }
    }
}
