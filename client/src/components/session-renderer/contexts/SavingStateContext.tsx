import React, { createContext, useContext, useState, ReactNode } from 'react';

interface SavingStateContextType {
  isSaving: boolean;
  lastSavedAt: Date | null;
  setSaving: (saving: boolean) => void;
  setLastSaved: () => void;
}

const SavingStateContext = createContext<SavingStateContextType | undefined>(undefined);

interface SavingStateProviderProps {
  children: ReactNode;
}

export function SavingStateProvider({ children }: SavingStateProviderProps) {
  const [isSaving, setIsSaving] = useState(false);
  const [lastSavedAt, setLastSavedAt] = useState<Date | null>(null);

  const setSaving = (saving: boolean) => {
    setIsSaving(saving);
  };

  const setLastSaved = () => {
    setLastSavedAt(new Date());
    setIsSaving(false);
  };

  return (
    <SavingStateContext.Provider
      value={{
        isSaving,
        lastSavedAt,
        setSaving,
        setLastSaved,
      }}
    >
      {children}
    </SavingStateContext.Provider>
  );
}

export function useSavingState() {
  const context = useContext(SavingStateContext);
  if (context === undefined) {
    throw new Error('useSavingState must be used within a SavingStateProvider');
  }
  return context;
}