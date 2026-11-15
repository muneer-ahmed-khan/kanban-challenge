import { useEffect, useRef, useState } from 'react';
import * as Select from '@radix-ui/react-select';
import { Check, ChevronDown } from 'lucide-react';

export default function AppSelect({ label, value, onValueChange, options, icon: Icon, className = '' }) {
  const triggerRef = useRef(null);
  const [portalContainer, setPortalContainer] = useState(undefined);

  useEffect(() => {
    setPortalContainer(triggerRef.current?.closest('dialog') || document.body);
  }, []);

  return <div className={`app-select ${className}`}>
    <Select.Root value={String(value)} onValueChange={onValueChange}>
      <Select.Trigger ref={triggerRef} className="app-select-trigger" aria-label={label}>
        {Icon && <Icon size={16} strokeWidth={1.9} aria-hidden="true" />}
        <Select.Value className="app-select-value" />
        <Select.Icon className="app-select-chevron"><ChevronDown size={16} strokeWidth={2} aria-hidden="true" /></Select.Icon>
      </Select.Trigger>
      <Select.Portal container={portalContainer}>
        <Select.Content className="app-select-content" position="popper" sideOffset={6} collisionPadding={12}>
          <Select.Viewport className="app-select-viewport">
            {options.map((option) => <Select.Item className="app-select-option" key={option.value} value={String(option.value)} textValue={option.label}>
              {option.color && <span className={`app-select-swatch ${option.color}`} aria-hidden="true" />}
              <Select.ItemText>{option.label}</Select.ItemText>
              <Select.ItemIndicator className="app-select-check"><Check size={15} strokeWidth={2.2} aria-hidden="true" /></Select.ItemIndicator>
            </Select.Item>)}
          </Select.Viewport>
        </Select.Content>
      </Select.Portal>
    </Select.Root>
  </div>;
}
