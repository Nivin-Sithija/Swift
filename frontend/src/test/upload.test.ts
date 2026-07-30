import { validateImageFile } from "../components/tickets/ImageUploader";
describe("image validation", () => {
  it("rejects unsupported file formats", () => {
    expect(
      validateImageFile(
        new File(["x"], "proof.pdf", { type: "application/pdf" }),
      ).error,
    ).toMatch(/PNG/);
  });
  it("rejects files over 5 MB", () => {
    expect(
      validateImageFile(
        new File([new Uint8Array(5 * 1024 * 1024 + 1)], "large.jpg", {
          type: "image/jpeg",
        }),
      ).error,
    ).toMatch(/5 MB/);
  });
  it("accepts valid jpeg evidence", () => {
    expect(
      validateImageFile(new File(["safe"], "proof.jpg", { type: "image/jpeg" }))
        .file?.name,
    ).toBe("proof.jpg");
  });
});
