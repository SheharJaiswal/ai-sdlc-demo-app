using InvoiceApp.Domain;
using Xunit;

namespace InvoiceApp.Tests;

public class ApprovalServiceTests
{
    private static readonly ApprovalActor Manager = new("manager.one", ApprovalRole.Manager);
    private static readonly ApprovalActor Director = new("director.one", ApprovalRole.Director);

    private static Invoice InvoiceWith(string id, decimal amount, InvoiceStatus status = InvoiceStatus.PendingApproval) =>
        new() { Id = id, CustomerName = "Test School", Amount = amount, Status = status };

    private static ApprovalService ServiceFor(params Invoice[] invoices) => new(new FakeInvoiceRepository(invoices));

    [Fact]
    public void Submit_MovesDraftToPendingApproval() =>
        Assert.Equal(InvoiceStatus.PendingApproval, ServiceFor(InvoiceWith("INV-1", 100m, InvoiceStatus.Draft)).Submit("INV-1").Status);

    [Fact]
    public void Approve_ManagerApprovesAtLowerInclusiveBoundary()
    {
        var result = ServiceFor(InvoiceWith("INV-1", 50_000m)).Approve("INV-1", Manager);
        Assert.Equal(InvoiceStatus.Approved, result.Status);
        var approval = Assert.Single(result.ApprovalHistory);
        Assert.Equal(Manager.Identity, approval.Identity);
        Assert.Equal(ApprovalRole.Manager, approval.Role);
        Assert.NotEqual(default, approval.ApprovedAt);
    }

    [Fact]
    public void Approve_ManagerIsRejectedImmediatelyAboveLowerBoundaryWithoutMutation()
    {
        var repository = new FakeInvoiceRepository(InvoiceWith("INV-1", 50_000.01m));
        var service = new ApprovalService(repository);
        var before = repository.GetById("INV-1")!;
        var error = Assert.Throws<InvalidOperationException>(() => service.Approve("INV-1", Manager));
        var after = repository.GetById("INV-1")!;
        Assert.Contains("Director", error.Message);
        AssertInvoiceUnchanged(before, after);
    }

    [Theory]
    [InlineData(50_000.01)]
    [InlineData(500_000)]
    public void Approve_DirectorApprovesDirectorOnlyRangeAndUpperInclusiveBoundary(decimal amount)
    {
        var result = ServiceFor(InvoiceWith("INV-1", amount)).Approve("INV-1", Director);
        Assert.Equal(InvoiceStatus.Approved, result.Status);
        Assert.Single(result.ApprovalHistory);
    }

    [Fact]
    public void Approve_RejectsAmountAboveUpperBoundaryWithoutMutation()
    {
        var repository = new FakeInvoiceRepository(InvoiceWith("INV-1", 500_000.01m));
        var service = new ApprovalService(repository);
        var before = repository.GetById("INV-1")!;
        var error = Assert.Throws<InvalidOperationException>(() => service.Approve("INV-1", Director));
        var after = repository.GetById("INV-1")!;
        Assert.Contains("high-value approval workflow", error.Message);
        AssertInvoiceUnchanged(before, after);
    }

    [Fact]
    public void Reject_RecordsReasonAndApprover()
    {
        var result = ServiceFor(InvoiceWith("INV-1", 100m)).Reject("INV-1", Manager, "Duplicate invoice");
        Assert.Equal(InvoiceStatus.Rejected, result.Status);
        Assert.Equal(Manager.Identity, result.DecidedBy);
        Assert.Equal("Duplicate invoice", result.DecisionNote);
    }

    private static void AssertInvoiceUnchanged(Invoice before, Invoice after)
    {
        Assert.Equal(before.Id, after.Id);
        Assert.Equal(before.CustomerName, after.CustomerName);
        Assert.Equal(before.Amount, after.Amount);
        Assert.Equal(before.Status, after.Status);
        Assert.Equal(before.CreatedAt, after.CreatedAt);
        Assert.Equal(before.DecidedBy, after.DecidedBy);
        Assert.Equal(before.DecidedAt, after.DecidedAt);
        Assert.Equal(before.DecisionNote, after.DecisionNote);
        Assert.Equal(before.ApprovalHistory, after.ApprovalHistory);
    }
}
