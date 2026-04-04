import type { ChangeEvent } from 'react'

export function ParamField({
  name,
  value,
  onChange,
  required,
  disabled,
}: {
  name: string
  value: string
  onChange: (v: string) => void
  required?: boolean
  disabled?: boolean
}) {
  function handleChange(e: ChangeEvent<HTMLInputElement>) {
    onChange(e.target.value)
  }

  return (
    <div className="run-field">
      <label className="run-field-label mono">
        {name}
        {required && <span className="run-required">*</span>}
      </label>
      <input
        className="run-field-input mono"
        value={value}
        onChange={handleChange}
        placeholder={required ? 'required' : 'optional'}
        disabled={disabled}
      />
    </div>
  )
}
