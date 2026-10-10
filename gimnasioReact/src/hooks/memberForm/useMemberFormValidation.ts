import { useForm, type Resolver, type FieldErrors } from 'react-hook-form';
import { memberFormSchema, type ModoFormulario } from '../../schemas/memberFormSchemas';
import type { FormData } from '../../types/MemberFormTypes';


const useMemberFormValidation = ({ modo, isEditing }: { modo: ModoFormulario; isEditing: boolean }) => { 
    const form = useForm<FormData>({
        // Custom resolver that reacts to modo/isEditing changes
        resolver: (async (values) => {
          const schema = memberFormSchema(modo, isEditing);
          const result = await schema.safeParseAsync(values);
          if (result.success) {
            return { values: result.data, errors: {} };
          }
          return { values: {}, errors: result.error.flatten().fieldErrors as FieldErrors<FormData> };
        }) as Resolver<FormData>,
        shouldUnregister: true,
        defaultValues: {
          miembro: '',
          membresia: '',
          multiplier: '1',
          dateInitial: '',
          nuevoName: '',
          nuevoLastname: '',
          nuevoPhone: '',
          nuevoAddress: '',
        },
      });

       const {
            register,
            handleSubmit,
            reset,
            watch,
            formState: { errors, isSubmitting, isDirty },
            setValue,
        } = form;

  return {
    register,
    handleSubmit,
    reset,
    watch,
    setValue,
    errors,
    isSubmitting,
    isDirty,
  };
};
export default useMemberFormValidation;