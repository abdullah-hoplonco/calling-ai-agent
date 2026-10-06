// Audio levels for the meters, 0..1. Written many times a second and read in animation
// frames, so it lives outside React state to keep the page from re-rendering.

export const levels = { lead: 0, omar: 0 };
