import { ImageResponse } from "next/og";

export const alt = "NetPay — M-Pesa payments infrastructure";
export const size = { width: 1200, height: 630 };
export const contentType = "image/png";

export default function OpenGraphImage() {
  return new ImageResponse(
    (
      <div
        style={{
          display: "flex",
          flexDirection: "column",
          justifyContent: "space-between",
          width: "100%",
          height: "100%",
          padding: "68px",
          backgroundColor: "#101b2d",
          color: "#f8fafc",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: "18px" }}>
          <div
            style={{
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              width: "62px",
              height: "62px",
              borderRadius: "16px",
              backgroundColor: "#20b89a",
              color: "#101b2d",
              fontSize: "38px",
              fontWeight: 800,
            }}
          >
            N
          </div>
          <div style={{ fontSize: "34px", fontWeight: 700 }}>NetPay</div>
        </div>
        <div style={{ display: "flex", flexDirection: "column", gap: "20px" }}>
          <div style={{ fontSize: "22px", fontWeight: 700, color: "#55d6b9", letterSpacing: "3px" }}>
            M-PESA PAYMENT INFRASTRUCTURE
          </div>
          <div style={{ fontSize: "64px", lineHeight: 1.08, fontWeight: 700, letterSpacing: "-2px" }}>
            Build on payment states, not assumptions.
          </div>
          <div style={{ fontSize: "27px", color: "#cbd5e1" }}>
            A consistent API for merchant-owned Daraja integrations.
          </div>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: "12px", fontSize: "20px", color: "#94a3b8" }}>
          <div style={{ width: "9px", height: "9px", borderRadius: "99px", backgroundColor: "#20b89a" }} />
          pay.nethub.co.ke
        </div>
      </div>
    ),
    size,
  );
}
