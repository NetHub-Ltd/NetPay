/** Controlled list for business category — keep in sync with product copy. */
export const BUSINESS_CATEGORIES = [
  { value: 'retail', label: 'Retail' },
  { value: 'services', label: 'Services' },
  { value: 'fintech', label: 'Fintech' },
  { value: 'education', label: 'Education' },
  { value: 'healthcare', label: 'Healthcare' },
  { value: 'hospitality', label: 'Hospitality' },
  { value: 'logistics', label: 'Logistics' },
  { value: 'other', label: 'Other' },
] as const

export type BusinessCategory = (typeof BUSINESS_CATEGORIES)[number]['value']
