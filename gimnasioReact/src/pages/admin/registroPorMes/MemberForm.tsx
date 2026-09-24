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

export const MemberForm = () => {
  const {
    // Form
    register,
    handleSubmit,
    errors,
    isSubmitting,
    // Mode
    modo,
    setModo,
    // Data
    miembros,
    membresias,
    selectedMembresia,
    // Pricing
    multiplier,
    discountPercent,
    multiplierOptions,
    showMultiplier,
    estimatedPrice,
    totalDays,
    estimatedDateFinal,
    // Handlers
    handleMemberShipsChange,
    handleMultiplierChange,
    setDiscountPercent,
    // Submission
    onSubmit,
    isEditing,
  } = useMemberForm();

  return (
    <main className="max-w-7xl mx-auto p-6 lg:p-10">
      <BreadCrumbsSection
        isEditing={isEditing}
        title="Asignar Membresías"
        description="Asocie membresías a los atletas registrados en el sistema"
        entityName="esta asignación"
      />
      <form onSubmit={handleSubmit(onSubmit)} className="space-y-8">
        <ModeToggle modo={modo} onChange={setModo} disabled={isSubmitting} />

        {modo === 'existente' ? (
          <ExistingMemberSelect
            register={register}
            errors={errors}
            miembros={miembros}
            disabled={isSubmitting}
          />
        ) : (
          <NewMemberFields register={register} errors={errors} disabled={isSubmitting} />
        )}

        <section className="gap-y-10 gap-x-8 grid grid-cols-1 md:grid-cols-2">
          <MembershipSelect
            register={register}
            errors={errors}
            membresias={membresias}
            onChange={handleMemberShipsChange}
            disabled={isSubmitting}
          />
          <DateInitialField register={register} errors={errors} disabled={isSubmitting} />
        </section>

        {showMultiplier && (
          <MultiplierDiscountFields
            multiplier={multiplier}
            discountPercent={discountPercent}
            multiplierOptions={multiplierOptions}
            onMultiplierChange={handleMultiplierChange}
            onDiscountChange={setDiscountPercent}
            disabled={isSubmitting}
          />
        )}

        <PaymentSummary
          selectedMembresia={selectedMembresia}
          multiplier={multiplier}
          discountPercent={discountPercent}
          estimatedPrice={estimatedPrice}
          totalDays={totalDays}
          estimatedDateFinal={estimatedDateFinal}
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