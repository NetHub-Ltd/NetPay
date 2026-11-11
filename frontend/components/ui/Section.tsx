import type { ReactNode } from "react";
import { Container } from "./Container";

export function Section({
  id,
  children,
  className = "",
  containerClassName = "",
}: {
  id?: string;
  children: ReactNode;
  className?: string;
  containerClassName?: string;
}) {
  return (
    <section id={id} className={`np-section ${className}`}>
      <Container className={containerClassName}>{children}</Container>
    </section>
  );
}
