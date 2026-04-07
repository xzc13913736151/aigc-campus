import React from "react";
import { render, screen } from "@testing-library/react";

import { Button } from "@/components/ui/button";


describe("Button", () => {
  it("renders its children", () => {
    render(<Button>Publish</Button>);
    expect(screen.getByRole("button", { name: "Publish" })).toBeInTheDocument();
  });
});
