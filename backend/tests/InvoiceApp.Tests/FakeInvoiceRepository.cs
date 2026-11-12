using InvoiceApp.Domain;

namespace InvoiceApp.Tests;

internal class FakeInvoiceRepository : IInvoiceRepository
{
    private readonly List<Invoice> _invoices = new();

    public FakeInvoiceRepository(params Invoice[] seed) => _invoices.AddRange(seed);

    public IReadOnlyList<Invoice> GetAll() => _invoices.Select(invoice => invoice.Copy()).ToList();
    public Invoice? GetById(string id) => _invoices.FirstOrDefault(i => i.Id == id)?.Copy();
    public IReadOnlyList<Invoice> GetByIds(IEnumerable<string> ids) => _invoices.Where(i => ids.Contains(i.Id)).Select(invoice => invoice.Copy()).ToList();
    public Invoice Add(Invoice invoice) { _invoices.Add(invoice.Copy()); return invoice.Copy(); }
    public void Update(Invoice invoice) { }
    public Invoice TransitionAtomically(string id, Func<Invoice, Invoice> transition)
    {
        var index = _invoices.FindIndex(invoice => invoice.Id == id);
        if (index < 0) throw new KeyNotFoundException($"Invoice {id} was not found.");
        var updated = transition(_invoices[index].Copy());
        _invoices[index] = updated.Copy();
        return updated.Copy();
    }
    public bool Remove(string id) => _invoices.RemoveAll(i => i.Id == id) > 0;
}
