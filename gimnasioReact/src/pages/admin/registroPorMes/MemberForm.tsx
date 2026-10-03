import { useMemberForm } from '@/hooks/useMemberForm';
import BreadCrumbsSection from '@/components/form/section/BreadCrumbsSection';
import { Button } from '@/components/ui';
import { ModeToggle } from '@/components/memberForm/ModeToggle';
import { ExistingMemberSelect } from '@/components/memberForm/ExistingMemberSelect';
import { NewMemberFields } from '@/components/memberForm/NewMemberFields';
import { MembershipSelect } from '@/components/memberForm/MembershipSelect';
import { DateInitialField } from '@/components/memberForm/DateInitialField';
import { MultiplierDiscountFields } from '@/components/memberForm/MultiplierDiscountFields';
import { PaymentSummary } from '@/components/memberForm/PaymentSummary';
import { SuspenderMembresiaModal } from '@/components/memberForm/operations/SuspenderMembresiaModal';
import { formatDateForDisplay, parseApiDateToInput } from '@/utils/dateUtils';
import type { SelectedMembresia } from '@/types/MemberFormTypes';
import { useState } from 'react';

export const MemberForm = () => {
  const {
    // Form
    register,
    handleSubmit,
    errors,
    isSubmitting,
    watch,
    // Mode
    modo,
    setModo,
    // Data
    miembros,
    membresias,
    selectedMembresia,
    asignacion,
    // Pricing
    multiplier,
    discountPercent,
    multiplierOptions,
    showMultiplier,
    estimatedPrice,
    totalDays,
    estimatedDateFinal,
    // Editability
    canEditAssignment,
    // Handlers
    handleMemberShipsChange,
    handleMultiplierChange,
    setDiscountPercent,
    // Submission
    onSubmit,
    isEditing,
  } = useMemberForm();

  const [showSuspendModal, setShowSuspendModal] = useState(false);

  const showMemberSelection = !isEditing;
  const dateInitial = watch('dateInitial');
  const membresiaValue = watch('membresia');

  const handleSuspendSuccess = () => {
    // Refresh the page to get updated assignment data
    window.location.reload();
  };

  // When editing: assignment fields editable only when estado_pago === 'pending'
  // Personal fields always editable when editing
  const membershipReadOnly = isSubmitting || !canEditAssignment;
  const dateInitialReadOnly = isSubmitting || !canEditAssignment;
  const pricingDisabled = isSubmitting || !canEditAssignment;

  // For PaymentSummary when editing, use asignacion data directly (most reliable)
  // parseApiDateToInput handles both DD/MM/YYYY and YYYY-MM-DD from API
  // membresia_details only has {id, name, price} - adapt to SelectedMembresia shape
  const paymentSummaryMembresia: SelectedMembresia | null = isEditing && asignacion?.membresia_details
    ? {
        id: asignacion.membresia_details.id,
        name: asignacion.membresia_details.name,
        price: asignacion.membresia_details.price,
        duration: selectedMembresia?.duration ?? 0,
        max_multiplier: selectedMembresia?.max_multiplier ?? 1,
        gimnasio: selectedMembresia?.gimnasio ?? 0,
      }
    : selectedMembresia;
  const paymentSummaryDateInitial = isEditing && asignacion?.dateInitial
    ? parseApiDateToInput(asignacion.dateInitial)
    : dateInitial;
  const paymentSummaryDateFinal = isEditing && asignacion?.dateFinal
    ? formatDateForDisplay(parseApiDateToInput(asignacion.dateFinal))
    : estimatedDateFinal;

  return (
    <main className="max-w-7xl mx-auto p-6 lg:p-10">
      <BreadCrumbsSection
        isEditing={isEditing}
        title="Asignar Membresías"
        description="Asocie membresías a los atletas registrados en el sistema"
        entityName="esta asignación"
      />
      <form onSubmit={handleSubmit((data) => {
        onSubmit(data);
      })} className="space-y-8">
        {showMemberSelection && <ModeToggle modo={modo} onChange={setModo} disabled={isSubmitting} />}

        {showMemberSelection ? (
          modo === 'existente' ? (
            <ExistingMemberSelect
              register={register}
              errors={errors}
              miembros={miembros}
              disabled={isSubmitting}
            />
          ) : (
            <NewMemberFields register={register} errors={errors} disabled={isSubmitting} />
          )
        ) : (
          // Editing: show same fields as "Nuevo miembro" - all editable, pre-filled via form reset()
          <NewMemberFields register={register} errors={errors} disabled={isSubmitting} />
        )}

        <section className="gap-y-10 gap-x-8 grid grid-cols-1 md:grid-cols-2">
          <MembershipSelect
            register={register}
            errors={errors}
            membresias={membresias}
            onChange={handleMemberShipsChange}
            disabled={isSubmitting}
            readOnly={membershipReadOnly}
            value={membresiaValue}
          />
          <DateInitialField
            register={register}
            errors={errors}
            disabled={isSubmitting}
            readOnly={dateInitialReadOnly}
          />
        </section>

        {showMultiplier && (
          <MultiplierDiscountFields
            multiplier={multiplier}
            discountPercent={discountPercent}
            multiplierOptions={multiplierOptions}
            onMultiplierChange={handleMultiplierChange}
            onDiscountChange={setDiscountPercent}
            disabled={pricingDisabled}
          />
        )}

        <PaymentSummary
          selectedMembresia={paymentSummaryMembresia}
          multiplier={multiplier}
          discountPercent={discountPercent}
          estimatedPrice={estimatedPrice}
          totalDays={totalDays}
          estimatedDateFinal={paymentSummaryDateFinal}
          dateInitial={paymentSummaryDateInitial}
          disabled={isSubmitting}
        />

        {/* Operation action buttons */}
        {!canEditAssignment && isEditing && (
          <section className="space-y-4 p-4 bg-amber-50 border border-amber-200 rounded-lg">
            <h3 className="text-sm font-medium text-amber-800">
              Esta membresía está en estado <strong>{asignacion?.estado_pago === 'paid' ? 'Pagada' : 'No pendiente'}</strong>.
              Los campos de plan y precios son de solo lectura. Use las operaciones de negocio:
            </h3>
            <div className="flex flex-wrap gap-2">
              <Button
                type="button"
                variant="secondary"
                onClick={() => setShowSuspendModal(true)}
                disabled={isSubmitting}
              >
                Suspender
              </Button>
              <Button type="button" variant="secondary" disabled>
                Cambiar plan
              </Button>
              <Button type="button" variant="secondary" disabled>
                Registrar devolución
              </Button>
              <Button type="button" variant="secondary" disabled>
                Renovar
              </Button>
            </div>
          </section>
        )}

        <div className="w-full flex items-center justify-center">
          <Button type="submit" disabled={isSubmitting}>
            {isSubmitting ? 'Guardando...' : isEditing ? 'Actualizar' : 'Registrar'}
          </Button>
        </div>
      </form>

      {/* Suspender Modal */}
      <SuspenderMembresiaModal
        isOpen={showSuspendModal}
        onClose={() => setShowSuspendModal(false)}
        onSuccess={handleSuspendSuccess}
        asignacion={asignacion}
      />
    </main>
  );
};
export default MemberForm;