"use client";

import { useState, useEffect, useCallback } from "react";

type ConfirmModalProps = {
  isOpen: boolean;
  title: string;
  message: string;
  confirmText?: string;
  cancelText?: string;
  confirmStyle?: "danger" | "primary";
  onConfirm: () => void;
  onCancel: () => void;
};

export function ConfirmModal({
  isOpen,
  title,
  message,
  confirmText = "Confirm",
  cancelText = "Cancel",
  confirmStyle = "primary",
  onConfirm,
  onCancel,
}: ConfirmModalProps) {
  if (!isOpen) return null;

  return (
    <div className="confirm-overlay" onClick={(e) => e.target === e.currentTarget && onCancel()}>
      <div className="confirm-modal">
        <h3>{title}</h3>
        <p>{message}</p>
        <div className="confirm-actions">
          <button className="confirm-btn cancel" onClick={onCancel}>
            {cancelText}
          </button>
          <button
            className={`confirm-btn ${confirmStyle}`}
            onClick={() => {
              onConfirm();
              onCancel();
            }}
          >
            {confirmText}
          </button>
        </div>
      </div>
    </div>
  );
}

type AlertModalProps = {
  isOpen: boolean;
  title: string;
  message: string;
  buttonText?: string;
  onClose: () => void;
};

export function AlertModal({
  isOpen,
  title,
  message,
  buttonText = "OK",
  onClose,
}: AlertModalProps) {
  if (!isOpen) return null;

  return (
    <div className="confirm-overlay" onClick={(e) => e.target === e.currentTarget && onClose()}>
      <div className="confirm-modal">
        <h3>{title}</h3>
        <p>{message}</p>
        <div className="confirm-actions">
          <button className="confirm-btn primary" onClick={onClose}>
            {buttonText}
          </button>
        </div>
      </div>
    </div>
  );
}

type GlobalModalState = {
  type: "confirm" | "alert" | null;
  isOpen: boolean;
  title: string;
  message: string;
  confirmText?: string;
  cancelText?: string;
  confirmStyle?: "danger" | "primary";
  onConfirm?: () => void;
  onCancel?: () => void;
};

export function showConfirm(
  title: string,
  message: string,
  options?: {
    confirmText?: string;
    cancelText?: string;
    confirmStyle?: "danger" | "primary";
  }
): Promise<boolean> {
  return new Promise((resolve) => {
    window.dispatchEvent(
      new CustomEvent("show-confirm", {
        detail: {
          title,
          message,
          confirmText: options?.confirmText || "Confirm",
          cancelText: options?.cancelText || "Cancel",
          confirmStyle: options?.confirmStyle || "primary",
          onConfirm: () => resolve(true),
          onCancel: () => resolve(false),
        },
      })
    );
  });
}

export function showAlert(
  title: string,
  message: string,
  buttonText: string = "OK"
): Promise<void> {
  return new Promise((resolve) => {
    window.dispatchEvent(
      new CustomEvent("show-alert", {
        detail: {
          title,
          message,
          buttonText,
          onClose: () => resolve(),
        },
      })
    );
  });
}

export function GlobalModalProvider({ children }: { children: React.ReactNode }) {
  const [modalState, setModalState] = useState<GlobalModalState>({
    type: null,
    isOpen: false,
    title: "",
    message: "",
  });

  useEffect(() => {
    const handleConfirm = (e: Event) => {
      const detail = (e as CustomEvent).detail;
      setModalState({
        type: "confirm",
        isOpen: true,
        title: detail.title,
        message: detail.message,
        confirmText: detail.confirmText,
        cancelText: detail.cancelText,
        confirmStyle: detail.confirmStyle,
        onConfirm: detail.onConfirm,
        onCancel: detail.onCancel,
      });
    };

    const handleAlert = (e: Event) => {
      const detail = (e as CustomEvent).detail;
      setModalState({
        type: "alert",
        isOpen: true,
        title: detail.title,
        message: detail.message,
        onConfirm: detail.onClose,
      });
    };

    window.addEventListener("show-confirm", handleConfirm);
    window.addEventListener("show-alert", handleAlert);

    return () => {
      window.removeEventListener("show-confirm", handleConfirm);
      window.removeEventListener("show-alert", handleAlert);
    };
  }, []);

  const handleClose = useCallback(() => {
    if (modalState.type === "confirm" && modalState.onCancel) {
      modalState.onCancel();
    }
    setModalState({ ...modalState, isOpen: false });
  }, [modalState]);

  const handleConfirm = useCallback(() => {
    if (modalState.onConfirm) {
      modalState.onConfirm();
    }
    setModalState({ ...modalState, isOpen: false });
  }, [modalState]);

  return (
    <>
      {children}
      {modalState.isOpen && modalState.type === "confirm" && (
        <ConfirmModal
          isOpen={true}
          title={modalState.title}
          message={modalState.message}
          confirmText={modalState.confirmText}
          cancelText={modalState.cancelText}
          confirmStyle={modalState.confirmStyle}
          onConfirm={handleConfirm}
          onCancel={handleClose}
        />
      )}
      {modalState.isOpen && modalState.type === "alert" && (
        <AlertModal
          isOpen={true}
          title={modalState.title}
          message={modalState.message}
          onClose={handleClose}
        />
      )}
    </>
  );
}
