import { render,screen } from "@testing-library/react";
import { ProcessingStepper } from "../components/tickets/TicketComponents";
it("marks completed, active and waiting processing steps",()=>{render(<ProcessingStepper current={1} steps={["Validate","Preserve","Classify"]}/>);expect(screen.getByText("Complete")).toBeInTheDocument();expect(screen.getByText("In progress")).toBeInTheDocument();expect(screen.getByText("Waiting")).toBeInTheDocument()});
