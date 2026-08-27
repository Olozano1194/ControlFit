import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { PasswordChangeRequiredPage } from '@/pages/auth/PasswordChangeRequiredPage';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { BrowserRouter } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import { axiosPrivate } from '@/api/axios/axios.private';

// Mock axiosPrivate
vi.mock('@/api/axios/axios.private', () => ({
  axiosPrivate: {
    post: vi.fn(),
  },
}));

// Mock react-hot-toast
vi.mock('react-hot-toast', async (importOriginal) => {
  const actual = await importOriginal();
  const original = actual as Record<string, unknown>;
  return {
    ...original,
    toast: {
      success: vi.fn(),
      error: vi.fn(),
    },
    Toaster: () => null, // Mock Toaster component
  };
});

// Mock localStorage
const localStorageMock = {
  getItem: vi.fn(),
  setItem: vi.fn(),
  removeItem: vi.fn(),
  clear: vi.fn(),
};
Object.defineProperty(window, 'localStorage', { value: localStorageMock });

// Test wrapper with providers
const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  });
  
  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        {children}
        <Toaster />
      </BrowserRouter>
    </QueryClientProvider>
  );
};

describe('PasswordChangeRequiredPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorageMock.removeItem.mockClear();
  });

  afterEach(() => {
    vi.resetAllMocks();
  });

  it('renders form with 3 password fields and submit button', () => {
    render(<PasswordChangeRequiredPage />, { wrapper: createWrapper() });
    
    expect(screen.getByLabelText('Contraseña temporal actual')).toBeInTheDocument();
    expect(screen.getByLabelText('Nueva contraseña')).toBeInTheDocument();
    expect(screen.getByLabelText('Confirmar nueva contraseña')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Actualizar contraseña' })).toBeInTheDocument();
    expect(screen.getByText('Cambia tu contraseña temporal')).toBeInTheDocument();
  });

  it('shows error when newPassword and confirmPassword do not match', async () => {
    render(<PasswordChangeRequiredPage />, { wrapper: createWrapper() });
    
    fireEvent.change(screen.getByLabelText('Contraseña temporal actual'), { 
      target: { value: 'TempPass123' } 
    });
    fireEvent.change(screen.getByLabelText('Nueva contraseña'), { 
      target: { value: 'NewPass456' } 
    });
    fireEvent.change(screen.getByLabelText('Confirmar nueva contraseña'), { 
      target: { value: 'DifferentPass789' } 
    });
    
    fireEvent.click(screen.getByRole('button', { name: 'Actualizar contraseña' }));
    
    await waitFor(() => {
      expect(screen.getByText('Las contraseñas no coinciden')).toBeInTheDocument();
    });
    
    // Should not call API
    expect(axiosPrivate.post).not.toHaveBeenCalled();
  });

  it('shows error when newPassword is less than 8 characters', async () => {
    render(<PasswordChangeRequiredPage />, { wrapper: createWrapper() });
    
    fireEvent.change(screen.getByLabelText('Contraseña temporal actual'), { 
      target: { value: 'TempPass123' } 
    });
    fireEvent.change(screen.getByLabelText('Nueva contraseña'), { 
      target: { value: 'Short1' } 
    });
    fireEvent.change(screen.getByLabelText('Confirmar nueva contraseña'), { 
      target: { value: 'Short1' } 
    });
    
    fireEvent.click(screen.getByRole('button', { name: 'Actualizar contraseña' }));
    
    await waitFor(() => {
      expect(screen.getByText(/Mínimo 8 caracteres/i)).toBeInTheDocument();
    });
    
    expect(axiosPrivate.post).not.toHaveBeenCalled();
  });

  it('submits successfully and redirects to login', async () => {
    // Mock successful API response
    (axiosPrivate.post as vi.Mock).mockResolvedValue({ data: { detail: 'Success' } });
    
    render(<PasswordChangeRequiredPage />, { wrapper: createWrapper() });
    
    fireEvent.change(screen.getByLabelText('Contraseña temporal actual'), { 
      target: { value: 'TempPass123' } 
    });
    fireEvent.change(screen.getByLabelText('Nueva contraseña'), { 
      target: { value: 'NewSecurePass456' } 
    });
    fireEvent.change(screen.getByLabelText('Confirmar nueva contraseña'), { 
      target: { value: 'NewSecurePass456' } 
    });
    
    fireEvent.click(screen.getByRole('button', { name: 'Actualizar contraseña' }));
    
    await waitFor(() => {
      expect(axiosPrivate.post).toHaveBeenCalledWith('/auth/password/change/', {
        old_password: 'TempPass123',
        new_password: 'NewSecurePass456',
        confirm_password: 'NewSecurePass456',
      });
    });
    
    await waitFor(() => {
      expect(localStorageMock.removeItem).toHaveBeenCalledWith('gym_access_token');
    });
  });

  it('handles 400 error with old_password field', async () => {
    const mockError = {
      response: {
        data: { old_password: ['La contraseña actual es incorrecta.'] }
      }
    };
    (axiosPrivate.post as vi.Mock).mockRejectedValue(mockError);
    
    render(<PasswordChangeRequiredPage />, { wrapper: createWrapper() });
    
    fireEvent.change(screen.getByLabelText('Contraseña temporal actual'), { 
      target: { value: 'WrongPass' } 
    });
    fireEvent.change(screen.getByLabelText('Nueva contraseña'), { 
      target: { value: 'NewPass456' } 
    });
    fireEvent.change(screen.getByLabelText('Confirmar nueva contraseña'), { 
      target: { value: 'NewPass456' } 
    });
    
    fireEvent.click(screen.getByRole('button', { name: 'Actualizar contraseña' }));
    
    await waitFor(() => {
      expect(screen.getByText('La contraseña actual es incorrecta.')).toBeInTheDocument();
    });
  });

  it('handles 400 error with new_password field', async () => {
    const mockError = {
      response: {
        data: { new_password: ['La contraseña debe tener al menos 8 caracteres.'] }
      }
    };
    (axiosPrivate.post as vi.Mock).mockRejectedValue(mockError);
    
    render(<PasswordChangeRequiredPage />, { wrapper: createWrapper() });
    
    fireEvent.change(screen.getByLabelText('Contraseña temporal actual'), { 
      target: { value: 'TempPass123' } 
    });
    fireEvent.change(screen.getByLabelText('Nueva contraseña'), { 
      target: { value: 'ValidPass123' } 
    });
    fireEvent.change(screen.getByLabelText('Confirmar nueva contraseña'), { 
      target: { value: 'ValidPass123' } 
    });
    
    fireEvent.click(screen.getByRole('button', { name: 'Actualizar contraseña' }));
    
    await waitFor(() => {
      expect(screen.getByText(/La contraseña debe tener al menos 8 caracteres/i)).toBeInTheDocument();
    });
  });

  it('handles 400 error with confirm_password field', async () => {
    const mockError = {
      response: {
        data: { confirm_password: ['Las contraseñas no coinciden.'] }
      }
    };
    (axiosPrivate.post as vi.Mock).mockRejectedValue(mockError);
    
    render(<PasswordChangeRequiredPage />, { wrapper: createWrapper() });
    
    fireEvent.change(screen.getByLabelText('Contraseña temporal actual'), { 
      target: { value: 'TempPass123' } 
    });
    fireEvent.change(screen.getByLabelText('Nueva contraseña'), { 
      target: { value: 'NewPass456' } 
    });
    fireEvent.change(screen.getByLabelText('Confirmar nueva contraseña'), { 
      target: { value: 'DifferentPass789' } 
    });
    
    fireEvent.click(screen.getByRole('button', { name: 'Actualizar contraseña' }));
    
    await waitFor(() => {
      expect(screen.getByText(/Las contraseñas no coinciden/i)).toBeInTheDocument();
    });
  });

  it('handles generic error with detail field', async () => {
    const mockError = {
      response: {
        data: { detail: ['Error del servidor'] }
      }
    };
    (axiosPrivate.post as vi.Mock).mockRejectedValue(mockError);
    
    // Mock toast.error
    const { toast } = await import('react-hot-toast');
    const errorSpy = vi.spyOn(toast, 'error');
    
    render(<PasswordChangeRequiredPage />, { wrapper: createWrapper() });
    
    fireEvent.change(screen.getByLabelText('Contraseña temporal actual'), { 
      target: { value: 'TempPass123' } 
    });
    fireEvent.change(screen.getByLabelText('Nueva contraseña'), { 
      target: { value: 'NewPass456' } 
    });
    fireEvent.change(screen.getByLabelText('Confirmar nueva contraseña'), { 
      target: { value: 'NewPass456' } 
    });
    
    fireEvent.click(screen.getByRole('button', { name: 'Actualizar contraseña' }));
    
    await waitFor(() => {
      expect(errorSpy).toHaveBeenCalledWith('Error del servidor');
    });
    
    errorSpy.mockRestore();
  });

  it('shows password when checkbox is checked', () => {
    render(<PasswordChangeRequiredPage />, { wrapper: createWrapper() });
    
    const oldPasswordInput = screen.getByLabelText('Contraseña temporal actual');
    const newPasswordInput = screen.getByLabelText('Nueva contraseña');
    const confirmPasswordInput = screen.getByLabelText('Confirmar nueva contraseña');
    
    expect(oldPasswordInput).toHaveAttribute('type', 'password');
    expect(newPasswordInput).toHaveAttribute('type', 'password');
    expect(confirmPasswordInput).toHaveAttribute('type', 'password');
    
    fireEvent.click(screen.getByLabelText('Mostrar contraseñas'));
    
    expect(oldPasswordInput).toHaveAttribute('type', 'text');
    expect(newPasswordInput).toHaveAttribute('type', 'text');
    expect(confirmPasswordInput).toHaveAttribute('type', 'text');
  });

  it('disables form when mutation is pending', async () => {
    let resolvePromise: (value: unknown) => void;
    const promise = new Promise<unknown>((resolve) => {
      resolvePromise = resolve;
    });
    (axiosPrivate.post as vi.Mock).mockReturnValue(promise);
    
    render(<PasswordChangeRequiredPage />, { wrapper: createWrapper() });
    
    fireEvent.change(screen.getByLabelText('Contraseña temporal actual'), { 
      target: { value: 'TempPass123' } 
    });
    fireEvent.change(screen.getByLabelText('Nueva contraseña'), { 
      target: { value: 'NewPass456' } 
    });
    fireEvent.change(screen.getByLabelText('Confirmar nueva contraseña'), { 
      target: { value: 'NewPass456' } 
    });
    
    const submitButton = screen.getByRole('button', { name: 'Actualizar contraseña' });
    fireEvent.click(submitButton);
    
    // Form should be disabled after click (while pending)
    await waitFor(() => {
      expect(screen.getByLabelText('Contraseña temporal actual')).toBeDisabled();
      expect(screen.getByLabelText('Nueva contraseña')).toBeDisabled();
      expect(screen.getByLabelText('Confirmar nueva contraseña')).toBeDisabled();
      expect(screen.getByRole('button', { name: 'Actualizando...' })).toBeDisabled();
    });
    
    resolvePromise!({ data: { detail: 'Success' } });
    await promise;
  });
});