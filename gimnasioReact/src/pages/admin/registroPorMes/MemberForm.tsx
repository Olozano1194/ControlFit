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
import { formatDateForDisplay, parseApiDateToInput } from '@/utils/dateUtils';

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
    // Editing values (from asignacion directly)
    isMembershipActive,
    // Handlers
    handleMemberShipsChange,
    handleMultiplierChange,
    setDiscountPercent,
    // Submission
    onSubmit,
    isEditing,
  } = useMemberForm();

  const showMemberSelection = !isEditing;
  const dateInitial = watch('dateInitial');
  const membresiaValue = watch('membresia');

  // When editing: if membership is active -> allow editing membership, date, multiplier, discount
  // If expired -> only allow editing member data (name, phone, etc.)
  // Use readOnly (not disabled) so values still submit and pass Zod validation
  const canEditMembership = isEditing ? isMembershipActive : true;
  const membershipReadOnly = isSubmitting || !canEditMembership;
  const dateInitialReadOnly = isSubmitting || !canEditMembership;
  const pricingDisabled = isSubmitting || !canEditMembership;

  // For PaymentSummary when editing, use asignacion data directly (most reliable)
  // parseApiDateToInput handles both DD/MM/YYYY and YYYY-MM-DD from API
  const paymentSummaryMembresia = isEditing && asignacion?.membresia_details
    ? asignacion.membresia_details
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
        console.log('[MemberForm] SUBMIT FIRED, data:', data);
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

        <div className="w-full flex items-center justify-center">
          <Button type="submit" disabled={isSubmitting}>
            {isSubmitting ? 'Guardando...' : isEditing ? 'Actualizar' : 'Registrar'}
          </Button>
        </div>
      </form>
    </main>
  );
};
export default MemberForm;