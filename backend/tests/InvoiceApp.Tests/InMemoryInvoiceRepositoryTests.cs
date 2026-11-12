using InvoiceApp.Api;
using InvoiceApp.Domain;
using Xunit;

namespace InvoiceApp.Tests;

public class InMemoryInvoiceRepositoryTests
{
    [Fact]
    public async Task TransitionAtomically_ConcurrentSecondApprovalOnlyCompletesOnce()
    {
        var repository = new InMemoryInvoiceRepository();
        var invoice = repository.Add(new Invoice { CustomerName = "Concurrency School", Amount = 500_000.01m, Status = InvoiceStatus.PendingApproval });
        var service = new ApprovalService(repository);
        service.Approve(invoice.Id, new ApprovalActor("manager.one", ApprovalRole.Manager));

        var attempts = await Task.WhenAll(Enumerable.Range(0, 12).Select(index => Task.Run(() =>
        {
            try { return service.Approve(invoice.Id, new ApprovalActor($"director.{index}", ApprovalRole.Director)); }
            catch (InvalidOperationException) { return null; }
        })));

        var completed = Assert.Single(attempts, result => result is not null)!;
        var stored = repository.GetById(invoice.Id)!;
        Assert.Equal(InvoiceStatus.Approved, stored.Status);
        Assert.Equal(completed.ApprovalHistory, stored.ApprovalHistory);
        Assert.Equal("manager.one", stored.ApprovalHistory[0].Identity);
        Assert.Equal(ApprovalRole.Manager, stored.ApprovalHistory[0].Role);
        Assert.StartsWith("director.", stored.ApprovalHistory[1].Identity);
        Assert.Equal(ApprovalRole.Director, stored.ApprovalHistory[1].Role);
    }

    [Fact]
    public async Task TransitionAtomically_ConcurrentSameIdentityOnlyRecordsOneValidApproval()
    {
        var repository = new InMemoryInvoiceRepository();
        var invoice = repository.Add(new Invoice { CustomerName = "Concurrency School", Amount = 500_000.01m, Status = InvoiceStatus.PendingApproval });
        var service = new ApprovalService(repository);
        var actor = new ApprovalActor("manager.one", ApprovalRole.Manager);
        var attempts = await Task.WhenAll(Enumerable.Range(0, 12).Select(_ => Task.Run(() =>
        {
            try { return service.Approve(invoice.Id, actor); }
            catch (InvalidOperationException) { return null; }
        })));
        Assert.Single(attempts, result => result is not null);
        var stored = repository.GetById(invoice.Id)!;
        Assert.Equal(InvoiceStatus.PendingApproval, stored.Status);
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
