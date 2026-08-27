import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useMutation } from '@tanstack/react-query';
import { axiosPrivate } from '@/api/axios/axios.private';
import { toast } from 'react-hot-toast';

interface FormData {
  oldPassword: string;
  newPassword: string;
  confirmPassword: string;
}

interface PasswordChangeRequest {
  old_password: string;
  new_password: string;
  confirm_password: string;
}

export function PasswordChangeRequiredPage() {
  const navigate = useNavigate();
  const [formData, setFormData] = useState<FormData>({
    oldPassword: '',
    newPassword: '',
    confirmPassword: '',
  });
  const [errors, setErrors] = useState<Partial<FormData>>({});
  const [showPassword, setShowPassword] = useState(false);

  const { mutate: changePassword, isPending } = useMutation({
    mutationFn: (data: PasswordChangeRequest) =>
      axiosPrivate.post('/auth/password/change/', data),
    onSuccess: () => {
      toast.success('Contraseña actualizada. Inicia sesión con tu nueva contraseña');
      // Logout automático para forzar re-login con nueva password
      localStorage.removeItem('gym_access_token');
      navigate('/login', { replace: true });
    },
    onError: (error: { response?: { data?: Record<string, string[]> }; message?: string }) => {
      const response = error?.response?.data;
      if (response?.old_password) setErrors({ oldPassword: response.old_password[0] });
      if (response?.new_password) setErrors({ newPassword: response.new_password[0] });
      if (response?.confirm_password) setErrors({ confirmPassword: response.confirm_password[0] });
      if (response?.detail) toast.error(Array.isArray(response.detail) ? response.detail[0] : response.detail);
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setErrors({});
    
    if (formData.newPassword !== formData.confirmPassword) {
      setErrors({ confirmPassword: 'Las contraseñas no coinciden' });
      return;
    }
    if (formData.newPassword.length < 8) {
      setErrors({ newPassword: 'Mínimo 8 caracteres' });
      return;
    }
    
    changePassword({
      old_password: formData.oldPassword,
      new_password: formData.newPassword,
      confirm_password: formData.confirmPassword,
    });
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 px-4">
      <div className="w-full max-w-md bg-white rounded-xl shadow-sm border border-gray-200 p-8">
        <div className="text-center mb-8">
          <h1 className="text-2xl font-bold text-gray-900">Cambia tu contraseña temporal</h1>
          <p className="text-gray-600 mt-2">Por seguridad, debes establecer una nueva contraseña antes de continuar.</p>
        </div>
        
        <form onSubmit={handleSubmit} className="space-y-5">
          <div>
            <label htmlFor="oldPassword" className="block text-sm font-medium text-gray-700 mb-1">Contraseña temporal actual</label>
            <input
              id="oldPassword"
              type={showPassword ? 'text' : 'password'}
              value={formData.oldPassword}
              onChange={(e) => setFormData({ ...formData, oldPassword: e.target.value })}
              className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              placeholder="Contraseña temporal del email"
              required
              disabled={isPending}
            />
            {errors.oldPassword && <p className="text-red-600 text-sm mt-1">{errors.oldPassword}</p>}
          </div>
          
          <div>
            <label htmlFor="newPassword" className="block text-sm font-medium text-gray-700 mb-1">Nueva contraseña</label>
            <input
              id="newPassword"
              type={showPassword ? 'text' : 'password'}
              value={formData.newPassword}
              onChange={(e) => setFormData({ ...formData, newPassword: e.target.value })}
              className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              placeholder="Mínimo 8 caracteres"
              required
              disabled={isPending}
            />
            {errors.newPassword && <p className="text-red-600 text-sm mt-1">{errors.newPassword}</p>}
          </div>
          
          <div>
            <label htmlFor="confirmPassword" className="block text-sm font-medium text-gray-700 mb-1">Confirmar nueva contraseña</label>
            <input
              id="confirmPassword"
              type={showPassword ? 'text' : 'password'}
              value={formData.confirmPassword}
              onChange={(e) => setFormData({ ...formData, confirmPassword: e.target.value })}
              className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              placeholder="Repite la nueva contraseña"
              required
              disabled={isPending}
            />
            {errors.confirmPassword && <p className="text-red-600 text-sm mt-1">{errors.confirmPassword}</p>}
          </div>
          
          <label className="flex items-center gap-2 text-sm text-gray-600">
            <input id="showPassword" type="checkbox" checked={showPassword} onChange={(e) => setShowPassword(e.target.checked)} />
            Mostrar contraseñas
          </label>
          
          <button
            type="submit"
            disabled={isPending}
            className="w-full py-2.5 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {isPending ? 'Actualizando...' : 'Actualizar contraseña'}
          </button>
        </form>
      </div>
    </div>
  );
}