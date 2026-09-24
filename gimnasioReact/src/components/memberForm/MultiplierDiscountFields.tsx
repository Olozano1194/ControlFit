import type { MultiplierDiscountFieldsProps } from '../../types/MemberFormTypes';
import Select from '../ui/Select';
import Input from '../ui/Input';
import Label from '../ui/Label';

export function MultiplierDiscountFields({
  multiplier,
  discountPercent,
  multiplierOptions,
  onMultiplierChange,
  onDiscountChange,
  disabled = false,
}: MultiplierDiscountFieldsProps) {
  const handleMultiplierChange = (event: React.ChangeEvent<HTMLSelectElement>) => {
    if (!disabled) {
      onMultiplierChange(event);
    }
  };

  const handleDiscountChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    if (!disabled) {
      onDiscountChange(Number(event.target.value) || 0);
    }
  };

  return (
    <section className="gap-y-10 gap-x-8 grid grid-cols-1 md:grid-cols-2">
      <div className="relative pt-5">
        <Select
          id="multiplier"
          value={String(multiplier)}
          onChange={handleMultiplierChange}
          disabled={disabled}
          aria-label="Periodos"
        >
          {multiplierOptions.map((val) => (
            <option key={val} value={String(val)}>
              {val} {val === 1 ? 'mes' : 'meses'}
            </option>
          ))}
        </Select>
        <Label htmlFor="multiplier">Periodos</Label>
      </div>
      <div className="relative pt-5">
        <Input
          id="discountPercent"
          type="number"
          value={String(discountPercent)}
          onChange={handleDiscountChange}
          min={0}
          max={100}
          step={0.5}
          disabled={disabled}
          aria-label="Descuento (%)"
        />
        <Label htmlFor="discountPercent">Descuento (%)</Label>
      </div>
    </section>
  );
}