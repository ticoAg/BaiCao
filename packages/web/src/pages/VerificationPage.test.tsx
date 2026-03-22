import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import VerificationPage from "./VerificationPage";
import { renderWithProviders } from "../test/render-with-providers";
import { verificationApi } from "../services/api";

describe("VerificationPage", () => {
  it("loads pending verifications and supports approving a record", async () => {
    const user = userEvent.setup();
    vi.spyOn(verificationApi, "list").mockResolvedValue({
      items: [
        {
          id: "verification-1",
          entity_type: "herb",
          entity_id: "herb-1",
          claimed_value: "人参可大补元气",
          status: "pending",
          applicant_id: "user-1",
          created_at: "2026-03-20T00:00:00",
        },
      ],
      total: 1,
    });
    vi.spyOn(verificationApi, "verify").mockResolvedValue({
      id: "verification-1",
      entity_type: "herb",
      entity_id: "herb-1",
      claimed_value: "人参可大补元气",
      status: "verified",
      applicant_id: "user-1",
      verifier_id: "expert-1",
      created_at: "2026-03-20T00:00:00",
      verified_at: "2026-03-20T08:00:00",
      verdict: "验证通过",
    });

    renderWithProviders(<VerificationPage />);

    expect(await screen.findByText("人参可大补元气")).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: /通过/ }));

    await waitFor(() =>
      expect(verificationApi.verify).toHaveBeenCalledWith(
        "verification-1",
        undefined,
        "verified",
        "验证通过",
      ),
    );
  });
});
