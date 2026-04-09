let toastFn: ((type: "success" | "error" | "warning" | "info", message: string) => void) | null = null;

export function registerToastFunction(fn: (type: "success" | "error" | "warning" | "info", message: string) => void) {
  toastFn = fn;
}

export function showToast(type: "success" | "error" | "warning" | "info", message: string) {
  if (toastFn) {
    toastFn(type, message);
  }
}

export function dismissToast(id: string) {
  // This would need to be connected to the ToastProvider
}
