/**
 * Classnames utility helper to merge Tailwind CSS classes cleanly.
 */
export function cn(...inputs: (string | undefined | null | false)[]): string {
  return inputs.filter(Boolean).join(" ");
}
