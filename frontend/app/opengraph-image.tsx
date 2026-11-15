import { ImageResponse } from "next/og";
import { siteUrl } from "../lib/site-url";

export const alt = "NetPay — M-Pesa Daraja API for business software";
export const size = { width: 1200, height: 630 };
export const contentType = "image/png";
export const dynamic = "force-static";

/** Keep the generated social card aligned with the global navy-and-teal brand. */
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
          backgroundColor: "#071e32",
          color: "#f7fbff",
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
              backgroundColor: "#70dfc8",
              color: "#06283b",
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
            M-Pesa Daraja API for business software
          </div>
          <div style={{ fontSize: "24px", color: "#c1d4de", maxWidth: "820px", lineHeight: 1.4 }}>
            Merchant-owned integrations. STK Push. Payment outcomes based on provider evidence.
          </div>
        </div>
        <div style={{ display: "flex", fontSize: "20px", color: "#c1d4de" }}>
          {new URL(siteUrl).host}
        </div>
      </div>
    ),
    { ...size },
  );
}
