// The temporary project name lives in exactly one place on the frontend: this
// constant. Renaming the product means editing this and apps/api/app/core/config.py.
export const APP_NAME = "Kadro";

export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api/v1";
