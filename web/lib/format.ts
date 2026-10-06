export function seconds(ms: number | null | undefined, digits = 2): string {
  if (ms === null || ms === undefined) return "–";
  return `${(ms / 1000).toFixed(digits)} s`;
}

export function millis(ms: number | null | undefined): string {
  if (ms === null || ms === undefined) return "–";
  return `${Math.round(ms)}`;
}

export function firstName(name: string): string {
  return name.split(" ")[0] ?? name;
}
