using InvoiceApp.Domain;

namespace InvoiceApp.Api.Auth;

public record UserSession(string Username, string Role);

public static class UserSessionExtensions
{
    public static ApprovalActor ToApprovalActor(this UserSession session) => session.Role switch
    {
        "Manager" => new ApprovalActor(session.Username, ApprovalRole.Manager),
        "Director" => new ApprovalActor(session.Username, ApprovalRole.Director),
        _ => throw new InvalidOperationException("This account does not have an approval role.")
    };
}

public class DemoUser
{
    public string Username { get; set; } = string.Empty;
    public string Password { get; set; } = string.Empty;
    public string Role { get; set; } = string.Empty;
}

public class DemoUsersOptions
{
    public List<DemoUser> Users { get; set; } = new();
}
