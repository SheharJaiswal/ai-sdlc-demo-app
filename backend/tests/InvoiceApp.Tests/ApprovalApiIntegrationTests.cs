using System.Net;
using System.Net.Http.Headers;
using System.Net.Http.Json;
using System.Text.Json;
using Microsoft.AspNetCore.Mvc.Testing;
using Xunit;

namespace InvoiceApp.Tests;

public class ApprovalApiIntegrationTests : IClassFixture<WebApplicationFactory<Program>>
{
    private readonly WebApplicationFactory<Program> _factory;

    public ApprovalApiIntegrationTests(WebApplicationFactory<Program> factory)
    {
        _factory = factory;
    }

    [Fact]
    public async Task Approve_UsesAuthenticatedManagerIdentityAndIgnoresClientSuppliedApproverFields()
    {
        using var client = _factory.CreateClient();
        var token = await Login(client, "demo.manager");
        client.DefaultRequestHeaders.Authorization = new AuthenticationHeaderValue("Bearer", token);
        var invoice = await CreateAndSubmit(client, 50_000m);

        var response = await client.PostAsJsonAsync($"/api/approvals/{invoice.Id}/approve", new { identity = "forged.director", role = "Director" });
        var document = JsonDocument.Parse(await response.Content.ReadAsStringAsync());

        Assert.Equal(HttpStatusCode.OK, response.StatusCode);
        Assert.Equal("demo.manager", document.RootElement.GetProperty("approvalHistory")[0].GetProperty("identity").GetString());
        Assert.Equal("Manager", document.RootElement.GetProperty("approvalHistory")[0].GetProperty("role").GetString());
    }

    [Fact]
    public async Task Approve_DeniesUnauthenticatedAndAdminRequests()
    {
        using var anonymous = _factory.CreateClient();
        Assert.Equal(HttpStatusCode.Unauthorized, (await anonymous.PostAsync("/api/approvals/INV-1001/approve", null)).StatusCode);

        using var admin = _factory.CreateClient();
        admin.DefaultRequestHeaders.Authorization = new AuthenticationHeaderValue("Bearer", await Login(admin, "demo.admin"));
        Assert.Equal(HttpStatusCode.Forbidden, (await admin.PostAsync("/api/approvals/INV-1001/approve", null)).StatusCode);
    }

    [Fact]
    public async Task Approve_RejectsManagerAboveLimitWithReasonAndPreservesInvoice()
    {
        using var client = _factory.CreateClient();
        client.DefaultRequestHeaders.Authorization = new AuthenticationHeaderValue("Bearer", await Login(client, "demo.manager"));
        var invoice = await CreateAndSubmit(client, 50_000.01m);
        using var beforeResponse = await client.GetAsync($"/api/invoices/{invoice.Id}");
        beforeResponse.EnsureSuccessStatusCode();
        using var before = JsonDocument.Parse(await beforeResponse.Content.ReadAsStringAsync());

        var rejected = await client.PostAsJsonAsync($"/api/approvals/{invoice.Id}/approve", new { });
        using var error = JsonDocument.Parse(await rejected.Content.ReadAsStringAsync());

        Assert.Equal(HttpStatusCode.Conflict, rejected.StatusCode);
        Assert.Contains("Director", error.RootElement.GetProperty("error").GetString());

        using var afterResponse = await client.GetAsync($"/api/invoices/{invoice.Id}");
        afterResponse.EnsureSuccessStatusCode();
        using var after = JsonDocument.Parse(await afterResponse.Content.ReadAsStringAsync());
        Assert.Equal(before.RootElement.GetRawText(), after.RootElement.GetRawText());
    }

    private static async Task<string> Login(HttpClient client, string username)
    {
        var response = await client.PostAsJsonAsync("/api/auth/login", new { username, password = "ChangeMe123!" });
        var document = JsonDocument.Parse(await response.Content.ReadAsStringAsync());
        return document.RootElement.GetProperty("token").GetString()!;
    }

    private static async Task<(string Id, decimal Amount)> CreateAndSubmit(HttpClient client, decimal amount)
    {
        var created = await client.PostAsJsonAsync("/api/invoices", new { customerName = "API policy test", amount });
        var document = JsonDocument.Parse(await created.Content.ReadAsStringAsync());
        var id = document.RootElement.GetProperty("id").GetString()!;
        var submitted = await client.PostAsync($"/api/invoices/{id}/submit", null);
        submitted.EnsureSuccessStatusCode();
        return (id, amount);
    }
}
