import React, { forwardRef } from 'react';
import styles from './ComponentName.module.css';

export interface ComponentNameProps {
  /** Unique identifier for testing and accessibility */
  id?: string;
  /** Additional CSS classes */
  className?: string;
  /** Children content */
  children?: React.ReactNode;
}

/**
 * ComponentName - [Brief description of purpose]
 * Atomic design layer: atom | molecule | organism
 */
export const ComponentName = forwardRef<HTMLDivElement, ComponentNameProps>(
  ({ id, className = '', children, ...props }, ref) => {
    return (
      <div
        ref={ref}
        id={id}
        className={`${styles.container} ${className}`}
        {...props}
      >
        {children}
      </div>
    );
  }
);

ComponentName.displayName = 'ComponentName';

export default ComponentName;