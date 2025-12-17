// Toast Aprimorado com Ações
import { toast } from "sonner";

interface ToastWithActionOptions {
  message: string;
  actionLabel?: string;
  onAction?: () => void;
  duration?: number;
}

// Toast de sucesso com ação
export const successWithAction = ({
  message,
  actionLabel = "Desfazer",
  onAction,
  duration = 5000,
}: ToastWithActionOptions) => {
  toast.success(message, {
    duration,
    action: onAction ? {
      label: actionLabel,
      onClick: onAction,
    } : undefined,
  });
};

// Toast de erro com retry
export const errorWithRetry = ({
  message,
  actionLabel = "Tentar novamente",
  onAction,
  duration = 8000,
}: ToastWithActionOptions) => {
  toast.error(message, {
    duration,
    action: onAction ? {
      label: actionLabel,
      onClick: onAction,
    } : undefined,
  });
};

// Toast de info com ação
export const infoWithAction = ({
  message,
  actionLabel = "Ver detalhes",
  onAction,
  duration = 5000,
}: ToastWithActionOptions) => {
  toast.info(message, {
    duration,
    action: onAction ? {
      label: actionLabel,
      onClick: onAction,
    } : undefined,
  });
};

// Toast de loading que pode ser atualizado
export const loadingToast = (message: string) => {
  return toast.loading(message);
};

export const updateToast = (
  toastId: string | number,
  message: string,
  type: "success" | "error" | "info" = "success"
) => {
  toast.dismiss(toastId);
  if (type === "success") toast.success(message);
  else if (type === "error") toast.error(message);
  else toast.info(message);
};

// Toast com progresso (simulado)
export const progressToast = async (
  message: string,
  operation: () => Promise<void>,
  successMessage: string,
  errorMessage: string
) => {
  const toastId = toast.loading(message);
  
  try {
    await operation();
    toast.dismiss(toastId);
    toast.success(successMessage);
  } catch (error) {
    toast.dismiss(toastId);
    toast.error(errorMessage);
    throw error;
  }
};

// Toast com countdown (para ações destrutivas)
export const confirmationToast = (
  message: string,
  onConfirm: () => void,
  countdown = 5
) => {
  let remaining = countdown;
  
  const toastId = toast(message, {
    duration: countdown * 1000,
    action: {
      label: `Confirmar (${remaining}s)`,
      onClick: onConfirm,
    },
  });

  const interval = setInterval(() => {
    remaining--;
    if (remaining <= 0) {
      clearInterval(interval);
    }
  }, 1000);

  return toastId;
};
