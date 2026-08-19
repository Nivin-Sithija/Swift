import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { DataTable } from "../../components/ui/DataTable";

interface Row {
  id: string;
  subject: string;
}

const rows: Row[] = [
  { id: "TCK-1", subject: "Card blocked" },
  { id: "TCK-2", subject: "Refund delay" },
];

describe("DataTable", () => {
  it("renders a header row and one row per item", () => {
    render(
      <DataTable<Row>
        columns={[
          { key: "id", label: "Ticket" },
          { key: "subject", label: "Subject" },
        ]}
        rows={rows}
        rowKey={(row) => row.id}
      />,
    );
    expect(screen.getByText("Ticket")).toBeInTheDocument();
    expect(screen.getByText("Card blocked")).toBeInTheDocument();
    expect(screen.getByText("Refund delay")).toBeInTheDocument();
  });

  it("calls onRowClick with the clicked row", async () => {
    const onRowClick = vi.fn();
    render(
      <DataTable<Row>
        columns={[{ key: "id", label: "Ticket" }]}
        rows={rows}
        rowKey={(row) => row.id}
        onRowClick={onRowClick}
      />,
    );
    await userEvent.click(screen.getByText("TCK-2"));
    expect(onRowClick).toHaveBeenCalledWith(rows[1]);
  });

  it("shows animated placeholder rows until table data is loaded", () => {
    const { container } = render(
      <DataTable<Row>
        columns={[
          { key: "id", label: "Ticket" },
          { key: "subject", label: "Subject" },
        ]}
        rows={[]}
        rowKey={(row) => row.id}
        loading
        loadingRows={4}
      />,
    );

    expect(screen.getByRole("status")).toHaveTextContent(/loading table data/i);
    expect(container.querySelectorAll(".table-cell-skeleton")).toHaveLength(8);
    expect(screen.queryByText("Card blocked")).not.toBeInTheDocument();
  });
});
