import { ImageResponse } from "next/og";

export const alt = "NetPay — M-Pesa payment API for business software";
export const size = { width: 1200, height: 630 };
export const contentType = "image/png";
export const dynamic = "force-static";

/** Ledger theme (Theme.md): indigo chrome + sky accent */
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
          backgroundColor: "#1e1b4b",
          color: "#f5f3ff",
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
              backgroundColor: "#3b82f6",
              color: "#ffffff",
              fontSize: "38px",
              fontWeight: 800,
            }}
          >
            N
          </div>
          <div style={{ fontSize: "34px", fontWeight: 700 }}>NetPay</div>
        </div>
        <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
          <div
            style={{
              fontSize: "52px",
              fontWeight: 800,
              lineHeight: 1.15,
              letterSpacing: "-0.03em",
              maxWidth: "900px",
            }}
          >
            M-Pesa payment API for business software
          </div>
          <div style={{ fontSize: "24px", color: "#c4b5fd", maxWidth: "820px", lineHeight: 1.4 }}>
            Merchant-owned Daraja integrations, STK Push, and payment events grounded in provider
            results.
          </div>
        </div>
        <div style={{ display: "flex", fontSize: "20px", color: "#c4b5fd" }}>
          pay.nethub.co.ke
        </div>
      </div>
    ),
    { ...size },
  );
}
