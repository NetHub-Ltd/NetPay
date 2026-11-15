const configuredSiteUrl = process.env.NEXT_PUBLIC_SITE_URL?.trim();

export const siteUrl = (configuredSiteUrl || "https://netpay.nethub.co.ke").replace(/\/+$/, "");
